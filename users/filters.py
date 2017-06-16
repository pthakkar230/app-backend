import django_filters
from django.contrib.auth import get_user_model


User = get_user_model()


class UserSearchFilter(django_filters.FilterSet):
    q = django_filters.CharFilter()

    class Meta:
        model = User
        fields = ('q',)
