from collections import OrderedDict
from unittest import TestCase

from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from base.namespace import Namespace
from users.tests.factories import UserFactory
from ..swagger.codec import OpenAPICodec
from ..swagger.document import Document, Schema, Property, Link, Response, Headers
from ..swagger.schema_generator import SchemaGenerator


class TestDocument(TestCase):
    def test_definitions(self):
        with self.assertRaises(TypeError) as definitions_list_error:
            Document(definitions='test')
            self.assertIn('list', definitions_list_error)
        with self.assertRaises(TypeError) as definition_schema_error:
            Document(definitions=[1])
            self.assertIn('schema', definition_schema_error)
        schema = Schema(name='Test', object_type='object')
        doc = Document(definitions=[schema])
        self.assertTupleEqual(doc.definitions, (schema,))

    def test_consumes(self):
        with self.assertRaises(TypeError) as consumes_list_error:
            Document(consumes='')
            self.assertIn('list', consumes_list_error)
        with self.assertRaises(TypeError) as consume_str_error:
            Document(consumes=[1])
            self.assertIn('string', consume_str_error)
        doc = Document(consumes=['application/json'])
        self.assertTupleEqual(doc.consumes, ('application/json',))

    def test_produces(self):
        with self.assertRaises(TypeError) as produces_list_error:
            Document(produces='')
            self.assertIn('list', produces_list_error)
        with self.assertRaises(TypeError) as produce_str_error:
            Document(produces=[1])
            self.assertIn('string', produce_str_error)
        doc = Document(produces=['application/json'])
        self.assertTupleEqual(doc.produces, ('application/json',))

    def test_clone(self):
        doc = Document(
            title='Example API',
            url='https://www.example.com',
            consumes=['application/json'],
            produces=['application/json'],
            definitions=[Schema(name='Test', object_type='object')],
            content={'test': 1}
        )
        copied = doc.clone({'test': 2})
        self.assertEqual(doc.title, copied.title)
        self.assertEqual(doc.url, copied.url)
        self.assertEqual(doc.consumes, copied.consumes)
        self.assertEqual(doc.produces, copied.produces)
        self.assertEqual(doc.definitions, copied.definitions)
        self.assertEqual(doc.data, {'test': 1})
        self.assertEqual(copied.data, {'test': 2})

    def test_equal(self):
        doc = Document(
            consumes=['application/json'],
            produces=['application/json'],
            definitions=[Schema(name='Test', object_type='object')],
        )
        doc2 = Document(
            consumes=['application/json'],
            produces=['application/json'],
            definitions=[Schema(name='Test', object_type='object')],
        )
        self.assertEqual(doc, doc2)


class TestHeaders(TestCase):
    def test_name(self):
        with self.assertRaises(TypeError) as name_str_error:
            Headers(name=1)
            self.assertIn('string', name_str_error)
        self.assertEqual(Headers(name=None).name, '')
        headers = Headers(name='test')
        self.assertEqual(headers.name, 'test')

    def test_description(self):
        with self.assertRaises(TypeError) as description_str_error:
            Headers(description=1)
            self.assertIn('string', description_str_error)
        self.assertEqual(Headers(description=None).description, '')
        headers = Headers(description='test')
        self.assertEqual(headers.description, 'test')

    def test_type(self):
        with self.assertRaises(TypeError) as type_str_error:
            Headers(value_type=1)
            self.assertIn('string', type_str_error)
        self.assertEqual(Headers(value_type=None).type, '')
        headers = Headers(value_type='test')
        self.assertEqual(headers.type, 'test')

    def test_equal(self):
        h1 = Headers(name='X-Test', description='Test', value_type='string')
        h2 = Headers(name='X-Test', description='Test', value_type='string')
        self.assertEqual(h1, h2)


