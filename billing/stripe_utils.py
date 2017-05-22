import logging
from datetime import datetime
from django.db import models
from django.utils import timezone
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
    # Not sure we will have to
    if (model_field is not None and
        (model_field.is_relation and not model_field.many_to_many)):

        if value is not None:
            if isinstance(value, dict):
                stripe_id = value.get("id")
            else:
                stripe_id = stripe_data.get(stripe_field)
            value = model_field.related_model.objects.get(stripe_id=stripe_id)

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
