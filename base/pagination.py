from rest_framework.pagination import LimitOffsetPagination as RestLimitOffsetPagination
from rest_framework.response import Response


class LimitOffsetPagination(RestLimitOffsetPagination):
    def get_paginated_response(self, data):
        return Response(data)