class TestSchema(TestCase):
    def test_name(self):
        with self.assertRaises(TypeError) as name_str_error:
            Schema(name=1)
            self.assertIn('string', name_str_error)
        self.assertEqual(Schema(name=None).name, '')
        schema = Schema(name='test')
        self.assertEqual(schema.name, 'test')

    def test_type(self):
        with self.assertRaises(TypeError) as type_str_error:
            Schema(object_type=1)
            self.assertIn('string', type_str_error)
        self.assertEqual(Schema(object_type=None).type, '')
        schema = Schema(object_type='test')
        self.assertEqual(schema.type, 'test')

    def test_properties(self):
        with self.assertRaises(TypeError) as properties_list_error:
            Schema(properties=1)
            self.assertIn('list', properties_list_error)
        with self.assertRaises(TypeError) as properties_object_error:
            Schema(properties=[1])
            self.assertIn('property object', properties_object_error)
        prop = Property(name='id', type='integer', description='Test description')
        schema = Schema(properties=[prop])
        self.assertEqual(schema.properties, (prop,))

    def test_required(self):
        with self.assertRaises(TypeError) as required_list_error:
            Schema(required=1)
            self.assertIn('list', required_list_error)
        with self.assertRaises(TypeError) as required_str_error:
            Schema(required=[1])
            self.assertIn('string', required_str_error)
        schema = Schema(required=['id'])
        self.assertEqual(schema.required, ('id',))

    def test_items(self):
        with self.assertRaises(TypeError) as items_list_error:
            Schema(items=1)
            self.assertIn('list', items_list_error)
        schema = Schema(items='Test')
        self.assertEqual(schema.items, 'Test')
        items = Schema()
        schema = Schema(items=items)
        self.assertEqual(schema.items, items)

    def test_equal(self):
        s1 = Schema(
            name="Test",
            object_type='object',
            properties=[
                Property(name='id', type='integer', description='Test description'),
                Property(name='name', type='string', description='Test description'),
            ],
            required=['id'],
        )
        s2 = Schema(
            name="Test",
            object_type='object',
            properties=[
                Property(name='id', type='integer', description='Test description'),
                Property(name='name', type='string', description='Test description'),
            ],
            required=['id'],
        )
        self.assertEqual(s1, s2)


class TestResponse(TestCase):
    def test_status_code(self):
        with self.assertRaises(TypeError) as status_code_str_error:
            Response(status_code=1)
            self.assertIn('string', status_code_str_error)
        with self.assertRaises(AssertionError):
            Response(status_code='1')
        self.assertEqual(Response(status_code=None).status_code, '')
        response = Response(status_code='200')
        self.assertEqual(response.status_code, '200')

    def test_description(self):
        with self.assertRaises(TypeError) as description_str_error:
            Response(description=1)
            self.assertIn('string', description_str_error)
        self.assertEqual(Response(description=None).description, '')
        self.assertEqual(Response(description='test').description, 'test')

    def test_schema(self):
        with self.assertRaises(TypeError) as schema_str_error:
            Response(schema=1)
            self.assertIn('string', schema_str_error)
        with self.assertRaises(TypeError) as schema_object_error:
            Response(schema=1)
            self.assertIn('schema object', schema_object_error)
        self.assertEqual(Response(schema='Test').schema, 'Test')
        schema = Schema()
        self.assertEqual(Response(schema=schema).schema, schema)

    def test_headers(self):
        with self.assertRaises(TypeError) as headers_list_error:
            Response(headers=1)
            self.assertIn('list', headers_list_error)
        with self.assertRaises(TypeError) as headers_object_error:
            Response(headers=[1])
            self.assertIn('headers object', headers_object_error)
        headers = Headers()
        self.assertEqual(Response(headers=[headers]).headers, (headers,))

    def test_equal(self):
        r1 = Response(status_code='200', description='Test retrieved',
                      schema=Schema(object_type='object', items='Test'))
        r2 = Response(status_code='200', description='Test retrieved',
                      schema=Schema(object_type='object', items='Test'))
        self.assertEqual(r1, r2)


class TestLink(TestCase):
    def test_responses(self):
        with self.assertRaises(TypeError) as responses_list_error:
            Link(responses=1)
            self.assertIn('list', responses_list_error)
        with self.assertRaises(TypeError) as responses_object_error:
            Link(responses=[1])
            self.assertIn('response object', responses_object_error)
        response = Response()
        self.assertEqual(Link(responses=[response]).responses, (response,))

    def test_equal(self):
        l1 = Link(url='/', action='get', responses=[
            Response(status_code='200', description='Test retrieved',
                     schema=Schema(object_type='object', items='Test')),
            Response(status_code='201', description='Test created', schema='Test')
        ])
        l2 = Link(url='/', action='get', responses=[
            Response(status_code='201', description='Test created', schema='Test'),
            Response(status_code='200', description='Test retrieved',
                     schema=Schema(object_type='object', items='Test')),
        ])
        self.assertEqual(l1, l2)


