from drf_haystack.serializers import HaystackSerializer

from projects.search_indexes import ProjectIndex
from projects.serializers import ProjectSerializer
from users.search_indexes import UserIndex
from users.serializers import UserSerializer
from servers.search_indexes import ServerIndex
from servers.serializers import ServerSerializer


class SearchSerializer(HaystackSerializer):
    class Meta:
        field_aliases = {'q': 'text'}
        serializers = {
            UserIndex: UserSerializer,
            ProjectIndex: ProjectSerializer,
            ServerIndex: ServerSerializer,
        }
