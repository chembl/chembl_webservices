__author__ = 'mnowotka'

from chembl_webservices.base import ChEMBLApiBase
from tastypie.utils import trailing_slash
from django.conf.urls import *
from tastypie.authorization import Authorization
from chembl_webservices.base import ChEMBLApiSerializer
from tastypie.exceptions import BadRequest
from tastypie import http
from chembl_core_db.chemicalValidators import validateChemblId
from django.db.models import Count
from chembl_webservices.cache import ChemblCache

try:
    from chembl_compatibility.models import Assays
except ImportError:
    from chembl_core_model.models import Assays

class AssaysResource(ChEMBLApiBase):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta:
        resource_name = 'assays'
        authorization = Authorization()
        include_resource_uri = False
        paginator_class = None
        serializer = ChEMBLApiSerializer('assay')
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w-]*)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w-]*)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def get_bundle(self, assay):
        data = dict()
        data['chemblId'] = assay.get('chembl_id')
        data['assayType'] = assay.get('assay_type__assay_type')
        data['journal'] = assay.get('doc__journal')
        data['assayOrganism'] = assay.get('assay_organism')
        data['assayStrain'] = assay.get('assay_strain') or 'Unspecified'
        data['assayDescription'] = assay.get('description')
        data['numBioactivities'] = assay.get('count')

        return data

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, request=None, **kwargs):
        if kwargs.get('pk', False):
            pk = kwargs['pk']
            if not validateChemblId(pk):
                raise BadRequest("Invalid Chembl Identifier supplied:%s" % pk)
            assays = Assays.objects.filter(chembl_id=pk).annotate(count=Count('activities')).\
            values('chembl_id', 'assay_type__assay_type', 'doc__journal', 'assay_organism', 'assay_strain',
                                                                                            'description', 'count')
            if not len(assays):
                return http.HttpNotFound("Assay not found for identifier:%s" % pk)
            assay = assays[0]
        else:
            return http.HttpNotFound()
        return self.get_bundle(assay)

#-----------------------------------------------------------------------------------------------------------------------
