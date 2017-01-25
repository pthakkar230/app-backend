from django.db import models
from rest_framework import serializers

from utils import encode_id, decode_id


class HashIDField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        value.pk = encode_id(value.pk)
        return super().to_representation(value)

    def to_internal_value(self, data):
        return super().to_internal_value(decode_id(data))


class HashIDSerializer(serializers.ModelSerializer):
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[models.AutoField] = HashIDField
    serializer_related_field = HashIDField
