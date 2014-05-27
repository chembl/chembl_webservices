__author__ = 'mnowotka'

from chembl_webservices.base import ChEMBLApiBase
from chembl_webservices.base import ChEMBLApiSerializer
from tastypie.utils import trailing_slash
from django.conf.urls import *
from tastypie.authorization import Authorization
from chembl_webservices import __version__


class StatusResource(ChEMBLApiBase):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta:
        resource_name = 'status'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer('service')
        allowed_methods = ['get']

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, request=None, **kwargs):
        return {'status': 'UP', 'version': __version__}

#-----------------------------------------------------------------------------------------------------------------------
