import ujson
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.encoding import force_bytes, force_text
from django_redis.serializers.base import BaseSerializer
from rest_framework_jwt.settings import api_settings
from hashids import Hashids

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def encode_id(value, salt=settings.SECRET_KEY):
    hashids = Hashids(salt=salt, min_length=8)
    return hashids.encode(value)


def decode_id(value_hashed, salt=settings.SECRET_KEY):
    hashids = Hashids(salt=salt, min_length=8)
    value_decode = hashids.decode(value_hashed)
    if value_decode:
        return hashids.decode(value_hashed)[0]
    else:
        return 0


def google_access_token_decoder(resp_str):
    if isinstance(resp_str, bytes):
        resp_str = resp_str.decode('utf-8')
    return ujson.loads(resp_str)


def create_ssh_key(user):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    user_ssh_dir = Path(settings.RESOURCE_DIR, user.username, '.ssh')
    if not user_ssh_dir.exists():
        user_ssh_dir.mkdir(parents=True, exist_ok=True)
    user_ssh_private_key_file = user_ssh_dir.joinpath("id_rsa")
    user_ssh_private_key_file.touch()
    user_ssh_private_key_file.write_bytes(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))
    user_ssh_public_key_file = user_ssh_dir.joinpath("id_rsa.pub")
    user_ssh_public_key_file.touch()
    user_ssh_public_key_file.write_bytes(public_key.public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    ))
    user_ssh_dir.chmod(0o770)
    user_ssh_private_key_file.chmod(0o440)
    user_ssh_public_key_file.chmod(0o600)


class UJSONSerializer(BaseSerializer):
    def dumps(self, value):
        return force_bytes(ujson.dumps(value))

    def loads(self, value):
        return ujson.loads(force_text(value))


def copy_model(model):
    if model is None:
        return
    new_object = model.__class__.objects.get(pk=model.pk)
    new_object.pk = None
    return new_object


alphanumeric = RegexValidator(r'^[0-9a-zA-Z-]*$', "You can use only alphanumeric characters.")


def create_jwt_token(user):
    payload = jwt_payload_handler(user)
    return jwt_encode_handler(payload)
