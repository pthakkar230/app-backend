from drf_haystack.filters import HaystackFilter


class SearchFilter(HaystackFilter):
    def build_filters(self, view, filters):
        if 'type' in filters:
            del filters['type']
        query_builder = self.get_query_builder(backend=self, view=view)
        return query_builder.build_query(**(filters if filters else {}))
