import traceback
import logging

from rest_framework.schemas import AutoSchema
from rest_framework.compat import coreschema, coreapi
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist

from ..models import EntityState
from ..models import EntityTypeState
from ..models import EntityMediaBase
from ..models import EntityLocalizationBase
from ..models import MediaAssociation
from ..models import FrameAssociation
from ..models import LocalizationAssociation
from ..models import Version
from ..serializers import EntityStateSerializer
from ..serializers import EntityStateFrameSerializer
from ..serializers import EntityStateLocalizationSerializer

from ._annotation_query import get_annotation_queryset
from ._attributes import AttributeFilterSchemaMixin
from ._attributes import AttributeFilterMixin
from ._attributes import patch_attributes
from ._attributes import validate_attributes
from ._attributes import convert_attribute
from ._util import computeRequiredFields
from ._permissions import ProjectEditPermission

logger = logging.getLogger(__name__)

class StateListSchema(AutoSchema, AttributeFilterSchemaMixin):
    def get_manual_fields(self, path, method):
        manual_fields = super().get_manual_fields(path,method)
        postOnly_fields = []
        getOnly_fields = []

        manual_fields += [
            coreapi.Field(
                name='project',
                required=True,
                location='path',
                schema=coreschema.String(description='A unique integer identifying a project')
            ),
        ]

        if (method=='POST'):
            postOnly_fields = [
                coreapi.Field(name='media_ids',
                              required=False,
                              location='body',
                              schema=coreschema.String(description='Videos this state applies to. (list)')),
                coreapi.Field(name='localization_ids',
                              required=False,
                              location='body',
                              schema=coreschema.String(description='Localizations this state applies to')),
                coreapi.Field(name='type',
                   required=True,
                   location='body',
                   schema=coreschema.String(description='A unique integer value identifying an entity type state.')),
                coreapi.Field(name='frame',
                   required=False,
                   location='body',
                   schema=coreschema.String(description='Frame number')),
                coreapi.Field(name='<varies>',
                   required=False,
                   location='body',
                   schema=coreschema.String(description='A value for each column of the given `entity_type_id`, see /EntityTypeSchema'))]
        if (method=='GET'):
            getOnly_fields = [
                coreapi.Field(name='media_id',
                              required=False,
                              location='query',
                              schema=coreschema.String(description='A unique integer value identifying a video.')),
                coreapi.Field(name='type',
                              required=False,
                              location='query',
                              schema=coreschema.String(description='A unique integer value identifying an entity type.')),
                coreapi.Field(name='version',
                              required=False,
                              location='query',
                              schema=coreschema.String(description='A unique integer value identifying a Version')),
                coreapi.Field(name='modified',
                              required=False,
                              location='query',
                              schema=coreschema.String(description='Set to true for original + modified annotations, false for original only')),
                coreapi.Field(name='operation',
                              required=False,
                              location='query',
                              schema=coreschema.String(description='Operation to perform on the query. Valid values are:\ncount: Return the number of elements\nattribute_count: Return count split by a given attribute name')),
            ]

        return manual_fields + postOnly_fields + getOnly_fields + self.attribute_fields()

