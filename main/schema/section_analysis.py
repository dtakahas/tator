from rest_framework.schemas.openapi import AutoSchema

from ._attributes import attribute_filter_parameter_schema

class SectionAnalysisSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['tags'] = ['SectionAnalysis']
        return operation

    def _get_path_parameters(self, path, method):
        return [{
            'name': 'project',
            'in': 'path',
            'required': True,
            'description': 'A unique integer identifying a project.',
            'schema': {'type': 'integer'},
        }]

    def _get_filter_parameters(self, path, method):
        return [
            {
                'name': 'media_id',
                'in': 'query',
                'required': False,
                'description': 'Unique integer identifying a media. Use this to do analyis '
                               'on a single file instead of sections.',
                'explode': False,
                'schema': {
                    'type': 'array',
                    'items': {
                        'type': 'integer',
                        'minimum': 1,
                    },
                },
            },
        ] + attribute_filter_parameter_schema

    def _get_request_body(self, path, method):
        return {}

    def _get_responses(self, path, method):
        responses = {}
        responses['404'] = {'description': 'Failure to find project with given ID.'}
        responses['400'] = {'description': 'Bad request.'}
        if method == 'GET':
            responses['200'] = {'description': 'Successful retrieval of section analysis.'}
        return responses

