from haystack import indexes

from .models import Server


class ServerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    project = indexes.CharField(model_attr='project')
    created_by = indexes.CharField(model_attr='created_by')
    image_name = indexes.CharField(model_attr='image_name')

    def get_model(self):
        return Server
