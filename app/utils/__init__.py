import re
from semantic_version import Version, Spec
from .exceptions import abort, http_excs, http_codes

def match_specs(version, *specs):
    for s in specs:
        if not Spec(s).match(Version(version)):
            return False
    return True
