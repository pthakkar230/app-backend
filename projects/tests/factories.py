import factory

from users.tests.factories import UserFactory
from ..models import Project, Collaborator, File


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda o: 'project {}'.format(o))


class CollaboratorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collaborator

    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    owner = True


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = File

    path = factory.Sequence(lambda n: 'test_{}.txt'.format(n))
    encoding = 'utf-8'
    author = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    content = factory.Sequence(lambda n: 'test {}'.format(n).encode())

    @classmethod
    def _generate(cls, create, attrs):
        content = attrs.pop('content')
        project_file = super()._generate(create, attrs)
        project_file.save(content=content)
        return project_file
