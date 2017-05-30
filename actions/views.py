from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from appdj.celery import app as celery_app
from .serializers import ActionSerializer
from .models import Action


class ActionList(generics.ListAPIView):
    queryset = Action.objects.select_related('content_type')
    serializer_class = ActionSerializer
    filter_fields = ('state', 'start_date', 'end_date')


class ActionViewSet(viewsets.ModelViewSet):
    queryset = Action.objects.select_related('content_type')
    serializer_class = ActionSerializer
    filter_fields = ('state', 'start_date', 'end_date')
    exclude_from_schema = True


@api_view(['POST'])
def cancel(request, pk=None):
    """
    Cancel an action object by ID
    """
    action = get_object_or_404(Action, pk=pk)
    if not action.can_be_cancelled:
        return Response({'message': 'This action can not be cancelled'}, status=status.HTTP_404_NOT_FOUND)
    celery_app.control.revoke(str(action.pk))
    return Response({'message': 'OK'})
