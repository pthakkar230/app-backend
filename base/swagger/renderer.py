from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework_swagger import renderers

from .codec import OpenAPICodec


class OpenAPIRenderer(renderers.OpenAPIRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context['response'].status_code != status.HTTP_200_OK:
            return JSONRenderer().render(data)
        extra = self.get_customizations()

        return OpenAPICodec().encode(data, extra=extra)