class TestOpenAPICodec(TestCase):
    def setUp(self):
        self.definition = Schema(
            name="Test",
            object_type='object',
            properties=[
                Property(name='id', type='integer', description='Test description'),
                Property(name='name', type='string', description='Test description'),
            ],
            required=['id'],
        )
        self.document = Document(
            title='Example API',
            url='https://www.example.com',
            consumes=['application/json'],
            produces=['application/json'],
            definitions=[self.definition],
            content={
                'link_get': Link(url='/id/', action='get', responses=[
                    Response(status_code='200', description='Test retrieved', schema=self.definition)
                ]),
                'link_get_array': Link(url='/', action='get', responses=[
                    Response(status_code='200', description='Test retrieved',
                             schema=Schema(object_type='object', items='Test'))
                ]),
                'link_post': Link(url='/', action='post', responses=[
                    Response(status_code='201', description='Test created', schema='Test')
                ])
            }
        )
        self.codec = OpenAPICodec()
        self.swagger = self.codec.generate_swagger_object(self.document)

    def test_encode(self):
        with self.assertRaises(TypeError):
            self.codec.encode({})
        doc = Document(title="Test")
        expected = b'{"swagger": "2.0", "info": {"title": "Test", "version": ""}, "paths": {}, "definitions": {}}'
        self.assertEqual(self.codec.encode(doc), expected)

    def test_consumes(self):
        self.assertIn('consumes', self.swagger)
        expected = ('application/json',)
        self.assertEqual(self.swagger['consumes'], expected)

    def test_produces(self):
        self.assertIn('produces', self.swagger)
        expected = ('application/json',)
        self.assertEqual(self.swagger['produces'], expected)

    def test_definitions(self):
        self.assertIn('definitions', self.swagger)
        expected = OrderedDict([
            (self.definition.name, OrderedDict([
                ("type", self.definition.type),
                ("properties", OrderedDict([
                    ("id", {
                        "type": "integer",
                        "description": "Test description"
                    }),
                    ("name", {
                        "type": "string",
                        "description": "Test description"
                    })
                ])),
                ("required", tuple(self.definition.required)),
            ]))
        ])
        self.assertDictEqual(self.swagger['definitions'], expected)

    def test_responses(self):
        self.assertIn('paths', self.swagger)
        expected = OrderedDict([
            ('/id/', OrderedDict([
                ('get', {
                    'operationId': 'link_get',
                    'parameters': [],
                    'responses': OrderedDict([
                        ('200', {
                            'description': 'Test retrieved',
                            'schema': OrderedDict([
                                ('type', 'object'),
                                ('properties', OrderedDict([
                                    ('id', {
                                        'type': 'integer',
                                        'description': 'Test description'
                                    }),
                                    ('name', {
                                        'type': 'string',
                                        'description': 'Test description'
                                    })
                                ])),
                                ('required', ('id',)),
                            ]),
                        })
                    ])
                }),
            ])),
            ('/', OrderedDict([
                ('get', {
                    'operationId': 'link_get_array',
                    'parameters': [],
                    'responses': OrderedDict([
                        ('200', {
                            'description': 'Test retrieved',
                            'schema': OrderedDict([
                                ('type', 'array'),
                                ('items', {
                                    '$ref': '#/definitions/Test'
                                })
                            ]),
                        })
                    ])
                }),
                ('post', {
                    'operationId': 'link_post',
                    'parameters': [],
                    'responses': OrderedDict([
                        ('201', {
                            'description': 'Test created',
                            'schema': {
                                '$ref': '#/definitions/Test'
                            },
                        })
                    ])
                }),
            ]))
        ])

        self.assertDictEqual(expected, self.swagger['paths'])

    def assertDictEqual(self, d1, d2, msg=None):
        for k, v1 in d1.items():
            self.assertIn(k, d2, msg)
            v2 = d2[k]
            if isinstance(v1, dict):
                self.assertDictEqual(v1, v2, msg)
            else:
                self.assertEqual(v1, v2, msg)
        return True


class TestSchemaGenerator(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.factory = APIRequestFactory()

    def _request(self):
        request = self.factory.get('/')
        request.namespace = Namespace.from_name(self.user.username)
        force_authenticate(request, user=self.user)
        return request

    def test_get_schema(self):
        request = self._request()
        generator = SchemaGenerator(title="Test API")
        schema = generator.get_schema(request=Request(request))
        self.assertIsNotNone(generator.endpoints)
        self.assertIsInstance(schema, Document)

    def test_get_empty_schema(self):
        request = self._request()
        generator = SchemaGenerator(patterns=[])
        schema = generator.get_schema(request=Request(request))
        self.assertIsNone(schema)
