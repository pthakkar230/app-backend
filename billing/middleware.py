from django.shortcuts import redirect
from django.urls import resolve
from django.conf import settings
from billing.models import Customer


class SubscriptionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            url_name = resolve(request.path).url_name
            if url_name not in settings.SUBSCRIPTION_EXEMPT_URLS:
                user = request.action.user
                if (settings.ENABLE_BILLING
                    and user
                    and not user.is_staff):
                    customer = user.customer
                    if not customer.has_active_subscription():
                        return redirect("subscription-required",
                                        namespace=user.username)
        except Customer.DoesNotExist:
            pass

        return self.get_response(request)
