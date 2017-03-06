from django.conf.urls import url

from .views import ActionList, cancel, ActionDetail

urlpatterns = [
    url(r'^$', ActionList.as_view(), name='action-list'),
    url(r'^(?P<pk>[\w-]+)/cancel/$', cancel, name='action-cancel'),
    url(r'^(?P<pk>[\w-]+)/$', ActionDetail.as_view(), name='action-detail'),
]
