import psycopg2
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.utils import timezone
from pathlib import Path

from projects.models import Project, ProjectFile
from servers.models import EnvironmentType, EnvironmentResource, Server, Workspace, Model, Job, DataSource, \
    ServerRunStatistics, ServerStatistics, SshTunnel
from users.models import UserProfile
from utils import decode_id


class Command(BaseCommand):
    help = 'Migrates data from old database'

    def add_arguments(self, parser):
        parser.add_argument('old_db', type=str, help='Old database url')

    def handle(self, *args, **options):
        self.conn = psycopg2.connect(options['old_db'])
        self.root_dir = Path(settings.RESOURCE_DIR)
        self.handle_users()
        self.handle_projects()
        self.handle_environment_types()
        self.handle_environment_resources()
        self.handle_servers()
        self.handle_server_data_sources()
        self.handle_server_run_statistics()
        self.handle_ssh_tunnels()
        self.handle_project_files()
        self.conn.close()

    def handle_users(self):
        User = get_user_model()
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
            "user".username,
            "user".first_name,
            "user".last_name,
            "user".email,
            "user".created_at,
            "user".active,
            CASE WHEN roles_users.role_id = 1 THEN TRUE ELSE FALSE END AS is_admin,
            "user".avatar_url,
            "user".bio,
            "user".url,
            "user".email_confirmed,
            "user".confirmed_at,
            "user".location,
            "user".company,
            "user".current_login_ip,
            "user".login_count,
            "user"."Timezone"
          FROM "user" LEFT JOIN roles_users ON "user".id = roles_users.user_id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating user: ", row['username'])
            user, created = User.objects.get_or_create(
                username=row['username'],
                defaults=dict(
                    first_name=row['first_name'] or '',
                    last_name=row['last_name'] or '',
                    email=row['email'],
                    date_joined=row['created_at'],
                    is_active=row['active'],
                    is_superuser=row['is_admin'],
                    is_staff=row['is_admin'],
                )
            )
            if created:
                UserProfile.objects.create(
                    user=user,
                    avatar_url=row['avatar_url'] or '',
                    bio=row['bio'] or '',
                    url=row['url'] or '',
                    email_confirmed=row['email_confirmed'],
                    confirmed_at=row['confirmed_at'],
                    location=row['location'] or '',
                    company=row['company'] or '',
                    current_login_ip=row['current_login_ip'] or '',
                    timezone=row['Timezone'] or '',
                )

    def handle_projects(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
            project.name,
            project.description,
            project.private,
            project.last_updated
          FROM project;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating project: ", row['name'])
            project, _ = Project.objects.get_or_create(
                name=row['name'],
                defaults=dict(
                    description=row['description'] or '',
                    private=row['private'],
                    last_updated=row['last_updated'] or timezone.now()
                )
            )

    def handle_environment_types(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
            environment_type.name,
            environment_type.image_name,
            environment_type.created_at,
            environment_type.cmd,
            environment_type.description,
            environment_type.work_dir,
            environment_type.env_vars,
            environment_type.container_path,
            environment_type.container_port,
            environment_type.active,
            environment_type.urldoc,
            environment_type.type,
            environment_type.usage
        FROM environment_type;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating env type: ", row['name'])
            EnvironmentType.objects.get_or_create(
                name=row['name'],
                defaults=dict(
                    image_name=row['image_name'],
                    created_at=row['created_at'],
                    cmd=row['cmd'] or '',
                    description=row['description'] or '',
                    work_dir=row['work_dir'] or '',
                    env_vars=row['env_vars'],
                    container_path=row['container_path'] or '',
                    container_port=row['container_port'],
                    active=row['active'],
                    urldoc=row['urldoc'] or '',
                    type=row['type'] or '',
                    usage=row['usage']
                )
            )

    def handle_environment_resources(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
            environment_resources.name,
            environment_resources.cpu,
            environment_resources.memory,
            environment_resources.description,
            environment_resources.created_at,
            environment_resources.active,
            environment_resources.storage_size
        FROM environment_resources;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating env resources: ", row['name'])
            EnvironmentResource.objects.get_or_create(
                name=row['name'],
                defaults=dict(
                    cpu=row['cpu'],
                    memory=row['memory'],
                    description=row['description'] or '',
                    created_at=row['created_at'] or timezone.now(),
                    active=row['active'],
                    storage_size=row['storage_size']
                )
            )

    def handle_servers(self):
        User = get_user_model()
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
          servers.name,
          servers.private_ip,
          servers.public_ip,
          servers.port,
          servers.created_at,
          servers.container_id,
          servers.env_vars,
          servers.startup_script,
          servers.type,
          models.method AS model_method,
          models.script AS model_script,
          jobs.method AS job_method,
          jobs.script AS job_script,
          "user".username,
          environment_resources.name AS env_res_name,
          environment_type.name AS env_type_name,
          project.name AS project_name
        FROM servers
        LEFT JOIN models ON servers.id = models.server_id
        LEFT JOIN jobs ON servers.id = jobs.server_id
        JOIN "user" ON servers.created_by_id = "user".id
        JOIN environment_type ON servers.environment_type_id = environment_type.id
        JOIN environment_resources ON servers.environment_resources_id = environment_resources.id
        JOIN project_server ON servers.id = project_server.server_id
        JOIN project ON project_server.project_id = project.id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating server: ", row['name'])
            user = User.objects.get(username=row['username'])
            env_res = EnvironmentResource.objects.get(name=row['env_res_name'])
            env_type = EnvironmentType.objects.get(name=row['env_type_name'])
            project = Project.objects.get(name=row['project_name'])
            server, created = Server.objects.get_or_create(
                name=row['name'],
                defaults=dict(
                    private_ip=row['private_ip'],
                    public_ip=row['public_ip'],
                    port=row['port'],
                    created_at=row['created_at'] or timezone.now(),
                    container_id=row['container_id'] or '',
                    env_vars=row['env_vars'],
                    startup_script=row['startup_script'] or '',
                    created_by=user,
                    environment_type=env_type,
                    environment_resources=env_res,
                    project=project
                )
            )
            if row['type'] == 'w':
                Workspace.objects.get_or_create(server=server)
            elif row['type'] == 'm':
                Model.objects.get_or_create(
                    server=server,
                    defaults=dict(
                        method=row['model_method'] or '',
                        script=row['model_script']
                    )
                )
            elif row['type'] == 'j':
                Job.objects.get_or_create(
                    server=server,
                    defaults=dict(
                        method=row['job_method'] or '',
                        script=row['job_script']
                    )
                )
            else:
                DataSource.objects.get_or_create(server=server)

    def handle_server_data_sources(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
            servers.name AS server_name,
            data_source.name AS data_source_name
        FROM servers
        JOIN server_data_sources ON servers.id = server_data_sources.server_id
        JOIN servers data_source ON server_data_sources.data_source_id = data_source.id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Connecting server to data source: ", row['server_name'])
            data_source = DataSource.objects.get(server__name=row['data_source_name'])
            server = Server.objects.get(name=row['server_name'])
            server.data_sources.add(data_source)
            server.save()

    def handle_server_run_statistics(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
          servers.name AS server_name,
          server_run_statistics.start,
          server_run_statistics.stop,
          server_run_statistics.exit_code,
          server_run_statistics.size,
          server_run_statistics.stacktrace
        FROM server_run_statistics
        JOIN servers ON server_run_statistics.server_id = servers.id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating server run stats: ", row['server_name'])
            server = Server.objects.get(name=row['server_name'])
            ServerRunStatistics.objects.create(
                server=server,
                start=row['start'],
                stop=row['stop'],
                exit_code=row['exit_code'],
                size=row['size'],
                stacktrace=row['stacktrace'] or ''
            )

    def handle_server_statistics(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
          servers.name AS server_name,
          server_statistics.start,
          server_statistics.stop,
          server_statistics.size
        FROM server_statistics
        JOIN servers ON server_statistics.server_id = servers.id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating server stats: ", row['server_name'])
            server = Server.objects.get(name=row['server_name'])
            ServerStatistics.objects.create(
                server=server,
                start=row['start'],
                stop=row['stop'],
                size=row['size']
            )

    def handle_ssh_tunnels(self):
        cur = self.conn.cursor()
        cur.execute("""
        SELECT
          servers.name AS server_name,
          ssh_tunnel.name,
          ssh_tunnel.host,
          ssh_tunnel.local_port,
          ssh_tunnel.endpoint,
          ssh_tunnel.remote_port,
          ssh_tunnel.username
        FROM ssh_tunnel
        JOIN servers ON ssh_tunnel.server_id = servers.id;
        """)
        columns = [column[0] for column in cur.description]
        for row in cur:
            row = dict(zip(columns, row))
            print("Creating ssh tunnels: ", row['name'])
            server = Server.objects.get(name=row['server_name'])
            SshTunnel.objects.get_or_create(
                name=row['name'],
                server=server,
                defaults=dict(
                    host=row['host'],
                    local_port=row['local_port'],
                    endpoint=row['endpoint'],
                    remote_port=row['remote_port'],
                    username=row['username'],
                )
            )

    def handle_project_files(self):
        cur = self.conn.cursor()
        User = get_user_model()
        for user_dir in self.root_dir.iterdir():
            if not user_dir.is_dir():
                continue
            user = User.objects.filter(username=user_dir.name).first()
            if user is not None:
                for project_dir in user_dir.iterdir():
                    if not project_dir.is_dir() or str(project_dir).startswith('.'):
                        continue
                    cur.execute("SELECT project.name FROM project WHERE project.id = %s;",
                                (decode_id(project_dir.name),))
                    old_project = cur.fetchone()
                    if old_project:
                        project_name = old_project[0]
                        project = Project.objects.filter(name=project_name).first()
                        if project is not None:
                            new_project_dir = Path(self.root_dir, user.username, str(project.pk))
                            project_dir.rename(new_project_dir)
                            files = self.walk_dir(ProjectFile, new_project_dir, user, project)
                            ProjectFile.objects.bulk_create(files)

    def walk_dir(self, model, directory, user, project):
        files = []
        for path in directory.iterdir():
            if path.is_dir():
                files.extend(self.walk_dir(model, path, user, project))
            else:
                files.append(model(
                    path=str(path.relative_to(self.root_dir.joinpath(user.username, str(project.id)))),
                    encoding='utf-8',
                    author=user,
                    project=project,
                ))
        return files
