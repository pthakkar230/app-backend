from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from billing.models import Customer
from billing.stripe_utils import create_stripe_customer_from_user
import logging
log = logging.getLogger('billing')


def check_if_customer_exists_for_user(sender, **kwargs):
    user = kwargs.get("user")
    if settings.ENABLE_BILLING:
        try:
            user.customer
        except Customer.DoesNotExist:
            log.info("No stripe customer exists for user {uname}. "
                     "Creating one.".format(uname=user.username))
            create_stripe_customer_from_user(user)

user_logged_in.connect(check_if_customer_exists_for_user)
