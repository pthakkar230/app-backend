import shutil
import socket
from tempfile import mkdtemp

from flask_testing import TestCase

from hubserver.app import db, create_app, cache
from faker import Faker


class BaseTestCase(TestCase):
    def setUp(self):
        self.app.config['RESOURCE_DIR'] = mkdtemp()
        db.create_all()

    def tearDown(self):
        shutil.rmtree(self.app.config.get('RESOURCE_DIR'), ignore_errors=True)
        db.session.remove()
        db.drop_all()
        cache.flushall()

    def create_app(self):
        app = create_app('config.TestConfig')
        return app


class BackBladeTestCase(BaseTestCase):
    def _login(self, test_client, email, password):
        return test_client.post('/auth/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)


class DockerTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.app.config['SPAWNER_CLASS'] = 'dockerspawner.DockerSpawner'


def get_any_name():
    faker = Faker()
    return faker.name()


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 0))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
