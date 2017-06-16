from haystack import indexes

from .models import Project


class ProjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    private = indexes.BooleanField(model_attr='private')

    def get_model(self):
        return Project
