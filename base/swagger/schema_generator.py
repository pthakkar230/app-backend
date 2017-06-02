from coreapi.compat import urlparse
from django.utils.encoding import force_text
from rest_framework import serializers
from rest_framework.schemas import SchemaGenerator as RestSchemaGenerator, is_list_view
from rest_framework.settings import api_settings
from rest_framework.utils.field_mapping import ClassLookupDict

from .document import Document, Link, Property, Schema, Response, Field


types_lookup = ClassLookupDict({
    serializers.JSONField: 'object',
    serializers.Field: 'string',
    serializers.IntegerField: 'integer',
    serializers.FloatField: 'number',
    serializers.DecimalField: 'number',
    serializers.BooleanField: 'boolean',
    serializers.FileField: 'file',
    serializers.MultipleChoiceField: 'array',
    serializers.ManyRelatedField: 'array',
    serializers.Serializer: 'object',
    serializers.ListSerializer: 'array'
})


class SchemaGenerator(RestSchemaGenerator):
    def get_schema(self, request=None):
        """
        Generate a `coreapi.Document` representing the API schema.
        """
        if self.endpoints is None:
            inspector = self.endpoint_inspector_cls(self.patterns, self.urlconf)
            self.endpoints = inspector.get_api_endpoints()

        links = self.get_links(request)
        if not links:
            return None
        definitions = self.get_definitions(request)
        consumes = self.get_consumes()
        produces = self.get_produces()
        return Document(title=self.title, url=self.url, content=links, definitions=definitions, consumes=consumes,
                        produces=produces)

    def get_link(self, path, method, view):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        fields = self.get_path_fields(path, method, view)
        fields += self.get_serializer_fields(path, method, view)
        fields += self.get_pagination_fields(path, method, view)
        fields += self.get_filter_fields(path, method, view)

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method, view)
        else:
            encoding = None

        description = self.get_description(path, method, view)

        if self.url and path.startswith('/'):
            path = path[1:]

        responses = self.get_responses(path, method, view)

        return Link(
            url=urlparse.urljoin(self.url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=description,
            responses=responses
        )

    def get_serializer_fields(self, path, method, view):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        request body input, as determined by the serializer class.
        """
        if method not in ('PUT', 'PATCH', 'POST'):
            return []

        if not hasattr(view, 'get_serializer'):
            return []

        serializer = view.get_serializer()

        if isinstance(serializer, serializers.ListSerializer):
            return [
                Field(
                    name='data',
                    location='body',
                    required=True,
                    type='array'
                )
            ]

        if not isinstance(serializer, serializers.Serializer):
            return []

        fields = []
        for field in serializer.fields.values():
            if field.read_only or isinstance(field, serializers.HiddenField):
                continue

            required = field.required and method != 'PATCH'
            if isinstance(field, serializers.Serializer):
                field = Field(
                    name=field.field_name,
                    required=required,
                    reference=field.__class__.__name__.replace('Serializer', '')
                )
            else:
                description = force_text(field.help_text) if field.help_text else ''
                field = Field(
                    name=field.field_name,
                    location='form',
                    required=required,
                    description=description,
                    type=types_lookup[field]
                )
            fields.append(field)
        return fields

    def get_definitions(self, request):
        view_endpoints = []
        for path, method, callback in self.endpoints:
            view = self.create_view(callback, method, request)
            if getattr(view, 'exclude_from_schema', False):
                continue
            path = self.coerce_path(path, method, view)
            view_endpoints.append((path, method, view))

        definitions = {}
        for path, method, view in view_endpoints:
            if not hasattr(view, 'get_serializer'):
                continue
            serializer = view.get_serializer()

            if not isinstance(serializer, serializers.Serializer):
                return []
            self.add_definition(serializer, definitions)
        definitions.update(self.get_error_definitions())
        return list(definitions.values())

    def add_definition(self, serializer, definitions):
        name = serializer.__class__.__name__.replace('Serializer', '')
        properties = []
        required_fields = []
        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField) or getattr(field, 'write_only', False):
                continue
            if isinstance(field, serializers.Serializer):
                reference = field.__class__.__name__.replace('Serializer', '')
                if reference not in definitions:
                    self.add_definition(field, definitions)
                properties.append(Property(
                    name=field.field_name,
                    reference=reference
                ))
            if isinstance(field, serializers.MultipleChoiceField):
                description = force_text(field.help_text) if field.help_text else ''
                properties.append(Property(
                    name=field.field_name,
                    type=types_lookup[field],
                    description=description,
                    items='string',
                    enum=list(field.choices.keys())
                ))
            else:
                description = force_text(field.help_text) if field.help_text else ''
                properties.append(Property(
                    name=field.field_name,
                    type=types_lookup[field],
                    description=description,
                    items='string' if isinstance(field, serializers.ManyRelatedField) else None
                ))
                if field.required:
                    required_fields.append(field.field_name)
        definitions[name] = Schema(
            name=name,
            object_type='object',
            properties=properties,
            required=required_fields
        )

    def get_error_definitions(self):
        definitions = {
            'not_found': Schema(
                name="NotFound",
                object_type='object',
                properties=[
                    Property(
                        name="detail",
                        type="string",
                        description=""
                    )
                ],
            )
        }
        return definitions

    @staticmethod
    def get_bad_request_property(field):
        return Property(
            name=field.field_name,
            type='array',
            description="%s field errors" % field.field_name,
            items='string'
        )

    def get_bad_request_definition(self, serializer):
        if serializer is None:
            return None
        name = serializer.__class__.__name__.replace('Serializer', '')
        properties = [
            Property(
                name="non_field_errors",
                type='array',
                description="Errors not connected to any field",
                items='string'
            )
        ]
        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue
            if isinstance(field, serializers.Serializer):
                name = field.__class__.__name__.replace('Serializer', '')
                properties.append(Property(
                    name=field.field_name,
                    type='object',
                    description="",
                    schema=self.get_bad_request_definition(field)
                ))
            else:
                properties.append(self.get_bad_request_property(field))
        return Schema(
            name=name,
            object_type='object',
            properties=properties
        )

    def get_responses(self, path, method, view):
        responses = []
        schema_name = None
        serializer = None
        if hasattr(view, 'get_serializer'):
            serializer = view.get_serializer()
            schema_name = serializer.__class__.__name__.replace('Serializer', '')
        if is_list_view(path, method, view):
            responses.append(Response(
                status_code='200',
                description='%s list' % schema_name if schema_name else view.get_view_name(),
                schema=Schema(
                    name=schema_name,
                    items=schema_name
                ) if schema_name is not None else None
            ))
        else:
            bad_request_definition = self.get_bad_request_definition(serializer)
            if method == 'GET':
                responses.extend([
                    Response(
                        status_code='200',
                        description='%s retrieved' % schema_name,
                        schema=schema_name
                    ),
                    Response(
                        status_code='404',
                        description='%s not found' % schema_name,
                        schema="NotFound"
                    )
                ])
            elif method == 'POST':
                responses.extend([
                    Response(
                        status_code='201',
                        description='%s created' % schema_name if schema_name else view.get_view_name(),
                        schema=schema_name
                    ),
                    Response(
                        status_code='400',
                        description='Invalid data supplied',
                        schema=bad_request_definition
                    )
                ])
            elif method == 'PUT':
                responses.extend([
                    Response(
                        status_code='200',
                        description='%s updated' % schema_name,
                        schema=schema_name
                    ),
                    Response(
                        status_code='400',
                        description='Invalid data supplied',
                        schema=bad_request_definition
                    )
                ])
            elif method == 'PATCH':
                responses.extend([
                    Response(
                        status_code='200',
                        description='%s updated' % schema_name,
                        schema=schema_name
                    ),
                    Response(
                        status_code='400',
                        description='Invalid data supplied',
                        schema=bad_request_definition
                    ),
                    Response(
                        status_code='404',
                        description='%s not found' % schema_name,
                        schema="NotFound"
                    )
                ])
            elif method == 'DELETE':
                responses.extend([
                    Response(
                        status_code='204',
                        description='%s deleted' % schema_name
                    ),
                    Response(
                        status_code='404',
                        description='%s not found' % schema_name,
                        schema="NotFound"
                    )
                ])
        return responses

    @staticmethod
    def get_consumes():
        return [parser.media_type for parser in api_settings.DEFAULT_PARSER_CLASSES]

    @staticmethod
    def get_produces():
        return [renderer.media_type for renderer in api_settings.DEFAULT_RENDERER_CLASSES]
