import operator
from collections import namedtuple

import itypes
from coreapi import Link as CoreLink, Document as CoreDocument, Field as CoreField
from coreapi.compat import string_types


Field = namedtuple('Field', ['name', 'reference', 'required', 'location', 'type', 'description', 'example'])
Field.__new__.__defaults__ = (False, None, '', '', '', None)

Property = namedtuple('Property', ['name', 'reference', 'type', 'description', 'example', 'items', 'schema', 'enum'])
Property.__new__.__defaults__ = (False, None, '', '', None, None, [])


class Document(CoreDocument):
    def __init__(self, url=None, title=None, description=None, media_type=None, content=None, definitions=None,
                 consumes=None, produces=None):
        super(Document, self).__init__(url=url, title=title, description=description, media_type=media_type,
                                       content=content)
        if definitions is not None and not isinstance(definitions, (list, tuple)):
            raise TypeError("'definitions' must be a list.")
        if definitions is not None and any((not isinstance(definition, Schema) for definition in definitions)):
            raise TypeError("definitions must be schema objects.")
        if (consumes is not None) and not isinstance(consumes, (list, tuple)):
            raise TypeError("'consumes' must be a list.")
        if (consumes is not None) and any((
                not isinstance(consume, string_types) for consume in consumes
        )):
            raise TypeError("Consumes must be a list of strings.")
        if (produces is not None) and not isinstance(produces, (list, tuple)):
            raise TypeError("'produces' must be a list.")
        if (produces is not None) and any((
                not isinstance(produce, string_types) for produce in produces
        )):
            raise TypeError("Produces must be a list of strings.")

        self._definitions = () if definitions is None else tuple(definitions)
        self._consumes = () if consumes is None else tuple(consumes)
        self._produces = () if produces is None else tuple(produces)

    def clone(self, data):
        return self.__class__(self.url, self.title, self.description, self.media_type, data, self.definitions,
                              self.consumes, self.produces)

    def __eq__(self, other):
        return (
            super(Document, self).__eq__(other) and
            self.definitions == other.definitions and
            self.consumes == other.consumes and
            self.produces == other.produces
        )

    @property
    def definitions(self):
        return self._definitions

    @property
    def consumes(self):
        return self._consumes

    @property
    def produces(self):
        return self._produces


class Headers(itypes.Object):
    def __init__(self, name=None, description=None, value_type=None):
        if (name is not None) and (not isinstance(name, string_types)):
            raise TypeError("Argument 'name' must be a string.")
        if (description is not None) and (not isinstance(description, string_types)):
            raise TypeError("Argument 'description' must be a string.")
        if (value_type is not None) and (not isinstance(value_type, string_types)):
            raise TypeError("Argument 'value_type' must be a string.")

        self._name = '' if name is None else name
        self._description = '' if description is None else description
        self._type = '' if value_type is None else value_type

    def __eq__(self, other):
        return (
            isinstance(other, Headers) and
            self.name == other.name and
            self.description == other.description and
            self.type == other.type
        )

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def type(self):
        return self._type


class Schema(itypes.Object):
    def __init__(self, name=None, object_type=None, properties=None, required=None, items=None):
        if (name is not None) and (not isinstance(name, string_types)):
            raise TypeError("Argument 'name' must be a string.")
        if (object_type is not None) and (not isinstance(object_type, string_types)):
            raise TypeError("Argument 'object_type' must be a string.")
        if (properties is not None) and (not isinstance(properties, (list, tuple))):
            raise TypeError("Argument 'properties' must be a list.")
        if (properties is not None) and any((
                item for item in properties if not isinstance(item, Property)
        )):
            raise TypeError("Argument 'properties' must be a property object.")
        if (required is not None) and (not isinstance(required, (list, tuple))):
            raise TypeError("Argument 'required' must be a list.")
        if (required is not None) and any((
                item for item in required if not isinstance(item, string_types)
        )):
            raise TypeError("Argument 'required' must be a list of strings.")
        if (items is not None) and (not isinstance(items, (Schema, string_types))):
            raise TypeError("Argument 'items' must be a a schema object or string.")

        self._name = '' if name is None else name
        self._type = '' if object_type is None else object_type
        self._properties = () if properties is None else tuple(properties)
        self._required = () if required is None else tuple(required)
        self._items = '' if items is None else items

    def __eq__(self, other):
        return (
            isinstance(other, Schema) and
            self.name == other.name and
            self.type == other.type and
            self.properties == other.properties and
            set(self.required) == set(other.required) and
            self.items == other.items
        )

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def properties(self):
        return self._properties

    @property
    def required(self):
        return self._required

    @property
    def items(self):
        return self._items


