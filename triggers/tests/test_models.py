from django.urls import reverse
from rest_framework.test import APILiveServerTestCase

from actions.models import Action
from actions.tests.factories import ActionFactory
from projects.models import Project
from projects.tests.factories import CollaboratorFactory
from servers.tests.factories import ServerFactory
from triggers.models import Trigger
from triggers.tests.factories import TriggerFactory


class TriggerTest(APILiveServerTestCase):
    def setUp(self):
        collaborator = CollaboratorFactory()
        self.user = collaborator.user
        self.project = collaborator.project
        self.token_header = 'Token {}'.format(self.user.auth_token.key)
        self.client = self.client_class(HTTP_AUTHORIZATION=self.token_header)

    def test_launch_action(self):
        effect = ActionFactory(
            method='post',
            state=Action.CREATED,
            path=reverse('project-list', kwargs={'namespace': self.user.username}),
            payload={'name': 'Project111'},
            user=self.user
        )
        TriggerFactory(cause=None, effect=effect, user=self.user)
        effect.dispatch(url=self.live_server_url)
        self.assertEqual(Project.objects.count(), 2)

    def test_launch_object_action(self):
        server = ServerFactory(project=self.project)
        effect = ActionFactory(
            method='get',
            state=Action.CREATED,
            path=reverse(
                'is_allowed',
                kwargs={
                    'namespace': self.user.username,
                    'project_pk': str(self.project.pk),
                    'pk': str(server.pk)
                }
            ),
            user=self.user
        )
        TriggerFactory(cause=None, effect=effect, user=self.user)
        resp = effect.dispatch(url=self.live_server_url)
        self.assertEqual(resp.status_code, 200)

    def test_dispatch_signal(self):
        cause = ActionFactory(state=Action.CREATED)
        tf = TriggerFactory(cause=cause, effect=None, webhook={})
        cause.state = Action.SUCCESS
        cause.save()
        self.assertEqual(Action.objects.count(), 2)
        tf.refresh_from_db()
        self.assertNotEqual(cause.pk, tf.cause.pk)
        self.assertEqual(tf.cause.state, Action.CREATED)
        self.assertEqual(cause.path, tf.cause.path)
        self.assertEqual(cause.method, tf.cause.method)

    def test_set_action_state(self):
        t = Trigger()
        action = ActionFactory(state=Action.CREATED)
        t._set_action_state(action, Action.SUCCESS)
        action.refresh_from_db()
        self.assertEqual(action.state, Action.SUCCESS)

    def test_trigger_with_payload(self):
        cause = ActionFactory(state=Action.CREATED)
        effect = ActionFactory(
            state=Action.CREATED,
            method='post',
            path='/{}/projects/'.format(self.user.username),
            payload=dict(name='DispatchTest'),
            user=self.user,
        )
        tr = TriggerFactory(cause=cause, effect=effect, webhook={})
        tr.dispatch(url=self.live_server_url)
        created_project = Project.objects.filter(name=effect.payload['name']).first()
        self.assertIsNotNone(created_project)
