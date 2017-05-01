from django.conf.urls import url

from .views import ActionList, cancel, ActionViewSet

urlpatterns = [
    url(r'^$', ActionList.as_view(), name='action-list'),
    url(r'^$', ActionViewSet.as_view({'post': 'create'}), name='action-create'),
    url(r'^(?P<pk>[\w-]+)/cancel/$', cancel, name='action-cancel'),
    url(r'^(?P<pk>[\w-]+)/$', ActionViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}),
        name='action-detail'),
]
