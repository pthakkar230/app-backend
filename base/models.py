from django.utils.functional import cached_property

from utils import encode_id


class HashIDMixin(object):
    @cached_property
    def hashid(self):
        return encode_id(self.id)
