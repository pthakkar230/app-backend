import logging
import stripe
from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone

from billing.models import Customer

stripe.api_key = settings.STRIPE_SECRET_KEY
log = logging.getLogger('billing')


def real_convert_field_to_stripe(model, stripe_field, stripe_data):

    field_name = "stripe_id" if stripe_field == "id" else stripe_field
    value = stripe_data.get(stripe_field)

    # Seems inefficient
    all_model_field_names = [f.name for f in model._meta.get_fields()]
    if field_name in all_model_field_names:
        model_field = model._meta.get_field(field_name)
    else:
        model_field = field_name = value = None

    # Not sure how to handle many to many fields just yet.
    # Not sure we will have to.
    # I've really come to hate this following block.
    # Will have to think about how to clean it up.
    if (model_field is not None and
        (model_field.is_relation and not model_field.many_to_many)):

        if value is not None:
            if isinstance(value, dict):
                identifier = value.get("id")
            else:
                identifier = stripe_data.get(stripe_field)

            if hasattr(model_field.related_model, "stripe_id"):
                kwargs = {'stripe_id': identifier}
            else:
                kwargs = {'pk': identifier}
            value = model_field.related_model.objects.get(**kwargs)

    elif isinstance(model_field, models.DateTimeField):
        if value is not None:
            value = datetime.fromtimestamp(value)
            value = timezone.make_aware(value)

    return (field_name, value)


def convert_stripe_object(model, stripe_obj):
    dict_tuples = [real_convert_field_to_stripe(model, field, stripe_obj)
                   for field in stripe_obj]
    converted = dict(tup for tup in dict_tuples if tup[0] is not None)
    if "created" not in converted:
        converted['created'] = datetime.now()
    return converted


def create_stripe_customer_from_user(auth_user):
    stripe_response = stripe.Customer.create(description=auth_user.first_name + " " + auth_user.last_name,
                                             email=auth_user.email)

    # Meh.
    stripe_response['user'] = auth_user.pk

    converted_data = convert_stripe_object(Customer, stripe_response)
    return Customer.objects.create(**converted_data)
