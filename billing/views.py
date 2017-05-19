import logging
import stripe
from rest_framework import viewsets, status
from rest_framework.response import Response

from billing.models import Plan
from billing.serializers import PlanSerializer
log = logging.getLogger('billing')


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