class Response(itypes.Object):
    def __init__(self, status_code=None, description=None, schema=None, headers=None):
        if (status_code is not None) and (not isinstance(status_code, string_types)):
            raise TypeError("Argument 'status_code' must be a string.")
        if status_code is not None:
            assert 99 < int(status_code) < 600, "Status code must be valid http status code"
        if (description is not None) and (not isinstance(description, string_types)):
            raise TypeError("Argument 'description' must be a string.")
        if (schema is not None) and (not isinstance(schema, (Schema, string_types))):
            raise TypeError("Argument 'schema' must be a schema object or string.")
        if (headers is not None) and (not isinstance(headers, (list, tuple))):
            raise TypeError("Argument 'headers' must be a list.")
        if (headers is not None) and any((
                not isinstance(item, Headers) for item in headers
        )):
            raise TypeError("Argument 'headers' must be a list of headers objects.")

        self._status_code = '' if status_code is None else status_code
        self._description = '' if description is None else description
        self._schema = '' if schema is None else schema
        self._headers = () if headers is None else tuple(headers)

    def __eq__(self, other):
        return (
            isinstance(other, Response) and
            self.status_code == other.status_code and
            self.description == other.description and
            self.schema == other.schema and
            self.headers == other.headers
        )

    @property
    def status_code(self):
        return self._status_code

    @property
    def description(self):
        return self._description

    @property
    def schema(self):
        return self._schema

    @property
    def headers(self):
        return self._headers


class Link(CoreLink):
    def __init__(self, url=None, action=None, encoding=None, transform=None, title=None, description=None, fields=None,
                 responses=None):
        if (url is not None) and (not isinstance(url, string_types)):
            raise TypeError("Argument 'url' must be a string.")
        if (action is not None) and (not isinstance(action, string_types)):
            raise TypeError("Argument 'action' must be a string.")
        if (encoding is not None) and (not isinstance(encoding, string_types)):
            raise TypeError("Argument 'encoding' must be a string.")
        if (transform is not None) and (not isinstance(transform, string_types)):
            raise TypeError("Argument 'transform' must be a string.")
        if (title is not None) and (not isinstance(title, string_types)):
            raise TypeError("Argument 'title' must be a string.")
        if (description is not None) and (not isinstance(description, string_types)):
            raise TypeError("Argument 'description' must be a string.")
        if (fields is not None) and (not isinstance(fields, (list, tuple))):
            raise TypeError("Argument 'fields' must be a list.")
        if (fields is not None) and any(
                [not isinstance(item, (string_types, Field, CoreField)) for item in fields]):
            raise TypeError("Argument 'fields' must be a list of strings or fields.")
        if (responses is not None) and (not isinstance(responses, (list, tuple))):
            raise TypeError("Argument 'responses' must be a list.")
        if (responses is not None) and any((
                not isinstance(item, Response) for item in responses
        )):
            raise TypeError("Argument 'responses' must be a list of response objects.")
        self._url = '' if (url is None) else url
        self._action = '' if (action is None) else action
        self._encoding = '' if (encoding is None) else encoding
        self._transform = '' if (transform is None) else transform
        self._title = '' if (title is None) else title
        self._description = '' if (description is None) else description
        self._fields = () if (fields is None) else tuple(
            [item if isinstance(item, (Field, CoreField)) else Field(item, required=False, location='')
                for item in fields])
        self._responses = () if (responses is None) else tuple(responses)

    def __eq__(self, other):
        return (
            super(Link, self).__eq__(other) and
            all((operator.contains(self.responses, response) for response in other.responses))
        )

    @property
    def responses(self):
        return self._responses
