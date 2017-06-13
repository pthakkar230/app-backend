from drf_haystack.viewsets import HaystackViewSet

from .filters import SearchFilter
from .serializers import SearchSerializer


class SearchViewSet(HaystackViewSet):
    serializer_class = SearchSerializer
    filter_backends = (SearchFilter,)

    def filter_queryset(self, *args, **kwargs):
        qs = self.get_queryset()
        if 'type' in self.request.query_params:
            types = []
            query_types = self.request.query_params.getlist('type')
            for typ in query_types:
                if typ in self.types:
                    types.append(self.types[typ])
            if types:
                qs = qs.models(*types)
        return super().filter_queryset(qs)

    @property
    def types(self):
        result = {}
        for index in self.serializer_class.Meta.serializers:
            model = index().get_model()
            result[model.__name__.lower()] = model
        return result
