from base.namespace import Namespace


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
