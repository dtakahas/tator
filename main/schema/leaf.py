from textwrap import dedent

from rest_framework.schemas.openapi import AutoSchema

from ._errors import error_responses
from ._message import message_schema
from ._message import message_with_id_list_schema
from ._attributes import attribute_filter_parameter_schema

boilerplate = dedent("""\
Leaves are used to define label hierarchies that can be used for autocompletion
of string attribute types. Leaves are a type of entity in Tator, meaning they
can be described by user-defined attributes.
""")

class LeafSuggestionSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'GET':
            operation['operationId'] = 'LeafSuggestion'
        operation['tags'] = ['Tator']
        return operation

    def get_description(self, path, method):
        return dedent("""\
        Get list of autocomplete suggestions.

        This endpoint is compatible with devbridge suggestion format. It performs
        a glob search on leaf objects in the project.

        <https://github.com/kraaden/autocomplete>
        """)

    def _get_path_parameters(self, path, method):
        return [
            {
                'name': 'project',
                'in': 'path',
                'required': True,
                'description': 'A unique integer identifying a project.',
                'schema': {'type': 'integer'},
            },
            {
                'name': 'ancestor',
                'in': 'path',
                'required': True,
                'description': 'Get descendents of a leaf element (inclusive), '
                               'by path (i.e. ITIS.Animalia).',
                'schema': {'type': 'string'},
            },
        ]

    def _get_filter_parameters(self, path, method):
        params = []
        if method == 'GET':
            params = [
                {
                    'name': 'minLevel',
                    'in': 'query',
                    'required': False,
                    'description': 'Integer specifying level of results that may be returned. '
                                   'For example, 2 refers to grandchildren of the level specified '
                                   'by the `ancestor` parameter.',
                    'schema': {'type': 'integer'},
                },
                {
                    'name': 'query',
                    'in': 'query',
                    'required': True,
                    'description': 'String to search for matching names.',
                    'schema': {'type': 'string'},
                },
            ]
        return params

    def _get_request_body(self, path, method):
        return {}

    def _get_responses(self, path, method):
        responses = error_responses()
        if method == 'GET':
            responses['200'] = {
                'description': 'Successful retrieval of suggestions.',
                'content': {'application/json': {'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/components/schemas/LeafSuggestion'},
                }}},
            }
        return responses

class LeafListSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'POST':
            operation['operationId'] = 'CreateLeafList'
        elif method == 'GET':
            operation['operationId'] = 'GetLeafList'
        elif method == 'PATCH':
            operation['operationId'] = 'UpdateLeafList'
        elif method == 'DELETE':
            operation['operationId'] = 'DeleteLeafList'
        operation['tags'] = ['Tator']
        return operation

    def get_description(self, path, method):
        long_desc = ''
        if method == 'GET':
            short_desc = 'Get leaf list.'
        elif method == 'POST':
            short_desc = 'Create leaf list.'
            long_desc = dedent("""\
            This method does a bulk create on a list of `LeafSpec` objects. A 
            maximum of 500 leaves may be created in one request.
            """)
        elif method == 'PATCH':
            short_desc = 'Update leaf list.'
            long_desc = dedent("""\
            This method does a bulk update on all leaves matching a query. Only 
            user-defined attributes may be bulk updated.
            """)
        elif method == 'DELETE':
            short_desc = 'Delete leaf list.'
            long_desc = dedent("""\
            This method performs a bulk delete on all leaves matching a query. It is 
            recommended to use a GET request first to check what is being deleted.
            """)
        return f"{short_desc}\n\n{boilerplate}\n\n{long_desc}"

    def _get_path_parameters(self, path, method):
        return [{
            'name': 'project',
            'in': 'path',
            'required': True,
            'description': 'A unique integer identifying a project.',
            'schema': {'type': 'integer'},
        }]

    def _get_filter_parameters(self, path, method):
        params = []
        if method in ['GET', 'PATCH', 'DELETE']:
            params = [
                {
                    'name': 'ancestor',
                    'in': 'query',
                    'required': False,
                    'description': 'Get descendents of a leaf element (inclusive), '
                                   'by path (i.e. ITIS.Animalia).',
                    'schema': {'type': 'string'},
                },
                {
                    'name': 'type',
                    'in': 'query',
                    'required': False,
                    'description': 'Unique integer identifying a leaf type.',
                    'schema': {'type': 'integer'},
                },
                {
                    'name': 'name',
                    'in': 'query',
                    'required': False,
                    'description': 'Name of the leaf element.',
                    'schema': {'type': 'string'},
                },
            ] + attribute_filter_parameter_schema
            # Remove search as it is not yet supported.
            params = [p for p in params if p['name'] != 'search']
        return params

    def _get_request_body(self, path, method):
        body = {}
        if method == 'POST':
            body = {'content': {'application/json': {
                'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/components/schemas/LeafSpec'},
                    'maxItems': 500,
                },
            }}}
        if method == 'PATCH':
            body = {'content': {'application/json': {
                'schema': {
                    '$ref': '#/components/schemas/AttributeBulkUpdate',
                },
            }}}
        return body

    def _get_responses(self, path, method):
        responses = error_responses()
        if method == 'GET':
            responses['200'] = {
                'description': 'Successful retrieval of leaf list.',
                'content': {'application/json': {'schema': {
                    'type': 'array',
                    'items': {'$ref': '#/components/schemas/Leaf'},
                }}},
            }
        elif method == 'POST':
            responses['201'] = message_with_id_list_schema('leaf')
        elif method == 'PATCH':
            responses['200'] = message_schema('update', 'leaf list')
        elif method == 'DELETE':
            responses['200'] = message_schema('deletion', 'leaf list')
        return responses

class LeafDetailSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'GET':
            operation['operationId'] = 'GetLeaf'
        elif method == 'PATCH':
            operation['operationId'] = 'UpdateLeaf'
        elif method == 'DELETE':
            operation['operationId'] = 'DeleteLeaf'
        operation['tags'] = ['Tator']
        return operation

    def get_description(self, path, method):
        if method == 'GET':
            short_desc = 'Get leaf.'
        elif method == 'PATCH':
            short_desc = 'Update leaf.'
        elif method == 'DELETE':
            short_desc = 'Delete leaf.'
        return f"{short_desc}\n\n{boilerplate}"

    def _get_path_parameters(self, path, method):
        return [{
            'name': 'id',
            'in': 'path',
            'required': True,
            'description': 'A unique integer identifying a leaf.',
            'schema': {'type': 'integer'},
        }]

    def _get_filter_parameters(self, path, method):
        return []

    def _get_request_body(self, path, method):
        body = {}
        if method == 'PATCH':
            body = {'content': {'application/json': {
                'schema': {'$ref': '#/components/schemas/LeafUpdate'},
            }}}
        return body

    def _get_responses(self, path, method):
        responses = error_responses()
        if method == 'GET':
            responses['200'] = {
                'description': 'Successful retrieval of leaf.',
                'content': {'application/json': {'schema': {
                    '$ref': '#/components/schemas/Leaf',
                }}},
            }
        elif method == 'PATCH':
            responses['200'] = message_schema('update', 'leaf')
        elif method == 'DELETE':
            responses['200'] = {'description': 'Successful deletion of leaf.'}
        return responses

