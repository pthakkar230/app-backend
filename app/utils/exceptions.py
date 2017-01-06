import sys
from werkzeug import exceptions as http_excs
from flask_restplus import abort as restplus_abort

http_codes = http_excs.default_exceptions

def abort(code, message=None, **kwargs):
	"""Properly abort the current request.

	A default message is provided based on the code
	if none is given. Raise a HTTPException for the
	given status code. Attach any keyword arguments
	to the exception for later processing.
	"""
	return restplus_abort(code=code, status=code,
		message=(message or code_gist(code)), **kwargs)

def code_gist(code):
	"""Get the gist of an http error code"""
	return http_codes[code].description
