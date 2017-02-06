from unittest.mock import patch

from django.test import TestCase

from projects.tests.factories import CollaboratorFactory
from servers.tests.fake_docker_api_client.fake_api import FAKE_CONTAINER_ID
from ..models import Model
from ..spawners import DockerSpawner
from .factories import ModelFactory, EnvironmentTypeFactory, EnvironmentResourcesFactory
from .fake_docker_api_client.fake_api_client import make_fake_client


class TestDockerSpawnerForModel(TestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.server = ModelFactory(
            server__environment_type=EnvironmentTypeFactory(
                image_name='test',
                cmd='{model.pk}|from {model.script:.{script_name_len}} import {model.method}',
                work_dir='/test',
                env_vars={'test': 'test', 'test2': '{server.name}'},
                container_path='/resources',
                container_port=8000
            ),
            server__environment_resources=EnvironmentResourcesFactory(
                memory=512
            ),
            server__project=collaborator.project)
        docker_client = make_fake_client()
        self.spawner = DockerSpawner(self.server, docker_client)

    def test_get_envs(self):
        expected = {
            'test': 'test',
            'TZ': 'UTC',
            'test2': self.server.server.name
        }
        self.assertEqual(self.spawner._get_envs(), expected)

    @patch('servers.spawners.DockerSpawner._get_container')
    def test_launch(self, _get_container):
        _get_container.return_value = None
        self.spawner.launch(**self.server.get_start_kwargs())
        self.assertEqual(self.server.server.container_id, FAKE_CONTAINER_ID)

    @patch('servers.spawners.DockerSpawner._is_swarm')
    def test_get_host_config(self, _is_swarm):
        _is_swarm.return_value = False
        expected = {
            'mem_limit': '512m',
            'port_bindings': {8000: None},
            'binds': [
                '{}:/resources'.format(self.server.volume_path)
            ],
            'restart_policy': None
        }
        self.assertDictEqual(expected, self.spawner._get_host_config())

    def test_status(self):
        self.assertEqual(Model.RUNNING, self.spawner.status())

    def test_create_container(self):
        self.spawner._create_container()
        self.assertTrue(bool(self.server.server.container_id))

    @patch('servers.spawners.DockerSpawner._get_envs')
    @patch('servers.spawners.DockerSpawner._get_host_config')
    def test_create_container_config(self, _get_host_config, _get_envs):
        self.spawner.cmd = 'test'
        _get_host_config.return_value = {}
        _get_envs.return_value = {}
        expected = {
            'image': 'test',
            'command': 'test',
            'environment': {},
            'name': self.server.container_name,
            'host_config': self.spawner.client.create_host_config(**{}),
            'working_dir': '/test',
            'ports': [8000],
            'cpu_shares': 0
        }
        self.assertEqual(self.spawner._create_container_config(), expected)

    def test_get_container_success(self):
        self.spawner._get_container()
        self.assertEqual(self.spawner.container_id, FAKE_CONTAINER_ID)

    def test_terminate(self):
        self.spawner.terminate()

    def test_stop(self):
        self.spawner.stop()
