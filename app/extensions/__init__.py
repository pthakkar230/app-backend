from app.utils.loading import load


def loader(app, **params):
    extension_output = {}
    for p, e, k in to_load:
        extension_output[p] = load(app, p, params, exclude=e, key=k)
    return extension_output


def add_extensions(package, exclude=None, key=None):
    to_load.append((package, exclude, key))


def remove_extensions(package):
    for i in range(len(to_load)):
        if to_load[i][0] == package:
            del to_load[i]
            return
    raise ValueError("Extension package '%s' has not been loaded" % package)


to_load = [('app.extensions', None, None)]
