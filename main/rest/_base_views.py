import traceback

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from ..schema import parse

class BaseListView(APIView):
    """ Base class for list views.
    """
    http_method_names = ['get', 'post']

    def get(self, request, format=None, **kwargs):
        response = Response({})
        try:
            params = parse(request)
            response_data = self._get(params)
            response = Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        return response

    def post(self, request, format=None, **kwargs):
        response = Response({})
        try:
            params = parse(request)
            response_data = self._post(params)
            response = Response(response_data, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        return response

    @staticmethod
    def copy_docstrings(cls):
        cls.get.__doc__ = cls._get.__doc__
        cls.post.__doc__ = cls._post.__doc__

class BaseDetailView(APIView):
    """ Base class for detail views.
    """
    http_method_names = ['get', 'patch', 'delete']

    def get(self, request, format=None, **kwargs):
        try:
            params = parse(request)
            response_data = self._get(params)
            response = Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        return response

    def patch(self, request, format=None, **kwargs):
        try:
            params = parse(request)
            response_data = self._patch(params)
            response = Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        return response

    def delete(self, request, format=None, **kwargs):
        try:
            params = parse(request)
            response_data = self._delete(params)
            response = Response(response_data, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist as dne:
            response=Response({'message' : str(dne)},
                              status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            response=Response({'message' : str(e),
                               'details': traceback.format_exc()}, status=status.HTTP_400_BAD_REQUEST)
        return response

    @staticmethod
    def copy_docstrings(cls):
        cls.get.__doc__ = cls._get.__doc__
        cls.patch.__doc__ = cls._patch.__doc__
        cls.delete.__doc__ = cls._delete.__doc__