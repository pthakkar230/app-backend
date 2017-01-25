from django.contrib.auth import get_user_model


class Namespace(object):
    def __init__(self, name='', typ='', obj=None):
        self.name = name
        self.object = obj
        self.type = typ

    @staticmethod
    def from_name(name):
        ns = Namespace(name=name)
        ns.object = get_user_model().objects.filter(username=name).first()
        if ns.object is not None:
            ns.type = 'user'
        return ns
