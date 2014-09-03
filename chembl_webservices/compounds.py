__author__ = 'mnowotka'

from django.conf import settings
from chembl_webservices.base import ChEMBLApiBase
from tastypie.utils import trailing_slash
from django.conf.urls import *
from django.core.exceptions import ObjectDoesNotExist
from tastypie.authorization import Authorization
from tastypie import http
from django.http import HttpResponse
import base64
import time
from collections import OrderedDict
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit.Chem import Draw
except ImportError:
    Chem = None
    Draw = None
    AllChem = None

try:
    from rdkit.Chem.Draw import DrawingOptions
except ImportError:
    DrawingOptions = None

try:
    import indigo
    import indigo_renderer
except ImportError:
    indigo = None
    indigo_renderer = None

from base import ChEMBLApiSerializer
from chembl_webservices.cache import ChemblCache

from tastypie.exceptions import BadRequest
from chembl_core_db.chemicalValidators import validateSmiles, validateChemblId, validateStandardInchiKey
from tastypie.utils.mime import build_content_type
from tastypie.exceptions import ImmediateHttpResponse
from django.db.utils import DatabaseError
from django.db import transaction
from django.db import connection

try:
    from chembl_compatibility.models import MoleculeDictionary
    from chembl_compatibility.models import CompoundMols
    from chembl_compatibility.models import MoleculeHierarchy
except ImportError:
    from chembl_core_model.models import MoleculeDictionary
    from chembl_core_model.models import CompoundMols
    from chembl_core_model.models import MoleculeHierarchy

try:
    DEFAULT_SYNONYM_SEPARATOR = settings.DEFAULT_COMPOUND_SEPARATOR
except AttributeError:
    DEFAULT_SYNONYM_SEPARATOR = ','

try:
    WS_DEBUG = settings.WS_DEBUG
except AttributeError:
    WS_DEBUG = False

#-----------------------------------------------------------------------------------------------------------------------


class CompoundsResource(ChEMBLApiBase):

#-----------------------------------------------------------------------------------------------------------------------

    class Meta:
        resource_name = 'compounds'
        authorization = Authorization()
        include_resource_uri = False
        paginator_class = None
        serializer = ChEMBLApiSerializer('compound')
        allowed_methods = ['get', 'post']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------

    def base_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/stdinchikey/(?P<stdinchikey>\w[\w-]*)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/stdinchikey/(?P<stdinchikey>\w[\w-]*)\.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/smiles/?(?P<smiles>[\S]*)\.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list'),
                name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/smiles/?(?P<smiles>[\S]*)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_list'),
                name="api_dispatch_list"),
            url(r"^(?P<resource_name>%s)/substructure/?(?P<smiles>[\S]*)\.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_sim'),
                name="api_get_substructure"),
            url(r"^(?P<resource_name>%s)/substructure/?(?P<smiles>[\S]*)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_sim'),
                name="api_get_substructure"),
            url(r"^(?P<resource_name>%s)/similarity/(?P<smiles>[\S]*)/(?P<simscore>\d+)\.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_sim'),
                name="api_get_similarity"),
            url(r"^(?P<resource_name>%s)/similarity/(?P<smiles>[\S]*)/(?P<simscore>\d+)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_sim'),
                name="api_get_similarity"),
            url(r"^(?P<resource_name>%s)/similarity.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_sim'),
                name="api_get_similarity"),
            url(r"^(?P<resource_name>%s)/similarity%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_sim'),
                name="api_get_similarity"),
            url(r"^(?P<resource_name>%s)/(?P<chemblid>\w[\w-]*)\.(?P<format>)%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<chemblid>\w[\w-]*)%s$" % (self._meta.resource_name, trailing_slash()),
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
            url(r"^(?P<resource_name>%s)/(?P<chemblid>\w[\w-]*)/image%s$" % (
                self._meta.resource_name, trailing_slash()), self.wrap_view('get_cached_image'),
                name="api_get_image"),
            url(r"^(?P<resource_name>%s)$" % self._meta.resource_name, self.wrap_view('dispatch_compounds'),
                name="api_dispatch_compounds"),
            url(r"^(?P<resource_name>%s)\.(?P<format>)$" % self._meta.resource_name,
                self.wrap_view('dispatch_compounds'), name="api_dispatch_compounds"),
        ]

#-----------------------------------------------------------------------------------------------------------------------

    def dispatch_compounds(self, request, **kwargs):
        if 'chemblid' in kwargs:
            return self.dispatch('detail', request, **kwargs)
        if 'smiles' in kwargs:
            return self.dispatch('list', request, **kwargs)
        if 'stdinchikey' in kwargs:
            return self.dispatch('detail', request, **kwargs)
        return http.HttpNotImplemented()

