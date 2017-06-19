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
from django.conf.urls.static import static
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound, APIException
from rest_framework_nested import routers
from oauth2_provider import views as oauth2_views

from base.swagger.views import get_swagger_view
from projects import views as project_views
from servers import views as servers_views
from users import views as user_views
from infrastructure import views as infra_views
from jwt_auth import views as jwt_views
from triggers import views as trigger_views
from billing import views as billing_views
from search.views import SearchViewSet

router = routers.DefaultRouter()

router.register(r'servers/options/resources', servers_views.EnvironmentResourceViewSet)
router.register(r'users', user_views.UserViewSet)
router.register(r'hosts', infra_views.DockerHostViewSet)
router.register(r'triggers', trigger_views.TriggerViewSet)
router.register(r'billing/customers', billing_views.CustomerViewSet)
router.register(r'billing/cards', billing_views.CardViewSet)
router.register(r'billing/plans', billing_views.PlanViewSet)
router.register(r'billing/subscriptions', billing_views.SubscriptionViewSet)
router.register(r'billing/invoices', billing_views.InvoiceViewSet)
user_router = routers.NestedSimpleRouter(router, r'users', lookup='user')
user_router.register(r'emails', user_views.EmailViewSet)
user_router.register(r'integrations', user_views.IntegrationViewSet)

router.register(r'projects', project_views.ProjectViewSet)
project_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
project_router.register(r'servers', servers_views.ServerViewSet)
project_router.register(r'files', project_views.FileViewSet)
project_router.register(r'project_files', project_views.ProjectFileViewSet)
project_router.register(r'servers/(?P<server_pk>[^/.]+)/ssh-tunnels',
                        servers_views.SshTunnelViewSet)
project_router.register(r'servers/(?P<server_pk>[^/.]+)/run-stats',
                        servers_views.ServerRunStatisticsViewSet)
project_router.register(r'servers/(?P<server_pk>[^/.]+)/stats',
                        servers_views.ServerStatisticsViewSet)
project_router.register(r'collaborators', project_views.CollaboratorViewSet)
router.register(r'service/(?P<server_pk>[^/.]+)/trigger', trigger_views.ServerActionViewSet)

schema_view = get_swagger_view(title='3blades API', url=settings.FORCE_SCRIPT_NAME or '/')

urlpatterns = [
    url(r'^auth/jwt-token-auth/$', jwt_views.ObtainJSONWebToken.as_view(), name='obtain-jwt'),
    url(r'^auth/jwt-token-refresh/$', jwt_views.RefreshJSONWebToken.as_view(), name='refresh-jwt'),
    url(r'^auth/jwt-token-verify/$', jwt_views.VerifyJSONWebToken.as_view(), name='verify-jwt'),
    url(r'^auth/register/$', user_views.RegisterView.as_view(), name='register'),
    url(r'^auth/authorize/?$', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    url(r'^auth/token/?$', oauth2_views.TokenView.as_view(), name="token"),
    url(r'^auth/', include('social_django.urls', namespace="social")),
    url(r'^swagger/$', schema_view),
    url(r'^(?P<namespace>[\w-]+)/search/$', SearchViewSet.as_view({'get': 'list'}), name='search'),
    url(r'^tbs-admin/', admin.site.urls),
    url(r'^actions/', include('actions.urls')),
    url(r'^servers/(?P<server_pk>[^/.]+)$', servers_views.server_internal_details, name="server_internal"),
    url(r'^(?P<namespace>[\w-]+)/triggers/send-slack-message/$', trigger_views.SlackMessageView.as_view(),
        name='send-slack-message'),
    url(r'^(?P<namespace>[\w-]+)/', include(router.urls)),
    url(r'^(?P<namespace>[\w-]+)/', include(project_router.urls)),
    url(r'^(?P<namespace>[\w-]+)/projects/(?P<project_pk>[\w-]+)/synced-resources/$',
        project_views.SyncedResourceViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^(?P<namespace>[\w-]+)/', include(user_router.urls)),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>[\w-]+)/ssh-key/$', user_views.ssh_key, name='ssh_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>[\w-]+)/ssh-key/reset/$', user_views.reset_ssh_key,
        name='reset_ssh_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>[\w-]+)/api-key/$', user_views.api_key, name='api_key'),
    url(r'^(?P<namespace>[\w-]+)/users/(?P<user_pk>[\w-]+)/api-key/reset/$', user_views.reset_api_key,
        name='reset_api_key'),
    url(r'^(?P<namespace>[\w-]+)/projects/(?P<project_pk>[\w-]+)/servers/(?P<pk>[^/.]+)/is-allowed/$',
        servers_views.IsAllowed.as_view(), name='is_allowed'),
    url(r'^(?P<namespace>[\w-]+)/service/(?P<server_pk>[^/.]+)/trigger/(?P<pk>[^/.]+)/call/$',
        trigger_views.call_trigger, name='server-trigger-call'),
    url(r'^(?P<namespace>[\w-]+)/projects/(?P<project_pk>[\w-]+)/servers/(?P<pk>[^/.]+)/start/$',
        servers_views.start, name='server-start'),
    url(r'^(?P<namespace>[\w-]+)/projects/(?P<project_pk>[\w-]+)/servers/(?P<pk>[^/.]+)/stop/$',
        servers_views.stop, name='server-stop'),
    url(r'^(?P<namespace>[\w-]+)/projects/(?P<project_pk>[\w-]+)/servers/(?P<pk>[^/.]+)/terminate/$',
        servers_views.terminate, name='server-terminate'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'(?P<namespace>[\w-]+)/billing/subscription_required/$', billing_views.no_subscription,
        name="subscription-required"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


@api_view()
def handler404(request):
    raise NotFound()


@api_view()
def handler500(request):
    raise APIException(detail="Internal Server Error", code=500)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^auth/simple-token-auth/$', user_views.ObtainAuthToken.as_view()),
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns = staticfiles_urlpatterns() + urlpatterns
