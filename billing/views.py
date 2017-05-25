import logging
import stripe
from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response

from base.views import NamespaceMixin
from billing.models import (Plan, Customer,
                            Card, Subscription,
                            Invoice)
from billing.serializers import (PlanSerializer, CustomerSerializer, CardSerializer,
                                 SubscriptionSerializer, InvoiceSerializer)
log = logging.getLogger('billing')


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def destroy(self, request, *args, **kwargs):
        # Assuming for now that we should only delete the customer record,
        # And leave the auth_user record
        instance = Customer.objects.get(pk=kwargs.get('pk'))
        stripe_obj = stripe.Customer.retrieve(instance.stripe_id)

        stripe_response = stripe_obj.delete()
        instance.delete()

        data = {'stripe_id': stripe_response['id'], 'deleted': True}
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)


class CardViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = Card.objects.all()
    serializer_class = CardSerializer

    def retrieve(self, request, *args, **kwargs):
        card = Card.objects.get(pk=kwargs.get('pk'),
                                customer__user=request.user)
        serializer = self.serializer_class(card)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        cards = Card.objects.filter(customer__user=request.user)
        serializer = self.serializer_class(cards, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        # Assuming for now that we should only delete the customer record,
        # And leave the auth_user record
        instance = Card.objects.get(pk=kwargs.get('pk'))
        stripe_customer = stripe.Customer.retrieve(instance.customer.stripe_id)

        stripe_response = stripe_customer.sources.retrieve(instance.stripe_id).delete()
        instance.delete()

        data = {'stripe_id': stripe_response['id'], 'deleted': True}
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def destroy(self, request, *args, **kwargs):
        instance = Plan.objects.get(pk=kwargs.get('pk'))
        stripe_obj = stripe.Plan.retrieve(instance.stripe_id)

        stripe_response = stripe_obj.delete()
        instance.delete()

        data = {'stripe_id': stripe_response['id'], 'deleted': True}
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)


class SubscriptionViewSet(NamespaceMixin,
                          viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = Subscription.objects.get(pk=kwargs.get('pk'))
        stripe_obj = stripe.Subscription.retrieve(instance.stripe_id)

        stripe_response = stripe_obj.delete()
        instance.canceled_at = timezone.make_aware(datetime.now())
        instance.ended_at = timezone.make_aware(datetime.now())
        instance.status = stripe_response['status']
        instance.save()

        data = {'stripe_id': stripe_response['id'], 'deleted': True}
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
def no_subscription(request, *args, **kwargs):
    return Response(status=status.HTTP_402_PAYMENT_REQUIRED)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
