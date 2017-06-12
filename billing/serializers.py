import logging
import stripe
from django.conf import settings
from rest_framework import serializers

from billing.models import (Customer, Card,
                            Plan, Subscription,
                            Invoice)
from billing.stripe_utils import (convert_stripe_object,
                                  create_stripe_customer_from_user,
                                  create_plan_in_stripe,
                                  create_subscription_in_stripe,
                                  create_card_in_stripe)
log = logging.getLogger('billing')
stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"
        read_only_fields = ('stripe_id', 'created')

    def create(self, validated_data):
        return create_plan_in_stripe(validated_data)

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


class CardSerializer(serializers.Serializer):
    # TODO: Create some sort of validator that validates that if token is not present, the rest of these are
    # Note: Tokens are heavily preferred, but CLI Tools require manually passing all arguments.
    # Hence this mess.
    name = serializers.CharField(max_length=200, required=False)
    address_line1 = serializers.CharField(max_length=255, required=False)
    address_line2 = serializers.CharField(max_length=255, required=False)
    address_city = serializers.CharField(max_length=255, required=False)
    address_state = serializers.CharField(max_length=100, required=False)
    address_zip = serializers.CharField(max_length=15, required=False)
    address_country = serializers.CharField(max_length=255, required=False)
    exp_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    exp_year = serializers.IntegerField(required=False)

    token = serializers.CharField(max_length=255, required=False)

    # Begin read-only fields
    id = serializers.UUIDField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    address_line1_check = serializers.CharField(read_only=True)
    address_zip_check = serializers.CharField(read_only=True)
    brand = serializers.CharField(read_only=True)
    cvc_check = serializers.CharField(read_only=True)
    last4 = serializers.CharField(read_only=True)
    fingerprint = serializers.CharField(read_only=True)
    funding = serializers.CharField(read_only=True)
    stripe_id = serializers.CharField(read_only=True)
    created = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return create_card_in_stripe(validated_data,
                                     user=self.context['request'].user)

    def update(self, instance, validated_data):
        customer = instance.customer
        stripe_customer = stripe.Customer.retrieve(customer.stripe_id)
        stripe_card = stripe_customer.sources.retrieve(instance.stripe_id)

        for key in validated_data:
            setattr(stripe_card, key, validated_data[key])

        stripe_resp = stripe_card.save()
        converted_data = convert_stripe_object(Card, stripe_resp)

        for key in converted_data:
            setattr(instance, key, converted_data[key])

        instance.save()
        return instance


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ('stripe_id', 'created', 'livemode')

    def create(self, validated_data):
        auth_user = validated_data.get('user')
        customer = create_stripe_customer_from_user(auth_user)
        return customer

    def update(self, instance, validated_data):
        stripe_obj = stripe.Customer.retrieve(instance.stripe_id)

        card = None
        for key in validated_data:
            if key.lower() == "default_source":
                card = validated_data[key]
                setattr(stripe_obj, key, card.stripe_id)

            elif key.lower() != "user":
                setattr(stripe_obj, key, validated_data[key])

        stripe_response = stripe_obj.save()
        if card is not None:
            stripe_response['default_source'] = card
        converted_data = convert_stripe_object(Customer, stripe_response)

        for key in converted_data:
            setattr(instance, key, converted_data[key])

        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("id", "plan", 'stripe_id', 'created', 'livemode', 'application_fee_percent',
                  'cancel_at_period_end', 'canceled_at', 'current_period_start',
                  'current_period_end', 'start', 'ended_at', 'quantity', 'status',
                  'trial_start', 'trial_end')
        read_only_fields = ('stripe_id', 'created', 'livemode', 'application_fee_percent',
                            'cancel_at_period_end', 'canceled_at', 'current_period_start',
                            'current_period_end', 'start', 'ended_at', 'quantity', 'status',
                            'trial_start', 'trial_end')

    def create(self, validated_data):
        return create_subscription_in_stripe(validated_data,
                                             user=self.context['request'].user)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"
