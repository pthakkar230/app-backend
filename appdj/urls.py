"""appdj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework_nested import routers
from rest_framework_swagger.views import get_swagger_view

from projects import views as project_views
from servers import views as servers_views
from users import views as user_views

router = routers.DefaultRouter()

router.register(r'servers/options/resources', servers_views.EnvironmentResourceViewSet)
router.register(r'servers/options/types', servers_views.EnvironmentTypeViewSet)
router.register(r'users', user_views.UserViewSet)
user_router = routers.NestedSimpleRouter(router, r'users', lookup='user')
user_router.register(r'emails', user_views.EmailViewSet)
user_router.register(r'integrations', user_views.IntegrationViewSet)

router.register(r'projects', project_views.ProjectViewSet)
project_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
project_router.register(r'workspaces', servers_views.WorkspaceViewSet)
project_router.register(r'models', servers_views.ModelViewSet)
project_router.register(r'jobs', servers_views.JobViewSet)
project_router.register(r'data-sources', servers_views.DataSourceViewSet)
project_router.register(r'files', project_views.FileViewSet)
project_router.register(r'(?P<server_type>workspaces|models|jobs|data-sources)/(?P<server_pk>[^/.]+)/ssh-tunnels',
                        servers_views.SshTunnelViewSet)
project_router.register(r'(?P<server_type>workspaces|models|jobs|data-sources)/(?P<server_pk>[^/.]+)/run-stats',
                        servers_views.ServerRunStatisticsViewSet)
project_router.register(r'(?P<server_type>workspaces|models|jobs|data-sources)/(?P<server_pk>[^/.]+)/stats',
                        servers_views.ServerStatisticsViewSet)
project_router.register(r'collaborators', project_views.CollaboratorViewSet)

schema_view = get_swagger_view(title='3blades API')

urlpatterns = [
    url(r'^swagger/$', schema_view),
    url(r'^admin/', admin.site.urls),
    url(r'^(?P<namespace>[\w-]+)/', include(router.urls)),
    url(r'^(?P<namespace>[\w-]+)/', include(project_router.urls)),
    url(r'^(?P<namespace>[\w-]+)/', include(user_router.urls)),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>\w+)/ssh-key/$', user_views.ssh_key, name='ssh_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>\w+)/ssh-key/reset/$', user_views.reset_ssh_key,
        name='reset_ssh_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>\w+)/api-key/$', user_views.api_key, name='api_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>\w+)/api-key/reset/$', user_views.reset_api_key,
        name='reset_api_key'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + urlpatterns
