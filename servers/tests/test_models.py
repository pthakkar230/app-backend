from django.test import TestCase
from django_redis import get_redis_connection

from projects.tests.factories import CollaboratorFactory
from servers.models import Workspace, Server, EnvironmentType, Job, Model


class TestWorkspace(TestCase):
    def setUp(self):
        self.cache = get_redis_connection("default")

    def tearDown(self):
        self.cache.flushall()

    def test_str(self):
        instance = Workspace(server=Server(id=1, name='test'))
        self.assertEqual(str(instance), instance.server.name)

    def test_hashid(self):
        expected = 'wedgpzLR'
        instance = Workspace(server_id=1)
        self.assertEqual(expected, instance.hashid)

    def test_container_name(self):
        env_type = EnvironmentType(name='test')
        expected = "server_wedgpzLR_test"
        server = Server(id=1, environment_type=env_type)
        instance = Workspace(server=server)
        self.assertEqual(instance.container_name, expected)

    def test_volume_path(self):
        collaborator = CollaboratorFactory(user__username='test', project__id=1)
        server = Server(project=collaborator.project)
        instance = Workspace(server=server)
        expected = '/tmp/test/wedgpzLR'
        self.assertEqual(instance.volume_path, expected)

    def test_state_cache_key(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        expected = 'server_state_wedgpzLR'
        self.assertEqual(instance.state_cache_key, expected)

    def test_status(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        self.cache.hset('server_state_wedgpzLR', "status", Workspace.RUNNING)
        self.assertEqual(instance.status, Workspace.RUNNING)

    def test_status_setter(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        self.cache.hset('server_state_wedgpzLR', "status", Workspace.STOPPED)
        instance.status = Workspace.RUNNING
        self.assertEqual(self.cache.hget('server_state_wedgpzLR', "status").decode(), Workspace.RUNNING)

    def test_needs_update(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        self.cache.hset('server_state_wedgpzLR', 'update', 'test')
        self.assertTrue(instance.needs_update())

    def test_update_message(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        msg = 'test'
        self.cache.hset('server_state_wedgpzLR', 'update', msg)
        self.assertEqual(instance.update_message, msg)

    def test_update_message_setter(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        msg = 'test'
        instance.update_message = msg
        self.assertEqual(self.cache.hget('server_state_wedgpzLR', "update").decode(), msg)

    def test_update_message_deleter(self):
        server = Server(id=1)
        instance = Workspace(server=server)
        msg = 'test'
        self.cache.hset('server_state_wedgpzLR', 'update', msg)
        del instance.update_message
        self.assertFalse(bool(self.cache.hexists('server_state_wedgpzLR', "update")))


class TestJob(TestCase):
    def test_get_start_kwargs(self):
        instance = Job(
            server=Server(id=1, environment_type=EnvironmentType(
                name='test',
                cmd='{job.hashid}|from {job.script:.{script_name_len}} import {job.method}'
            )),
            script='test.py',
            method='test',
            auto_restart=True
        )
        expected = {
            'command': 'wedgpzLR|from test import test',
            'restart': {"Name": "on-failure", "MaximumRetryCount": 2}
        }
        self.assertEqual(instance.get_start_kwargs(), expected)


class TestModel(TestCase):
    def test_get_start_kwargs(self):
        instance = Model(
            server=Server(id=1, environment_type=EnvironmentType(
                name='test',
                cmd='{model.hashid}|from {model.script:.{script_name_len}} import {model.method}'
            )),
            script='test.py',
            method='test'
        )
        expected = {
            'command': 'wedgpzLR|from test import test',
        }
        self.assertEqual(instance.get_start_kwargs(), expected)
