from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from base.views import NamespaceMixin
from .models import Trigger
from .serializers import TriggerSerializer, SlackMessageSerializer


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
