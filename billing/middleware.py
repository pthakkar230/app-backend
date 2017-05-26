from django.shortcuts import redirect
from django.urls import resolve
from billing.models import Customer


class SubscriptionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            url_name = resolve(request.path).url_name
            # TODO: Exempt certain urls via settings
            if url_name != "subscription-required":
                user = request.user
                if user.is_authenticated and not user.is_staff:
                    customer = user.customer
                    if not customer.has_active_subscription():
                        return redirect("subscription-required",
                                        namespace=user.username)
        except Customer.DoesNotExist:
            pass

        return self.get_response(request)
