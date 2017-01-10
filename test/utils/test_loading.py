from .. import loading

package_names = (
    'package.module',
    'package.subpackage',
    'package.subpackage.submodule',
    'package.subpackage.subsubpackage',
    'package.subpackage.subsubpackage.subsubmodule',
)

loader_names = (
    'package.module',
    'package.subpackage.submodule',
    'package.subpackage.subsubpackage',
)


def test_iter_modules():
    pass


def test_iter_loaders():
    loaders = dict(iter_loaders(".package"))
    for name in loader_names:
        assert name in loaders, "'%s' has a loader, but was not collected" % name
        del loaders[name]

    if loaders:
        assert False, "The follow loaders should not have been collected %s" % list(loaders)
