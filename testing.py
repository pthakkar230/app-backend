
import os

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
root = pjoin(here, 'app')

with open(pjoin(root, 'utils', 'loading.py')) as f:
    code = compile(f.read(), "loading.py", 'exec')
    globs, locs = {}, {}
    exec(code, globs)
assert 'iter_modules' in globs