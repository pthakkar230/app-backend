from base.namespace import Namespace
from utils import decode_id


class NamespaceMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        name = view_kwargs.pop('namespace', None)
        request.namespace = Namespace.from_name(name)
        return


class HashIDMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        for kwarg in view_kwargs:
            pk_in_kwargs = any([
                kwarg == 'pk',
                kwarg == 'id',
                kwarg.endswith('_pk'),
                kwarg.endswith('_id')
            ])
            if pk_in_kwargs:
                view_kwargs[kwarg] = decode_id(view_kwargs[kwarg])
        return
