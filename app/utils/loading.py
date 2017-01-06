import re
import pkgutil
import inspect
import importlib.util

def load(obj, package, params=None, **kwargs):
    """Return a dict of loader names mapped to their outputs.
    
    Parameters
    ----------
    obj : any
        The object to be loaded - this is the first
        argument passed to each identified loader.
    package : :obj:`str`
        The name of the package where loaders reside.
    params : :obj:`dict`
        Keywords passed to all loaders.
    **kwargs
        Passed to :func:`iter_loaders`.
    """
    return {n: l(obj, **(params or {})) for
        n, l in iter_loaders(package, **kwargs)}

def iter_loaders(package, exclude=None, key=None):
    """Iterate over packages and/or modules with a loader at their root

    A module or package has a loader if it has a callable ``'loader'`` attribute.

    Parameters
    ----------
    package : :obj:`str`
        The name of the package where loaders reside.
    exclude : :obj:`list` of :obj:`str`, None
        A list of regex strings that exclude modules if
        their names match any of the given patterns.
    key : callable
        A callable that accepts a module as input and returns
        True or False to filter modules. The modules that
        result in False are not yielded."""
    # use key rather than an if statement to avoid excesive imports
    key = join_keys(lambda m: callable(getattr(m, 'loader', None)), key)
    for module in iter_modules(package, exclude, key=key):
        yield module.__name__, module.loader

def join_keys(*keys):
    """An "or" statement for multiple keys

    As a convenience non-callable keys are ignored
    """
    def key(obj):
        for k in keys:
            if callable(k) and k(obj):
                return True
        else:
            return False
    return key

def iter_modules(name, exclude=None, key=None):
    """Iterate over nested submodules

    Parameters
    ----------
    name : str
        Defines the scope of the search for submodules.
    exclude : :obj:`list` of :obj:`str`, None
        A list of regex strings that exclude modules if
        their names match the given patterns.
    key : callable
        A callable that accepts a module as input and returns
        True or False to filter modules. The modules that
        result in False are not yielded.
    """
    if name.startswith('.'):
        f = inspect_frame(1)
        while f.f_globals['__name__'] == __name__:
            f = f.f_back
        package = f.f_globals['__name__']
    else:
        package = None
    spec = importlib.util.find_spec(name, package)
    if spec is None:
        raise ImportError("Could not find module spec for '%s'" % package)
    exclude = list(exclude or ())
    search_paths = spec.submodule_search_locations
    for finder, name, ispkg in pkgutil.walk_packages(search_paths):
        for e in exclude:
            if re.match(e, name):
                break
        else:
            module = load_module(finder, name)
            if not key or key(module):
                # don't search submodules
                exclude.insert(0, name)
                yield module

def load_module(finder, name):
    """Load a module given its name and finder"""
    return finder.find_module(name).load_module(name)

def frame_globals(i=0):
    return inspect_frame(i).f_globals

def inspect_frame(i=0, last=None):
    if last:
        # use a reference frame
        f = last
    else:
        # use the calling frame
        f = inspect.currentframe().f_back
    # shift back i frames
    while i>0:
        f = f.f_back
        i -= 1
    return f
