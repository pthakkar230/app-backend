import factory
from factory import fuzzy
from users.tests.factories import UserFactory
from projects.models import Project, Collaborator, ProjectFile


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


class ProjectFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectFile

    author = factory.SubFactory(UserFactory)
    # TODO: Does this guarantee the project belongs to the user? I don't think so...
    project = factory.SubFactory(ProjectFactory)
    public = fuzzy.FuzzyChoice([True, False])
    # file must be passed in
    file = None
