import factory
from factory import fuzzy
from users.tests.factories import UserFactory
from projects.models import Project, Collaborator, File, ProjectFile


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda o: 'project{}'.format(o))


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


class ProjectFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectFile

    author = factory.SubFactory(UserFactory)
    # TODO: Does this guarantee the project belongs to the user? I don't think so...
    project = factory.SubFactory(ProjectFactory)
    public = fuzzy.FuzzyChoice([True, False])
    # file must be passed in
    file = None
