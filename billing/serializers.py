import logging
import stripe
from django.conf import settings
from rest_framework import serializers

from billing.models import (Customer, Card, Plan, Subscription)
from billing.stripe_utils import convert_stripe_object
log = logging.getLogger('billing')
stripe.api_key = settings.STRIPE_SECRET_KEY


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


class CardSerializer(serializers.Serializer):
    # Should probably be a PrimaryKey field but have had trouble w/ config
    user = serializers.UUIDField(write_only=True)
    name = serializers.CharField(max_length=200)
    address_line1 = serializers.CharField(max_length=255)
    address_line2 = serializers.CharField(max_length=255, required=False)
    address_city = serializers.CharField(max_length=255)
    address_state = serializers.CharField(max_length=100)
    address_zip = serializers.CharField(max_length=15)
    address_country = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=100, write_only=True)
    exp_month = serializers.IntegerField(min_value=1, max_value=12)
    exp_year = serializers.IntegerField()
    cvc = serializers.IntegerField(write_only=True)

    # Begin read-only fields
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
        customer = Customer.objects.get(user__id=validated_data.pop("user"))
        stripe_cust = stripe.Customer.retrieve(customer.stripe_id)

        validated_data['object'] = "card"
        stripe_resp = stripe_cust.sources.create(source=validated_data)
        stripe_resp['customer'] = customer

        converted_data = convert_stripe_object(Card, stripe_resp)
        return Card.objects.create(**converted_data)

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
        read_only_fields = ('stripe_id', 'created')

    def create(self, validated_data):
        auth_user = validated_data.get('user')
        stripe_response = stripe.Customer.create(description=auth_user.first_name + " " + auth_user.last_name,
                                                 email=auth_user.email)
        # Meh.
        stripe_response['user'] = auth_user
        converted_data = convert_stripe_object(Customer, stripe_response)
        return Customer.objects.create(**converted_data)

    def update(self, instance, validated_data):
        # TODO: Prevent changing the Customer.user
        stripe_obj = stripe.Customer.retrieve(instance.stripe_id)

        for key in validated_data:
            setattr(stripe_obj, key, validated_data[key])

        stripe_response = stripe_obj.save()
        converted_data = convert_stripe_object(Customer, stripe_response)

        for key in converted_data:
            setattr(instance, key, converted_data[key])

        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("customer", "plan")
        read_only_fields = ('stripe_id', 'created')

    def create(self, validated_data):
        customer = validated_data.get("customer")
        plan = validated_data.get("plan")

        stripe_response = stripe.Subscription.create(customer=customer.stripe_id,
                                                     plan=plan.stripe_id)
        converted_data = convert_stripe_object(Subscription, stripe_response)
        return Subscription.objects.create(**converted_data)
