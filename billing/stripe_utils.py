from datetime import datetime
from django.db.models import DateTimeField
from django.utils import timezone


def convert_field_to_stripe(field, data):
    field_name = field.name
    value = data.get(field_name)

    if field.name == 'id':
        field_name = "stripe_id"
    if isinstance(field, DateTimeField):
        value = datetime.fromtimestamp(data.get(field_name))
        value = timezone.make_aware(value)

    return (field_name, value)


def convert_stripe_object(model, stripe_obj):
    converted = dict([convert_field_to_stripe(field, stripe_obj)
                      for field in model._meta.get_fields()])
    return converted

