from textwrap import dedent

from rest_framework.schemas.openapi import AutoSchema

from ._errors import error_responses
from ._message import message_schema
from ._message import message_with_id_schema

class UserDetailSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'GET':
            operation['operationId'] = 'GetUser'
        elif method == 'PATCH':
            operation['operationId'] = 'UpdateUser'
        operation['tags'] = ['Tator']
        return operation

    def get_description(self, path, method):
        if method == 'GET':
            short_desc = "Get user."
        elif method == 'PATCH':
            short_desc = "Update user."
        return f"{short_desc}"

    def _get_path_parameters(self, path, method):
        return [{
            'name': 'id',
            'in': 'path',
            'required': True,
            'description': 'A unique integer identifying a localization association.',
            'schema': {'type': 'integer'},
        }]

    def _get_filter_parameters(self, path, method):
        return []

    def _get_request_body(self, path, method):
        body = {}
        if method == 'PATCH':
            body = {'content': {'application/json': {
                'schema': {'$ref': '#/components/schemas/UserUpdate'},
            }}}
        return body

    def _get_responses(self, path, method):
        responses = error_responses()
        if method == 'GET':
            responses['200'] = {
                'description': 'Successful retrieval of user.',
                'content': {'application/json': {'schema': {
                    '$ref': '#/components/schemas/User',
                }}},
            }
        return responses

class CurrentUserSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'GET':
            operation['operationId'] = 'Whoami'
        operation['tags'] = ['Tator']
        return operation

    def get_description(self, path, method):
        return dedent("""\
        Get current user.

        Retrieves user making the request.
        """)

    def _get_path_parameters(self, path, method):
        return []

    def _get_filter_parameters(self, path, method):
        return []

    def _get_responses(self, path, method):
        responses = {
            '200': {
                'description': 'Successful retrieval of user who sent request.',
                'content': {'application/json': {'schema': {
                    '$ref': '#/components/schemas/User',
                }}},
            },
        }
        return responses
