__author__ = 'mnowotka'

from chembl_webservices.base import ChEMBLApiBase
from tastypie.utils import trailing_slash
from django.conf.urls import *
from tastypie import http
from tastypie.exceptions import BadRequest
from chembl_core_db.chemicalValidators import validateChemblId

#-----------------------------------------------------------------------------------------------------------------------

class DerivativeResource(ChEMBLApiBase):
    def __init__(self):
        self.core_resource_name = None
        self.name = None
        super(DerivativeResource, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^" + self.parent_resource_name + "/(?P<pk>\w[\w-]*)/(?P<resource_name>%s)%s$" %
                (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^" + self.parent_resource_name + "/(?P<pk>\w[\w-]*)/(?P<resource_name>%s)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def validateId(self, pk):
        return validateChemblId(pk)

#-----------------------------------------------------------------------------------------------------------------------

    def get_bundle(self, objs):
        raise NotImplementedError

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, request=None, **kwargs):
        if kwargs.get('pk', False):
            pk = kwargs['pk']
            if not self.validateId(pk):
                raise BadRequest("Invalid Identifier supplied:%s" % pk)
            return self.get_bundle(self.getCoreResources(pk))
        else:
            return http.HttpNotFound()

#-----------------------------------------------------------------------------------------------------------------------

    def getCoreResources(self, pk):
        raise NotImplementedError

#-----------------------------------------------------------------------------------------------------------------------
