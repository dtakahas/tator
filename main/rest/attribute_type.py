import traceback

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django.core.exceptions import ObjectDoesNotExist
from drf_yasg import openapi

from ..models import AttributeTypeBase
from ..models import AttributeTypeBool
from ..models import AttributeTypeInt
from ..models import AttributeTypeFloat
from ..models import AttributeTypeEnum
from ..models import AttributeTypeString
from ..models import AttributeTypeDatetime
from ..models import AttributeTypeGeoposition
from ..models import EntityTypeBase
from ..models import Project
from ..serializers import AttributeTypeSerializer

from ._schema import make_schema
from ._attributes import convert_attribute
from ._permissions import ProjectFullControlPermission


class AttributeTypeListAPI(APIView):
    serializer_class = AttributeTypeSerializer
    permission_classes = [ProjectFullControlPermission]
    swagger_schema = make_schema({
        'all': [
            openapi.Parameter(
                name='project',
                in_='path',
                required=True,
                description='A unique integer identifying a project',
                type=openapi.TYPE_INTEGER),
        ],
        'GET': [
            openapi.Parameter(
                name='applies_to',
                in_='query',
                required=False,
                description='Unique integer identifying an entity type '
                            'that this attribute describes.',
                type=openapi.TYPE_INTEGER),
        ],
        'POST': [
            openapi.Parameter(
                name='name',
                in_='body',
                required=True,
                description='Name of the attribute.',
                schema=openapi.Schema(type=openapi.TYPE_STRING)),
            openapi.Parameter(
                name='description',
                in_='body',
                required=False,
                description='Description of the attribute.',
                schema=openapi.Schema(type=openapi.TYPE_STRING),
                default=""),
            openapi.Parameter(
                name='dtype',
                in_='body',
                required=True,
                description='Data type of the attribute',
                schema=openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['bool', 'int', 'float', 'enum', 'str', 'datetime', 'geopos'],
                ),
            ),
            openapi.Parameter(
                name='applies_to',
                in_='body',
                required=True,
                description='Unique integer identifying an entity type '
                            'that this attribute describes.',
                schema=openapi.Schema(type=openapi.TYPE_INTEGER)),
            openapi.Parameter(
                name='order',
                in_='body',
                required=False,
                description='Integer specifying where this attribute '
                            'is displayed in the UI. Negative values '
                            'are hidden by default.',
                schema=openapi.Schema(type=openapi.TYPE_INTEGER),
                default=0),
            openapi.Parameter(
                name='default',
                in_='body',
                required=False,
                description='Default value for the attribute.',
                schema=openapi.Schema(type=openapi.TYPE_STRING)),
            openapi.Parameter(
                name='lower_bound',
                in_='body',
                required=False,
                description='Lower bound for float or int dtype.',
                schema=openapi.Schema(type=openapi.TYPE_NUMBER)),
            openapi.Parameter(
                name='upper_bound',
                in_='body',
                required=False,
                description='Upper bound for float or int dtype.',
                schema=openapi.Schema(type=openapi.TYPE_NUMBER)),
            openapi.Parameter(
                name='choices',
                in_='body',
                required=False,
                description='Array of possible values for enum dtype.',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING))),
            openapi.Parameter(
                name='labels',
                in_='body',
                required=False,
                description='Array of labels for enum dtype.',
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING))),
            openapi.Parameter(
                name='autocomplete',
                in_='body',
                required=False,
                description='JSON object indictating URL of autocomplete service.',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'serviceUrl': openapi.Schema(type=openapi.TYPE_STRING)},
                    description='URL of autocomplete service.',
                ),
            ),
            openapi.Parameter(
                name='use_current',
                in_='body',
                required=False,
                description='True to use current datetime as default.',
                schema=openapi.Schema(type=openapi.TYPE_BOOLEAN)),
        ],
    })

    def get(self, request, format=None, **kwargs):
        response=Response({})
        try:
            params = self.swagger_schema.parse(request, kwargs)
            qs = AttributeTypeBase.objects.filter(project=params['project'])
            if params['applies_to']:
                qs = qs.filter(**params)
            response = Response(AttributeTypeSerializer(qs, many=True).data)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response

    def get_queryset(self):
        return AttributeTypeBase.objects.all()

    def post(self, request, format=None, **kwargs):
        response=Response({})
        try:
            # Get the parameters.
            params = self.swagger_schema.parse(request, kwargs)
            params['applies_to'] = EntityTypeBase.objects.get(pk=params['applies_to'])
            params['project'] = Project.objects.get(pk=params['project'])
            if params['order'] is None:
                params['order'] = 0

            # Pop off optional parameters.
            dtype = params.pop('dtype')
            default = params.pop('default')
            lower_bound = params.pop('lower_bound')
            upper_bound = params.pop('upper_bound')
            choices = params.pop('choices')
            labels = params.pop('labels')
            autocomplete = params.pop('autocomplete')
            use_current = params.pop('use_current')

            # Create the attribute type.
            if dtype == 'bool':
                obj = AttributeTypeBool(**params)
            elif dtype == 'int':
                obj = AttributeTypeInt(**params)
            elif dtype == 'float':
                obj = AttributeTypeFloat(**params)
            elif dtype == 'enum':
                obj = AttributeTypeEnum(**params, choices=choices, labels=labels)
            elif dtype == 'str':
                obj = AttributeTypeString(**params, autocomplete=autocomplete)
            elif dtype == 'datetime':
                obj = AttributeTypeDatetime(**params, use_current=use_current)
            elif dtype == 'geopos':
                obj = AttributeTypeGeoposition(**params)

            # Set parameters that need conversion.
            if default:
                obj.default = convert_attribute(obj, default)
            if lower_bound:
                obj.lower_bound = convert_attribute(obj, lower_bound)
            if upper_bound:
                obj.upper_bound = convert_attribute(obj, upper_bound)
            obj.save()
            response=Response({'message': 'Attribute type created successfully!', 'id': obj.id},
                              status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response;

class AttributeTypeDetailAPI(RetrieveUpdateDestroyAPIView):
    serializer_class = AttributeTypeSerializer
    permission_classes = [ProjectFullControlPermission]
    swagger_schema = make_schema({
        'all': [
            openapi.Parameter(
                name='pk',
                in_='path',
                required=True,
                description='A unique integer identifying an attribute type',
                type=openapi.TYPE_INTEGER),
        ],
        'GET': [],
        'PATCH': [
            openapi.Parameter(
                name='name',
                in_='body',
                required=False,
                description='Name of the attribute.',
                schema=openapi.Schema(type=openapi.TYPE_STRING)),
            openapi.Parameter(
                name='description',
                in_='body',
                required=False,
                description='Description of the attribute.',
                schema=openapi.Schema(type=openapi.TYPE_STRING)),
        ],
        'DELETE': [],
    })

    def patch(self, request, format=None, **kwargs):
        """ Updates a localization type.
        """
        response = Response({})
        try:
            params = self.schema.parse(request, kwargs)
            obj = AttributeTypeBase.objects.get(pk=params['pk'])
            if params['name'] is not None:
                obj.name = params['name']
            if params['description'] is not None:
                obj.description = params['description']
            obj.save()
            response=Response({'message': 'Attribute type updated successfully!'},
                              status=status.HTTP_200_OK)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        return response

    def get_queryset(self):
        return AttributeTypeBase.objects.all()


