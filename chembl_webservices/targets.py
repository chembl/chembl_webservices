__author__ = 'mnowotka'

from django.conf import settings
from django.core.exceptions import FieldError
from base import ChEMBLApiBase
from tastypie.utils import trailing_slash
from django.conf.urls import *
from django.db.models import Count
from tastypie import http
from tastypie.authorization import Authorization
from chembl_webservices.base import ChEMBLApiSerializer
from tastypie.exceptions import BadRequest
from chembl_core_db.chemicalValidators import validateChemblId, validateUniprot, validateRefseq
from chembl_webservices.cache import ChemblCache
from collections import OrderedDict

try:
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import TargetDictionary

try:
    DEFAULT_SYNONYM_SEPARATOR = settings.DEFAULT_TARGET_SEPARATOR
except AttributeError:
    DEFAULT_SYNONYM_SEPARATOR = ','

class TargetsResource(ChEMBLApiBase):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta:
        resource_name = 'targets'
        authorization = Authorization()
        include_resource_uri = False
        paginator_class = None
        serializer = ChEMBLApiSerializer('target')
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)\.(?P<format>\w+)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w-]*)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w-]*)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/uniprot_all/(?P<uniprot>\w[\w-]*)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/uniprot_all/(?P<uniprot>\w[\w-]*)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/uniprot/(?P<uniprot>\w[\w-]*)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                                                                                            name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/uniprot/(?P<uniprot>\w[\w-]*)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                                                                                            name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/refseq/(?P<refseq>\w[\w-]*)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/refseq/(?P<refseq>\w[\w-]*)\.(?P<format>\w+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def get_bundle(self, targets, separator=DEFAULT_SYNONYM_SEPARATOR):

        ret = OrderedDict()
        try:
            good_targets = targets.filter(in_starlite=True)
        except FieldError:
            good_targets = targets

        for tid, chemblid, pref_name, target_type, organism, compound_count, activity_count in \
            good_targets.annotate(compoundCount=Count('assays__moleculedictionary', distinct=True),
                bioactivityCount=Count('assays__activities')).values_list('tid', 'chembl__chembl_id', 'pref_name',
                'target_type__target_type','organism', 'compoundCount', 'bioactivityCount').order_by('-compoundCount'):

            data = dict()
            data['chemblId'] = chemblid
            data['preferredName'] = pref_name
            data['description'] = pref_name
            data['targetType'] = target_type
            data['organism'] = organism
            data['compoundCount'] = compound_count
            data['bioactivityCount'] = activity_count
            data['geneNames'] = 'Unspecified' # TODO: resolve it somehow
            ret[tid] = data

        for tid, synonym in good_targets.values_list('tid',
                                            'component_sequences__componentsynonyms__component_synonym').distinct():
            if synonym:
                if 'synonyms' in ret[tid]:
                    ret[tid]['synonyms'] += (separator + synonym)
                else:
                    ret[tid]['synonyms'] = synonym

        for tid, accession in good_targets.values_list('tid', 'component_sequences__accession').distinct():
            if accession:
                if 'proteinAccession' in ret[tid]:
                    ret[tid]['proteinAccession'] += (separator + accession)
                else:
                    ret[tid]['proteinAccession'] = accession

        return ret.values()

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, request=None, **kwargs):
        synonymSeparator = kwargs.get('synonymseparator', DEFAULT_SYNONYM_SEPARATOR)
        if kwargs.get('pk', False):
            pk = kwargs['pk']
            if not validateChemblId(pk):
                raise BadRequest("Invalid Chembl Identifier supplied:%s" % pk)
            ret = self.get_bundle(TargetDictionary.objects.filter(chembl_id=pk), separator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Target not found for identifier:%s" % pk)
            return ret[0]
        elif kwargs.get('uniprot', False):
            uniprot = kwargs['uniprot']
            if not validateUniprot(uniprot):
                raise BadRequest("Invalid UniProt Identifier supplied:%s" % uniprot)
            ret = self.get_bundle(TargetDictionary.objects.filter(component_sequences__accession=uniprot),
                                                                                            separator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Target not found for accession:%s" % uniprot)
            return ret[0]
        else:
            return http.HttpNotFound()

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, request=None, **kwargs):
        synonymSeparator = kwargs.get('synonymseparator', DEFAULT_SYNONYM_SEPARATOR)

        if kwargs.get('uniprot', False):
            uniprot = kwargs['uniprot']
            if not validateUniprot(uniprot):
                raise BadRequest("Invalid UniProt Identifier supplied:%s" % uniprot)
            ret = self.get_bundle(TargetDictionary.objects.filter(component_sequences__accession=uniprot),
                                                                                            separator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Target not found for accession:%s" % uniprot)

        elif kwargs.get('refseq', False):
            refseq = kwargs['refseq']
            if not validateRefseq(refseq):
                raise BadRequest("Invalid RefSeq Identifier supplied:%s" % refseq)
            ret = self.get_bundle(TargetDictionary.objects.filter(component_sequences__accession=refseq),
                                                                                            separator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Target not found for accession:%s" % refseq)
        else:
            ret = self.get_bundle(TargetDictionary.objects.all(), separator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("No targets in database")

        return ret

#-----------------------------------------------------------------------------------------------------------------------