from django.shortcuts import redirect
from billing.models import Customer


class SubscriptionMiddleware(object):
    # TODO: Exempt certain urls
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        try:
            if user.is_authenticated and not user.is_staff:
                customer = user.customer
                if not customer.has_active_subscription():
                    return redirect("subscription-required", namespace=user.username)
        except Customer.DoesNotExist:
            pass

        return self.get_response(request)
