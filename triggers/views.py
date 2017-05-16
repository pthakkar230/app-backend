from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base.views import NamespaceMixin
from .models import Trigger
from .serializers import TriggerSerializer, SlackMessageSerializer, ServerActionSerializer


class TriggerViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Trigger.objects.all()
    serializer_class = TriggerSerializer


class SlackMessageView(APIView):
    exclude_from_schema = True

    def post(self, request):
        serializer = SlackMessageSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.send()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ServerActionViewSet(NamespaceMixin, viewsets.ModelViewSet):
    queryset = Trigger.objects.all()
    serializer_class = ServerActionSerializer


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def call_trigger(request, **kwargs):
    trigger = get_object_or_404(Trigger, pk=kwargs['pk'])
    trigger.dispatch()
    return Response({'message': 'OK'})
