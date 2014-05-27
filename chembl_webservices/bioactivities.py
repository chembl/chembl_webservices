__author__ = 'mnowotka'

from chembl_webservices.base import ChEMBLApiBase
from chembl_webservices.assays import AssaysResource
from chembl_webservices.targets import TargetsResource
from chembl_webservices.compounds import CompoundsResource
from tastypie.utils import trailing_slash
from chembl_webservices.base import ChEMBLApiSerializer
from django.conf.urls import *
from tastypie import http
from tastypie.authorization import Authorization
from tastypie.exceptions import BadRequest
from chembl_core_db.chemicalValidators import validateChemblId
from chembl_webservices.cache import ChemblCache

try:
    from chembl_compatibility import Activities
except ImportError:
    from chembl_core_model.models import Activities

#-----------------------------------------------------------------------------------------------------------------------


class BioactivitiesResource(ChEMBLApiBase):
    def __init__(self):
        self.parent_resource_name = None
        super(BioactivitiesResource, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^" + self.parent_resource_name + "/(?P<pk>\w[\w-]*)/bioactivities%s$" % (trailing_slash()),
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^" + self.parent_resource_name + "/(?P<pk>\w[\w-]*)/bioactivities\.(?P<format>\w+)%s$" % (
                trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def get_bundle(self, activities, isXML):
        ret = []

        for activity in activities.values('doc__journal', 'doc__year', 'doc__volume', 'doc__issue', 'doc__first_page',
                                          'molecule__moleculehierarchy__parent_molecule__chembl_id',
                                          'molecule__chembl_id', 'assay__target__chembl_id', 'assay__target__pref_name',
                                          'assay__target__organism', 'assay__confidence_score__confidence_score',
                                          'assay__assay_type__assay_type', 'assay__chembl_id', 'assay__description',
                                          'record__compound_key', 'standard_type', 'activity_comment',
                                          'standard_relation', 'standard_units', 'standard_value'):
            data = dict()

            reference = "Unspecified"
            if activity.get('doc__journal') and activity.get('doc__year') and activity.get('doc__volume') and \
               activity.get('doc__issue') and activity.get('doc__first_page'):
                reference = activity.get('doc__journal') + ", (" + str(activity.get('doc__year')) + ") " + \
                            activity.get('doc__volume') + ":" + activity.get('doc__issue') + ":" + \
                            activity.get('doc__first_page')

            data['reference'] = reference
            data['parent_cmpd_chemblid'] = activity.get('molecule__moleculehierarchy__parent_molecule__chembl_id')
            data['ingredient_cmpd_chemblid'] = activity.get('molecule__chembl_id')
            data['target_chemblid'] = activity.get('assay__target__chembl_id')
            data['target_name'] = activity.get('assay__target__pref_name') or "Unspecified"
            data['organism'] = activity.get('assay__target__organism') or "Unspecified"
            data['target_confidence'] = activity.get('assay__confidence_score__confidence_score') or "Unspecified"
            data['assay_type'] = activity.get('assay__assay_type__assay_type') or "Unspecified"
            data['assay_chemblid'] = activity.get('assay__chembl_id')
            data['assay_description'] = activity.get('assay__description') or "Unspecified"
            data['name_in_reference'] = activity.get('record__compound_key') or "Unspecified"
            data['bioactivity_type'] = activity.get('standard_type') or "Unspecified"
            data['activity_comment'] = activity.get('activity_comment') or "Unspecified"
            data['operator'] = activity.get('standard_relation') or "Unspecified"
            data['units'] = activity.get('standard_units') or "Unspecified"
            data['value'] = str(activity.get('standard_value')) if activity.get('standard_value') else "Unspecified"

            if isXML:
                for key in data.keys():
                    data[key.replace('_', '__')] = data.pop(key)

            ret.append(data)

        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_list(self, request=None, **kwargs):
        """
        A version of ``obj_get_list`` that uses the cache as a means to get
        commonly-accessed data faster.
        """

        isXML = (self.determine_format(request) == 'application/xml')
        kwargs['isXML'] = isXML
        cache_key = self.generate_cache_key('list', **kwargs)
        get_failed = False
        in_cache = True

        try:
            obj_list = self._meta.cache.get(cache_key)
        except Exception:
            obj_list = None
            get_failed = True
            self.log.error('Caching get exception', exc_info=True, extra={'request': request,})

        if obj_list is None:
            in_cache = False
            obj_list = self.obj_get_list(request=request, **kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, obj_list)
                except Exception:
                    self.log.error('Caching set exception', exc_info=True, extra={'request': request,})

        return obj_list, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, request=None, **kwargs):
        if kwargs.get('pk', False):
            pk = kwargs['pk']
            if not validateChemblId(pk):
                raise BadRequest("Invalid Chembl Identifier supplied:%s" % pk)
            isXML = (self.determine_format(request) == 'application/xml')
            ret = self.get_bundle(self.getActivities(pk), isXML)
#            if not len(ret):
#                raise ObjectDoesNotExist("%s not found for identifier:%s" % (self._meta.resource_name.split('s_')[0].title(), pk))
            return ret
        else:
            return http.HttpNotFound()

#-----------------------------------------------------------------------------------------------------------------------

    def getActivities(self, pk):
        raise NotImplementedError

#-----------------------------------------------------------------------------------------------------------------------


class AssaysBioactivitiesResource(BioactivitiesResource):
    def __init__(self):
        super(AssaysBioactivitiesResource, self).__init__()
        self.parent_resource_name = AssaysResource._meta.resource_name

    def getActivities(self, pk):
        return Activities.objects.filter(assay__chembl_id=pk)

    class Meta:
        resource_name = 'assays_bioactivities'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer('bioactivity')
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------


class TargetsBioactivitiesResource(BioactivitiesResource):
    def __init__(self):
        super(TargetsBioactivitiesResource, self).__init__()
        self.parent_resource_name = TargetsResource._meta.resource_name

    def getActivities(self, pk):
        return Activities.objects.filter(assay__target__chembl_id=pk)

    class Meta:
        resource_name = 'targets_bioactivities'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer('bioactivity')
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------


class CompoundsBioactivitiesResource(BioactivitiesResource):
    def __init__(self):
        super(CompoundsBioactivitiesResource, self).__init__()
        self.parent_resource_name = CompoundsResource._meta.resource_name

    def getActivities(self, pk):
        return Activities.objects.filter(molecule__chembl_id=pk)

    class Meta:
        resource_name = 'compounds_bioactivities'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer('bioactivity')
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------