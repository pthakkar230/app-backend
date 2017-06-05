import abc
import os

import logging
import tarfile
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.functional import cached_property
from docker import from_env
from docker.errors import APIError

from utils import create_jwt_token


logger = logging.getLogger(__name__)


class ServerSpawner(object):
    """
    Server service interface to allow start/stop/terminate servers
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, server):
        self.server = server

    @abc.abstractmethod
    def start(self, **kwargs) -> None:
        return None

    @abc.abstractmethod
    def stop(self) -> None:
        return None

    @abc.abstractmethod
    def terminate(self) -> None:
        return None

    @abc.abstractmethod
    def status(self) -> str:
        """
        Server statuses should be those defined in server model
        """
        return ''


class DockerSpawner(ServerSpawner):
    def __init__(self, server, client=None):
        super().__init__(server)
        self.client = client or (server.host.client if server.host else from_env())
        self.container_port = self.server.config.get('port') or settings.SERVER_PORT
        self.container_id = ''
        self.cmd = None
        self.entry_point = None
        self.restart = None
        self.network_name = 'project_{}_network'.format(self.server.project.pk)

    def _get_envs(self) -> dict:
        all_env_vars = {}
        # get user defined env vars
        all_env_vars.update(self.server.env_vars or {})
        # get admin defined env vars
        all_env_vars['TZ'] = self._get_user_timezone()
        logger.info("Environment variables to create a container:'{}'".format(all_env_vars))
        return all_env_vars

    def start(self) -> None:
        self.cmd = self._get_cmd()
        if self._is_swarm and not self._is_network_exists():
            self._create_network()
        try:
            # get the container by container_name (if exists)
            if not self._get_container():
                self._create_container()

            try:
                self.client.start(self.server.container_name)
            except APIError as e:
                logger.info(e.response.content)
                raise

            self._set_ip_and_port()

        except Exception:
            self.server.status = self.server.ERROR
            raise  # this is part of celery task, we need to know if it fails

    def _get_cmd(self):
        command = '''/runner -key={token} -ns={server.project.owner.username}
        -projectID={server.project.pk} -serverID={server.pk} -root={domain}'''.format(
            token=create_jwt_token(self.server.project.owner),
            server=self.server,
            domain=Site.objects.get_current()
        )
        if 'script' in self.server.config:
            command += " " + "--script=" + self.server.config["script"]
        if 'function' in self.server.config:
            command += " " + "--function=" + self.server.config["function"]
        if ("type" in self.server.config) and (self.server.config["type"] in settings.SERVER_COMMANDS):
            command += " " + settings.SERVER_COMMANDS[self.server.config["type"]]
        elif "type" in self.server.config:
            command += " --type=" + self.server.config["type"]
        elif "command" in self.server.config:
            command += " " + self.server.config["command"]
        return command

    def _get_host_config(self):
        binds = ['{}:{}'.format(self.server.volume_path, settings.SERVER_RESOURCE_DIR)]
        ssh_path = self._get_ssh_path()
        if ssh_path:
            binds.append('{}:{}/.ssh'.format(ssh_path, settings.SERVER_RESOURCE_DIR))
        if self.server.startup_script:
            binds.append('{}:/start.sh'.format(
                str(Path(self.server.volume_path).joinpath(self.server.startup_script))))
        ports = {port: None for port in self._get_exposed_ports()}
        ports[self.container_port] = None
        config = dict(
            mem_limit='{}m'.format(self.server.environment_resources.memory),
            port_bindings=ports,
            binds=binds,
            restart_policy=self.restart,
        )
        if not self._is_swarm:
            config['links'] = self._connected_links()
        return config

    def _prepare_tar_file(self):
        tar_stream = BytesIO()
        tar = tarfile.TarFile.xzopen(name="server.tar.xz", fileobj=tar_stream, mode="w")
        tar.add(self.server.volume_path, arcname=settings.SERVER_RESOURCE_DIR)
        ssh_path = self._get_ssh_path()
        if ssh_path:
            tar.add(ssh_path, arcname=settings.SERVER_RESOURCE_DIR)
        tar.close()
        tar_stream.seek(0)
        return tar_stream

    def _create_container(self):
        try:
            docker_resp = self.client.create_container(**self._create_container_config())
        except APIError as e:
            logger.info(e.response.content)
            raise
        if not docker_resp:
            raise TypeError('Unexpected empty value when trying to create a container')
        self.container_id = docker_resp['Id']
        self.server.container_id = self.container_id
        self.server.save()
        logger.info("Container created '{}', id:{}".format(self.server.container_name, self.container_id))

    def _create_container_config(self):
        config = dict(
            image=self.server.image_name,
            command=self.cmd,
            environment=self._get_envs(),
            name=self.server.container_name,
            host_config=self.client.create_host_config(**self._get_host_config()),
            ports=[self.container_port],
            cpu_shares=0,
        )
        if self._is_swarm:
            config['networking_config'] = self._create_network_config()
        if self.entry_point:
            config.update(dict(entrypoint=self.entry_point))
        return config

    def _create_network_config(self):
        config = {'aliases': [self.server.name]}
        if self.server.connected.exists():
            config['links'] = self._connected_links()
        return self.client.create_networking_config({
            self.network_name: self.client.create_endpoint_config(
                **config
            )
        })

    def _get_container(self):
        logger.info("Getting container '%s'", self.server.container_name)
        self.container_id = ''
        container = None
        try:
            container = self.client.inspect_container(self.server.container_name)
            self.container_id = container['Id']
            logger.info("Found existing container to the name: '%s'" % self.server.container_name)
        except APIError as e:
            if e.response.status_code == 404:
                logger.info("Container '%s' is gone", self.server.container_name)
            elif e.response.status_code == 500:
                logger.info("Container '%s' is on unhealthy node", self.server.container_name)
            else:
                raise
        if container is not None:
            if not self._compare_container_env(container):
                try:
                    self.client.remove_container(self.server.container_name)
                except APIError as e:
                    if e.response.status_code == 404:
                        pass
                    else:
                        raise
                except:
                    self.server.status = self.server.ERROR
                    raise
                container = None
        return container

    def _set_ip_and_port(self):
        resp = self.client.inspect_container(self.server.container_name)
        if resp is None:
            raise RuntimeError("Failed to get port info for %s" % self.server.container_name)
        network_settings = resp.get("NetworkSettings", {})
        ports = network_settings.get("Ports")
        if ports is None:
            return
        self.server.config['ports'] = {}
        for port, mapping in ports.items():
            port = port.split("/")[0]
            self.server.config['ports'][settings.SERVER_PORT_MAPPING[port]] = mapping[0]["HostPort"]
        self.server.private_ip = mapping[0]["HostIp"]
        self.server.save()

    def terminate(self) -> None:

        try:
            # if the container has a state, then it exists
            self.client.remove_container(self.server.container_name)
        except APIError as e:
            if e.response.status_code == 404:
                logger.info("Container '%s' does not exist. It will be removed from db",
                            self.server.container_name)
        except:
            logger.info("Unexpected error trying to terminate a server")
            raise

    def stop(self) -> None:
        # try to stop the container by docker client
        try:
            self.client.stop(self.server.container_name)
        except APIError as de:
            if de.response.status_code != 404:
                raise
        except:
            logger.info("Unexpected error trying to stop a server")
            raise

    def status(self):
        try:
            result = self.client.inspect_container(self.server.container_name)
        except APIError as e:
            if e.response.status_code == 404:
                return self.server.STOPPED
            return self.server.ERROR
        else:
            return {
                'created': self.server.STOPPED,
                'restarting': self.server.LAUNCHING,
                'running': self.server.RUNNING,
                'paused': self.server.STOPPED,
                'exited': self.server.STOPPED
            }[result['State']['Status']]

    def _get_ssh_path(self):
        ssh_path = os.path.abspath(os.path.join(self.server.volume_path, '..', '.ssh'))
        if os.path.exists(ssh_path):
            return str(ssh_path)
        return ''

    def _compare_container_env(self, container) -> bool:
        old_envs = dict(env.split("=", maxsplit=1) for env in container.get('Config', {}).get('Env', []))
        return all(old_envs.get(key) == val for key, val in (self.server.env_vars or {}).items())

    def _get_user_timezone(self):
        tz = 'UTC'
        owner_profile = self.server.project.owner.profile
        if owner_profile and owner_profile.timezone:
            tz = owner_profile.timezone
        return tz

    def _connected_links(self):
        links = {}
        for source in self.server.connected.all():
            if not source.is_running():
                DockerSpawner(source).launch()
            links[source.container_name] = source.name.lower()
        return links

    def _create_network(self):
        try:
            self.client.create_network(self.network_name, 'overlay')
        except APIError:
            logger.exception("Create network exception")
            raise

    def _is_network_exists(self):
        try:
            return bool(self.client.networks(names=[self.network_name]))
        except APIError:
            logger.exception("Check network exception")
            raise

    @cached_property
    def _is_swarm(self):
        try:
            resp = self.client.info()
        except APIError:
            return False
        return "swarm" in resp.get("Version", "")

    def _get_exposed_ports(self):
        result = [self.container_port]
        try:
            resp = self.client.inspect_image(self.server.image_name)
        except APIError:
            return result
        result.extend([k.split('/')[0] for k in resp["Config"]["ExposedPorts"]])
        return result


class ServerDummySpawner(ServerSpawner):
    def status(self) -> str:
        return 'running'

    def start(self, **kwargs):
        self.server.status = self.server.RUNNING
        return None

    def stop(self):
        self.server.status = self.server.STOPPED
        return None

    def terminate(self):
        self.server.delete()
        return None
