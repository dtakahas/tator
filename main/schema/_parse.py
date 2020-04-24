import logging

from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.request import Request
from openapi_core import create_spec
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.contrib.django import DjangoOpenAPIRequest

logger = logging.getLogger(__name__)

def _parse(request):
    """ Parses a request using Tator's generated OpenAPI spec.
    """
    # This request was processed by OpenAPIParserMixin
    if parse.validator is None:
        generator = SchemaGenerator(title='Tator REST API')
        spec = generator.get_schema()
        openapi_spec = create_spec(spec)
        parse.validator = RequestValidator(openapi_spec)
    openapi_request = DjangoOpenAPIRequest(request)
    if openapi_request.mimetype.startswith('application/json'):
        openapi_request.mimetype = 'application/json'
    result = parse.validator.validate(openapi_request)
    return result

parse.validator = None

class OpenAPIResponse(Request):
    def __init__(self, request, parsers=None, authenticators=None,
                 negotiator=None, parser_context=None):
        self._openapi = _parse(request)
        super().__init__(request, parsers, authenticators, negotiator, parser_context)

    def parse(self):
        self._openapi.raise_for_errors()
        out = {
            **self._openapi.parameters.path,
            **self._openapi.parameters.query,
        }
        if self._openapi.body:
            if isinstance(self._openapi.body, list):
                out['body'] = self._openapi.body
            else:
                out = {**out, **self._openapi.body}
        return out

class OpenAPIParserMixin:
    def initialize_request(self, request, *args, **kwargs):
        parser_context = self.get_parser_context(request)
        return OpenAPIResponse(
            request,
            parsers=self.get_parsers(),
            authenticators=self.get_authenticators(),
            negotiator=self.get_content_negotiator(),
            parser_context=parser_context,
        )