#-----------------------------------------------------------------------------------------------------------------------

    def dispatch_sim(self, request, **kwargs):
        self.method_check(request, allowed=['get', 'post'])
        #self.is_authenticated(request)
        #self.throttle_check(request)
        #self.log_throttled_access(request)

        start = time.time()
        if 'simscore' in kwargs:
            ret, in_cache = self.get_similarity(request, **kwargs)
        else:
            ret, in_cache = self.get_substructure(request, **kwargs)
        end = time.time()

        res = self.create_response(request, ret)

        if WS_DEBUG:
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start

        return res

#-----------------------------------------------------------------------------------------------------------------------

    def get_bundle(self, molecules, explode=False, sim=False, synonymSeparator=DEFAULT_SYNONYM_SEPARATOR):

        name = molecules.model.__name__
        prefix = 'molecule__' if name is 'CompoundMols' else ''

        field_items = [
                  ('chembl_id', 'chemblId'),
                  ('pref_name', 'preferredCompoundName'),
                  ('max_phase', 'knownDrug'),
                  ('compoundproperties__med_chem_friendly', 'medChemFriendly'),
                  ('compoundproperties__ro3_pass', 'passesRuleOfThree'),
                  ('compoundproperties__full_molformula', 'molecularFormula'),
                  ('compoundstructures__canonical_smiles', 'smiles'),
                  ('compoundstructures__standard_inchi_key', 'stdInChiKey'),
                  ('compoundproperties__molecular_species', 'species'),
                  ('compoundproperties__num_ro5_violations', 'numRo5Violations'),
                  ('compoundproperties__rtb', 'rotatableBonds'),
                  ('compoundproperties__mw_freebase', 'molecularWeight'),
                  ('compoundproperties__alogp', 'alogp'),
                  ('compoundproperties__acd_logp', 'acdLogp'),
                  ('compoundproperties__acd_logd', 'acdLogd'),
                  ('compoundproperties__acd_most_apka', 'acdAcidicPka'),
                  ('compoundproperties__acd_most_bpka', 'acdBasicPka')]

        fields = dict((prefix + key, value) for key, value in field_items)

        if prefix and sim:
            fields['similarity'] = 'similarity'

        if connection.vendor == 'postgresql':
            transaction.commit_unless_managed()
            transaction.enter_transaction_management()
            transaction.managed(True)

        mols = molecules.exclude(**{prefix + 'downgraded' : True})
        try:
            ret = self.get_vals(mols, fields)

        except DatabaseError:
            if connection.vendor == 'postgresql':
                transaction.rollback()
            mols = molecules
            ret = self.get_vals(mols, fields)

        if connection.vendor == 'postgresql':
            transaction.commit()
            transaction.leave_transaction_management()


        syn_fields = map(lambda x: prefix + x, ['chembl_id', 'moleculesynonyms__synonyms'])

        if prefix and sim and connection.vendor == 'postgresql': #TODO: try to remove this hack, check if latest django version can cope without it
            syn_fields.append('similarity')

        vals = mols.values_list(*syn_fields).distinct()

        if vals and len(vals[0]) > 2: #TODO: try to remove this hack, check if latest django version can cope without it
            vals = map(lambda x : x[:2], vals)

        for chemblid, synonym in vals:
            if synonym:
                r = ret[chemblid]
                if 'synonyms' in ret[chemblid]:
                    r['synonyms'].append(synonym)
                else:
                    r['synonyms'] = [synonym]

        ret = ret.values()
        for r in ret:
            syn = r.get('synonyms', [])
            r['synonyms'] = syn if explode else synonymSeparator.join(syn)
            if not r['synonyms']:
                r['synonyms'] = None
            r['knownDrug'] = 'Yes' if r['knownDrug'] == 4 else 'No'
            r['medChemFriendly'] = 'Yes' if r['medChemFriendly'] == 'Y' else 'No'
            r['passesRuleOfThree'] = 'Yes' if r['passesRuleOfThree'] == 'Y' else 'No'

        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get(self, request=None, **kwargs):
        explode = 'explode_synonyms' in kwargs
        synonymSeparator = kwargs.get('synonymseparator', DEFAULT_SYNONYM_SEPARATOR)
        mols = MoleculeDictionary.objects.only('pk', 'chembl', 'pref_name', 'max_phase', 'compoundproperties')
        if kwargs.get('chemblid', False):
            chemblid = kwargs['chemblid']
            if not validateChemblId(chemblid):
                raise BadRequest("Invalid Chembl Identifier supplied:%s" % chemblid)
            ret = self.get_bundle(
                mols.filter(
                    chembl_id=chemblid), explode, synonymSeparator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Compound not found for identifier:%s" % chemblid)
        elif kwargs.get('stdinchikey', False):
            key = kwargs['stdinchikey']
            if not validateStandardInchiKey(key):
                raise BadRequest("Invalid Standard InChi Key supplied:%s" % key)
            ret = self.get_bundle(
                mols.filter(
                    compoundstructures__standard_inchi_key=key), explode, synonymSeparator=synonymSeparator)
            if not len(ret):
                return http.HttpNotFound("Compound not found for identifier:%s" % key)
        else:
            return http.HttpNotFound()
        return ret[0]

#-----------------------------------------------------------------------------------------------------------------------

    def obj_get_list(self, request=None, **kwargs):

        explode = 'explode_synonyms' in kwargs
        smiles = kwargs.get('smiles', False)
        synonymSeparator = kwargs.get('synonymseparator', DEFAULT_SYNONYM_SEPARATOR)
        if not validateSmiles(smiles):
            raise BadRequest("Invalid SMILES supplied:%s" % smiles)

        if smiles:
            ctabs = CompoundMols.objects.flexmatch(smiles)
            return self.get_bundle(ctabs, explode, synonymSeparator=synonymSeparator)
        else:
            return http.HttpNotFound()

#-----------------------------------------------------------------------------------------------------------------------

    def post_list(self, request, **kwargs):
        """
        Creates a new resource/object with the provided data.

        Calls ``obj_create`` with the provided data and returns a response
        with the new resource's location.

        If a new resource is created, return ``HttpCreated`` (201 Created).
        If ``Meta.always_return_data = True``, there will be a populated body
        of serialized data.
        """

        if request.META['CONTENT_TYPE'].startswith(('multipart/form-data', 'multipart/form-data')):
            args = request.POST.dict()
        else:
            args = self.deserialize(request, request.body, format=request.META.get('CONTENT_TYPE', 'application/json'))
        kvargs = kwargs.copy()
        kvargs.update(args)
        return self.get_list(request, **kvargs)

#-----------------------------------------------------------------------------------------------------------------------

    def get_vals(self, objects, fields2attrs):
        ret = OrderedDict()
        for object in objects.values_list(*fields2attrs.keys()):
            data = dict()
            chemblid = None
            for idx, field in enumerate(fields2attrs):
                attr = fields2attrs[field]
                data[attr] = object[idx]
                if attr == 'chemblId':
                    chemblid = object[idx]
            ret[chemblid] = data
        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def get_cached_image(self, request, **kwargs):

        chemblid = kwargs.get('chemblid', '')
        in_cache = True
        if not validateChemblId(chemblid):
            raise BadRequest("Invalid Chembl Identifier supplied:%s" % chemblid)

        size = int(kwargs.get("dimensions", 500))
        engine = kwargs.get("engine", 'rdkit')
        engine = engine.lower()
        ignoreCoords = kwargs.get("ignoreCoords", False)

        if size < 1 or size > 500:
            return self.answerBadRequest(request, "Image dimensions supplied are invalid, max value is 500")

        argDict = {"chemblid": chemblid, "size": size, "engine": engine, "ignoreCoords": ignoreCoords}

        cache_key = self.generate_cache_key('image', **argDict)
        get_failed = False

        start = time.time()
        try:
            ret = self._meta.cache.get(cache_key)
        except Exception:
            ret = None
            get_failed = True
            self.log.error('Cashing get exception', exc_info=True, extra=argDict)

        if ret is None:
            in_cache = False
            ret = self.get_image(request, **kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, ret)
                except Exception:
                    self.log.error('Cashing set exception', exc_info=True, extra=argDict)
        end = time.time()

        if request.is_ajax():
            ret.content = base64.b64encode(ret.content)
        if WS_DEBUG:
            ret['X-ChEMBL-in-cache'] = in_cache
            ret['X-ChEMBL-retrieval-time'] = end - start
        return ret

#-----------------------------------------------------------------------------------------------------------------------

    def get_image(self, request, **kwargs):

        try:
            if kwargs.get('chemblid', False):
                chemblid = kwargs['chemblid']
                if not validateChemblId(chemblid):
                    raise BadRequest("Invalid Chembl Identifier supplied:%s" % chemblid)
                try:
                    molfile = MoleculeDictionary.objects.filter(chembl_id=chemblid).values_list(
                                                                                "compoundstructures__molfile")[0][0]
                except IndexError:
                    return http.HttpNotFound()
            else:
                return http.HttpNotFound()
        except ObjectDoesNotExist:
            return http.HttpNotFound()

        size = int(kwargs.get("dimensions", 500))
        engine = kwargs.get("engine", 'rdkit')
        engine = engine.lower()
        ignoreCoords = kwargs.get("ignoreCoords", False)

        if size < 1 or size > 500:
            return self.answerBadRequest(request, "Image dimensions supplied are invalid, max value is 500")

        response = HttpResponse(mimetype="image/png")

        if engine == 'rdkit':
            fontSize = int(size / 33)
            if size < 200:
                fontSize = 1
            mol = Chem.MolFromMolBlock(str(molfile))
            if ignoreCoords:
                AllChem.Compute2DCoords(mol)

            if DrawingOptions:
                options = DrawingOptions()
                options.useFraction = 1.0
                options.dblBondOffset = .13
                options.atomLabelFontSize = fontSize
            else:
                options={"useFraction": 1.0,
                         "dblBondOffset": .13,
                         'atomLabelFontSize': fontSize,}
            image = Draw.MolToImage(mol, size=(size, size), fitImage=True, options=options)
            image.save(response, "PNG")

        elif engine == 'indigo':
            indigoObj = indigo.Indigo()
            renderer = indigo_renderer.IndigoRenderer(indigoObj)
            indigoObj.setOption("render-output-format", "png")
            indigoObj.setOption("render-margins", 10, 10)
            indigoObj.setOption("render-image-size", size, size)
            indigoObj.setOption("render-coloring", True)
            indigoObj.setOption("ignore-stereochemistry-errors", "true")
            mol = indigoObj.loadMolecule(str(molfile))
            if ignoreCoords:
                mol.layout()
            image = renderer.renderToBuffer(mol)
            response.write(image.tostring())
        else:
            return self.answerBadRequest(request, "Unsupported engine %s" % engine)

        return response

#-----------------------------------------------------------------------------------------------------------------------

    def get_substructure(self, request, **kwargs):

        smiles = kwargs.get('smiles', None)

        if not validateSmiles(smiles):
            return self.answerBadRequest(request, "Invalid SMILES supplied:%s" % smiles)
        if len(smiles) < 6:
            return self.answerBadRequest(request,
                "SMILES too short (sequence of length 6 or more is required for substructure search): %s" % smiles)

        return self.get_cached_method('substructure', **kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def get_similarity(self, request, **kwargs):

        smiles = kwargs.get('smiles', None)
        simscore = kwargs.get('simscore', None)

        if not validateSmiles(smiles):
            return self.answerBadRequest(request, "Invalid SMILES supplied:%s" % smiles)
        if int(simscore) < 70 or int(simscore) > 100:
            return self.answerBadRequest(request, "Invalid Similarity Score supplied:%s" % simscore)

        return self.get_cached_method('similarity', **kwargs)

#-----------------------------------------------------------------------------------------------------------------------

    def get_cached_method(self, name, **kwargs):

        explode = 'explode_synonyms' in kwargs
        smiles = kwargs.get('smiles', None)
        simscore = kwargs.get('simscore', None)
        synonymSeparator = kwargs.get('synonymseparator', DEFAULT_SYNONYM_SEPARATOR)
        argDict = {'explode':explode, 'smiles':smiles, 'simscore':simscore, 'synonymSeparator':synonymSeparator}

        cache_key = self.generate_cache_key(name, **argDict)
        get_failed = False
        in_cache = True

        try:
            ret = self._meta.cache.get(cache_key)
        except Exception:
            ret = None
            get_failed = True
            self.log.error('Cashing get exception', exc_info=True, extra=argDict)

        if ret is None:
            filters = {
                'molecule__chembl__entity_type':'COMPOUND',
                'molecule__compoundstructures__isnull' : False,
                'pk__in' : MoleculeHierarchy.objects.all().values_list('parent_molecule_id'),
                'molecule__compoundproperties__isnull' : False,
            }
            in_cache = False
            method = getattr(self, name, None)
            kwargs['obj'] = CompoundMols.objects
            ctabs = method(**kwargs).filter(**filters)

            ret = self.get_bundle(ctabs, explode, simscore, synonymSeparator=synonymSeparator)

            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, ret)
                except Exception:
                    self.log.error('Cashing set exception', exc_info=True, extra=argDict)

        return ret, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def similarity(self, **kwargs):
        return kwargs['obj'].similar_to(kwargs['smiles'], kwargs['simscore'])

#-----------------------------------------------------------------------------------------------------------------------

    def substructure(self, **kwargs):
        return kwargs['obj'].with_substructure(kwargs['smiles'])

#-----------------------------------------------------------------------------------------------------------------------

    def answerBadRequest(self, request, error):
        response_class = http.HttpBadRequest
        desired_format = self.determine_format(request)
        data = {'exception': error}
        serialized = self.serialize(request, data, desired_format)
        raise ImmediateHttpResponse(response=response_class(content=serialized,
                                                    content_type=build_content_type(desired_format)))

#-----------------------------------------------------------------------------------------------------------------------
