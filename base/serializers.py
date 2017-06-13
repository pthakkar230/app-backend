class SearchSerializerMixin(object):
    def to_representation(self, instance):
        if not isinstance(instance, self.Meta.model):
            instance = instance.object
        return super().to_representation(instance)
