import logging
import stripe
from django.conf import settings
from rest_framework import serializers

from billing.models import (Plan)
from billing.stripe_utils import convert_stripe_object
log = logging.getLogger('billing')


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"
        read_only_fields = ('stripe_id', 'created')

    def create(self, validated_data):
        stripe_response = stripe.Plan.create(id=validated_data.get('name').lower().replace(" ", "-"),
                                             amount=validated_data.get('amount'),
                                             currency=validated_data.get('currency'),
                                             interval=validated_data.get('interval'),
                                             interval_count=validated_data.get('interval_count'),
                                             name=validated_data.get('name'),
                                             statement_descriptor=validated_data.get('statement_descriptor'),
                                             trial_period_days=validated_data.get('trial_period_days'))

        converted_data = convert_stripe_object(Plan, stripe_response)
        return Plan.objects.create(**converted_data)

    def update(self, instance, validated_data):
        stripe_obj = stripe.Plan.retrieve(instance.stripe_id)
        for key in validated_data:
            setattr(stripe_obj, key, validated_data[key])

        stripe_response = stripe_obj.save()
        converted_data = convert_stripe_object(Plan, stripe_response)
        for key in converted_data:
            setattr(instance, key, converted_data[key])

        instance.save()
        return instance


class CustomerSerializer(serializers.ModelSerializer):
    pass