class StateListAPI(APIView, AttributeFilterMixin):
    """
    Create/List EntityState (by Video id)

    It is importarant to know the fields required for a given entity_type_id as they are expected
    in the request data for this function. As an example, if the entity_type_id has attributetypes
    associated with it named time and position, the JSON object must have them specified as keys.'

    Example:
    Entity_Type_id (3) refers to "Standard attributes". Standard attributes has 3 Attribute types
    associated with it, 'time', 'temperature', 'camera'. The JSON object in the request data should
    look like:
    ```
    {
       'entity_type_id': <entity_type_id>
       'frame': <frame_idx>,
       'time': <time>,
       'temperature': <value>,
       'camera': <value>
    }
    ```
    """
    schema=StateListSchema()
    permission_classes = [ProjectEditPermission]

    def get_queryset(self):
        filterType=self.request.query_params.get('type', None)

        mediaId=self.request.query_params.get('media_id', None)
        allStates = EntityState.objects.all()
        if mediaId != None:
            mediaId = list(map(lambda x: int(x), mediaId.split(',')))
            allStates = allStates.filter(Q(association__media__in=mediaId) | Q(association__frameassociation__extracted__in=mediaId))
        if filterType != None:
            allStates = allStates.filter(meta=filterType)
        if filterType == None and mediaId == None:
            allStates = allStates.filter(project=self.kwargs['project'])

        allStates = self.filter_by_attribute(allStates)

        if filterType:
            type_object=EntityTypeState.objects.get(pk=filterType)
            if type_object.association == 'Frame':
                allStates = allStates.annotate(frame=F('association__frameassociation__frame')).order_by('frame')
        return allStates

    def get(self, request, format=None, **kwargs):
        """
        Returns a list of all EntityStates associated with the given video.
        """
        filterType=self.request.query_params.get('type', None)
        try:
            self.validate_attribute_filter(request.query_params)
            annotation_ids, annotation_count, _ = get_annotation_queryset(
                kwargs['project'],
                request.query_params,
                self
            )
            allStates = EntityState.objects.filter(pk__in=annotation_ids)
            if self.operation:
                if self.operation == 'count':
                    return Response({'count': allStates.count()})
                else:
                    raise Exception('Invalid operation parameter!')
            else:
                if filterType:
                    type_object = EntityTypeState.objects.get(pk=filterType)
                    if type_object.association == 'Frame':
                        # Add frame association media to SELECT columns (frame is there from frame sort operation)
                        allStates = allStates.annotate(frame=F('association__frameassociation__frame')).order_by('frame')
                        # This optomization only works for frame-based associations
                        allStates = allStates.annotate(association_media=F('association__frameassociation__media'))
                        allStates = allStates.annotate(extracted=F('association__frameassociation__extracted'))
                        response = EntityStateFrameSerializer(allStates)
                    elif type_object.association == 'Localization':
                        localquery=LocalizationAssociation.objects.filter(entitystate=OuterRef('pk'))
                        allStates = allStates.annotate(association_color=F('association__localizationassociation__color'),
                                                       association_segments=F('association__localizationassociation__segments'),
                                                       association_localizations=Array(localquery.values('localizations')),
                                                       association_media=F('association__frameassociation__media'))
                        allStates = allStates.order_by('id')
                        response = EntityStateLocalizationSerializer(allStates)
                    else:
                        logger.warning("Using generic/slow serializer")
                        allStates = allStates.order_by('id')
                        response = EntityStateSerializer(allStates, many=True)
                    logger.info(allStates.query)
                else:
                    allStates = allStates.order_by('id')
                    response = EntityStateSerializer(allStates, many=True)
                responseData = response.data
                if request.accepted_renderer.format == 'csv':
                    if filterType:
                        type_object=EntityTypeState.objects.get(pk=filterType)
                        if type_object.association == 'Frame' and type_object.interpolation == InterpolationMethods.LATEST:
                            for idx,el in enumerate(responseData):
                                mediaEl=EntityMediaBase.objects.get(pk=el['association']['media'])
                                endFrame=0
                                if idx + 1 < len(responseData):
                                    next_element=responseData[idx+1]
                                    endFrame=next_element['association']['frame']
                                else:
                                    endFrame=mediaEl.num_frames
                                el['media']=mediaEl.name

                                el['endFrame'] = endFrame
                                el['startSeconds'] = int(el['association']['frame']) * mediaEl.fps
                                el['endSeconds'] = int(el['endFrame']) * mediaEl.fps
                return Response(responseData)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
            return response;

    def post(self, request, format=None, **kwargs):
        """
        Add a new EntityState for a given video.
        """
        entityType=None
        response=Response({})

        try:
            reqObject=request.data;
            media_ids=[]
            if 'media_ids' in reqObject:
                req_ids = reqObject['media_ids'];
                if type(req_ids) == list:
                    media_ids = req_ids
                else:
                    ## Handle when someone uses a singular video
                    media_ids.append(req_ids)
            else:
                raise Exception('Missing required field in request Object "media_ids", got={}'.format(reqObject))

            mediaElements=EntityMediaBase.objects.filter(pk__in=media_ids)

            if mediaElements.count() == 0:
                raise Exception('No matching media elements')

            project=mediaElements[0].project
            for video in mediaElements:
                if video.project != project:
                    raise Exception('Videos cross projects')


            modified = None
            if 'modified' in reqObject:
                modified = bool(reqObject['modified'])

            if 'version' in reqObject:
                version = Version.objects.get(pk=reqObject['version'])
            else:
                # If no version is given, assign the localization to version 0 (baseline)
                version = Version.objects.filter(project=project, number=0)
                if version.exists():
                    version = version[0]
                else:
                    # If version 0 does not exist, create it.
                    version = Version.objects.create(
                        name="Baseline",
                        description="Initial version",
                        project=project,
                        number=0,
                    )

            if 'type' in reqObject:
                entityTypeId=reqObject['type']
            else:
                raise Exception('Missing required field in request object "type"')

            entityType = EntityTypeState.objects.get(id=entityTypeId)

            reqFields, reqAttributes, attrTypes=computeRequiredFields(entityType)

            attrs={}
            for key, attrType in zip(reqAttributes, attrTypes):
                if key in reqObject:
                    convert_attribute(attrType, reqObject[key]) # Validates attr value
                    attrs[key] = reqObject[key];
                else:
                    # missing a key
                    raise Exception('Missing attribute value for "{}". Required for = "{}"'.
                                   format(key,entityType.name));

            obj = EntityState(project=project,
                              meta=entityType,
                              attributes=attrs,
                              created_by=request.user,
                              modified_by=request.user,
                              modified=modified,
                              version=version)

            association=None
            if entityType.association == "Media":
                association=MediaAssociation()
                association.save()
                association.media.add(*mediaElements)
            elif entityType.association == "Frame":
                if 'frame' not in reqObject:
                    raise Exception('Missing "frame" for Frame association')
                if len(media_ids) > 1:
                    raise Exception('Ambigious media id(s) specified for Frame Association')
                association=FrameAssociation(frame=reqObject['frame'])
                association.save()
                association.media.add(*mediaElements)
            elif entityType.association == "Localization":
                if 'localization_ids' not in reqObject:
                    raise Exception('Missing localization ids for localization association')
                localIds=reqObject['localization_ids']
                association=LocalizationAssociation()
                association.save()
                elements=EntityLocalizationBase.objects.filter(pk__in=localIds)
                association.localizations.add(*elements)
            else:
                #This is a programming error
                assoc=entityType.association
                name=entityType.name
                raise Exception(f'Unknown association type {assoc} for {name}')

            association.save()
            obj.association=association
            obj.save()
            response = Response({'id': obj.id},
                                status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response;

class StateDetailAPI(RetrieveUpdateDestroyAPIView):
    """ Default Update/Destory view... TODO add custom `get_queryset` to add user authentication checks
    """
    serializer_class = EntityStateSerializer
    queryset = EntityState.objects.all()
    permission_classes = [ProjectEditPermission]

    def delete(self, request, **kwargs):
        response = Response({}, status=status.HTTP_204_NO_CONTENT)
        try:
            state_object = EntityState.objects.get(pk=self.kwargs['pk'])
            self.check_object_permissions(request, state_object)
            association_object = state_object.association
            association_object.delete()
        except PermissionDenied as err:
            raise
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response;

    def patch(self, request, **kwargs):
        response = Response({})
        try:
            state_object = EntityState.objects.get(pk=self.kwargs['pk'])
            self.check_object_permissions(request, state_object)
            # Patch modified field
            if "modified" in request.data:
                state_object.modified = request.data["modified"]
                state_object.save()
            new_attrs = validate_attributes(request, state_object)
            patch_attributes(new_attrs, state_object)

        except PermissionDenied as err:
            raise
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        finally:
            return response;
