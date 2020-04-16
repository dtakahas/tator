import functools
import logging

from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema

logger = logging.getLogger(__name__)

def is_valid(param, value):
    """ Checks if a value is valid according to its schema.
    """
    type_ = getattr(param, 'type', None)
    if type_ is None:
        type_ = getattr(param.schema, 'type', None)
    if type_ == openapi.TYPE_BOOLEAN:
        valid = type(value) == bool
    elif type_ == openapi.TYPE_INTEGER:
        valid = type(value) == int
    elif type_ == openapi.TYPE_NUMBER:
        try:
            float(value)
            valid = True
        except:
            valid = False
    elif type_ == openapi.TYPE_STRING:
        valid = type(value) == str
    elif type_ == openapi.TYPE_ARRAY:
        valid = type(value) == list
    elif type_ == openapi.TYPE_OBJECT:
        valid = type(value) == dict
    return True

class SchemaTemplate(SwaggerAutoSchema):
    def __init__(self, fields, view, path, method, components, request, overrides, operation_keys=None):
        """ Accepts a dict containing mapping from supported method to list of Field objects.
        """
        super().__init__(view, path, method, components, request, overrides, operation_keys)
        self.overrides['manual_parameters'] = fields.get(method, []) + fields.get('all', [])

    def add_manual_parameters(self, parameters):
        return self.overrides['manual_parameters']

    @classmethod
    def parse(cls, fields, request, kwargs):
        """ Returns a dict of parameter values from a request. Raises an exception if a required
            field is missing.
        """
        values = {}
       
        for field in fields.get('all', []) + fields.get(request.method, []):
            # Get default value
            default = getattr(field, 'default', None)

            # Grab the field value
            if field.in_ == 'body':
                values[field.name] = request.data.get(field.name, default)
            elif field.in_ == 'path':
                values[field.name] = kwargs.get(field.name, default)
            elif field.in_ == 'query':
                values[field.name] = request.query_params.get(field.name, default)

            # Check if required field 
            if field.required and values[field.name] is None:
                raise Exception(f'Missing required field "{field.name}" in request '
                                f'{field.in_} for {request.path}!')

            # Validate the value
            if values[field.name] is not None:
                if not is_valid(field, values[field.name]):
                    raise Exception(f'Invalid value for field "{field.name}" in request '
                                    f'{field.in_} for {request.path}! {valid[0].text}')
        return values

def make_schema(fields):
    class Schema(SchemaTemplate):
        __init__ = functools.partialmethod(SchemaTemplate.__init__, fields)
        parse = functools.partial(SchemaTemplate.parse, fields)

    return Schema
