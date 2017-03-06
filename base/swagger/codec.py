import json
from collections import OrderedDict

from coreapi.compat import urlparse, string_types
from openapi_codec import OpenAPICodec as CoreOpenAPICodec
from django.utils.encoding import force_bytes
from openapi_codec.encode import _get_links
from openapi_codec.utils import get_method, get_encoding, get_location

from .document import Document, Schema


class OpenAPICodec(CoreOpenAPICodec):
    def encode(self, document, **options):
        if not isinstance(document, Document):
            raise TypeError('Expected a `coreapi.Document` instance')
        data = self.generate_swagger_object(document)
        return force_bytes(json.dumps(data))

    def generate_swagger_object(self, document):
        """
        Generates root of the Swagger spec.
        """
        parsed_url = urlparse.urlparse(document.url)

        swagger = OrderedDict()

        swagger['swagger'] = '2.0'
        swagger['info'] = OrderedDict()
        swagger['info']['title'] = document.title
        swagger['info']['version'] = ''  # Required by the spec
        if document.consumes:
            swagger['consumes'] = document.consumes
        if document.produces:
            swagger['produces'] = document.produces

        if parsed_url.netloc:
            swagger['host'] = parsed_url.netloc
        if parsed_url.scheme:
            swagger['schemes'] = [parsed_url.scheme]

        swagger['paths'] = self._get_paths_object(document)
        swagger['definitions'] = self._get_definitions_object(document)

        return swagger

    def _get_paths_object(self, document):
        paths = OrderedDict()

        links = _get_links(document)

        for operation_id, link, tags in links:
            if link.url not in paths:
                paths[link.url] = OrderedDict()

            method = get_method(link)
            operation = self._get_operation(operation_id, link, tags)
            paths[link.url].update({method: operation})

        return paths

    def _get_definitions_object(self, document):
        definitions = OrderedDict()
        for definition in document.definitions:
            if definition.name not in definitions:
                definitions[definition.name] = self._get_definition_object(definition)
        return definitions

    def _get_definition_object(self, definition):
        def_obj = OrderedDict(
            type=definition.type,
            properties=self._get_properties(definition)
        )
        if getattr(definition, 'required', None):
            def_obj['required'] = definition.required

        return def_obj

    def _get_schema_object(self, definition):
        if isinstance(definition, Schema):
            if definition.items:
                return OrderedDict(
                    type='array',
                    items=self._get_schema_object(definition.items)
                )
            else:
                return self._get_definition_object(definition)
        if isinstance(definition, string_types) and definition:
            return {"$ref": "#/definitions/%s" % definition}

    @staticmethod
    def _get_properties(definition):
        properties = OrderedDict()
        for prop in definition.properties:
            properties[prop.name] = {}
            if prop.reference:
                properties[prop.name].update({
                    '$ref': '#/definitions/%s' % prop.reference
                })
            else:
                update = {
                    'type': prop.type,
                    'description': prop.description,
                }
                if prop.items:
                    update['items'] = {'type': prop.items}
                properties[prop.name].update(update)
        return properties

    def _get_operation(self, operation_id, link, tags):
        encoding = get_encoding(link)
        description = link.description.strip()
        summary = description.splitlines()[0] if description else None

        operation = {
            'operationId': operation_id,
            'responses': self._get_responses(link),
            'parameters': self._get_parameters(link, encoding)
        }

        if description:
            operation['description'] = description
        if summary:
            operation['summary'] = summary
        if encoding:
            operation['consumes'] = [encoding]
        if tags:
            operation['tags'] = tags
        return operation

    @staticmethod
    def _get_parameters(link, encoding):
        """
        Generates Swagger Parameter Item object.
        """
        parameters = []
        properties = {}
        required = []

        for field in link.fields:
            location = get_location(link, field)
            if location == 'form':
                if encoding in ('multipart/form-data', 'application/x-www-form-urlencoded'):
                    # 'formData' in swagger MUST be one of these media types.
                    parameter = {
                        'name': field.name,
                        'required': field.required,
                        'in': 'formData',
                        'description': field.description,
                        'type': field.type or 'string',
                    }
                    if field.type == 'array':
                        parameter['items'] = {'type': 'string'}
                    parameters.append(parameter)
                else:
                    # Expand coreapi fields with location='form' into a single swagger
                    # parameter, with a schema containing multiple properties.
                    use_type = field.type or 'string'
                    if use_type == 'file':
                        use_type = 'string'

                    if field.reference:
                        schema_property = {
                            '$ref': '#/definitions/%s' % field.reference
                        }
                    else:
                        schema_property = {
                            'description': field.description,
                            'type': use_type,
                        }
                        if field.type == 'array':
                            schema_property['items'] = {'type': 'string'}
                    properties[field.name] = schema_property
                    if field.required:
                        required.append(field.name)
            elif location == 'body':
                if encoding == 'application/octet-stream':
                    # https://github.com/OAI/OpenAPI-Specification/issues/50#issuecomment-112063782
                    schema = {'type': 'string', 'format': 'binary'}
                else:
                    schema = {}
                parameter = {
                    'name': field.name,
                    'required': field.required,
                    'in': location,
                    'description': field.description,
                    'schema': schema
                }
                parameters.append(parameter)
            else:
                parameter = {
                    'name': field.name,
                    'required': field.required,
                    'in': location,
                    'description': field.description or '',
                    'type': field.type or 'string',
                }
                if field.type == 'array':
                    parameter['items'] = {'type': 'string'}
                parameters.append(parameter)

        if properties:
            parameter = {
                'name': 'data',
                'in': 'body',
                'schema': {
                    'type': 'object',
                    'properties': properties
                }
            }
            if required:
                parameter['schema']['required'] = required
            parameters.append(parameter)

        return parameters

    def _get_responses(self, link):
        """
        Returns minimally acceptable responses object based
        on action / method type.
        """
        responses = OrderedDict()
        for response in link.responses:
            responses[response.status_code] = {
                'description': response.description or '',
            }
            if response.schema:
                responses[response.status_code]['schema'] = self._get_schema_object(response.schema)
        return responses
