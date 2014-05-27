__author__ = 'mnowotka'

try:
    __version__ = __import__('pkg_resources').get_distribution('chembl_webservices').version
except Exception as e:
    __version__ = 'development'

from chembl_webservices.base import ChEMBLApi
from chembl_webservices.status import *
from chembl_webservices.compounds import *
from chembl_webservices.assays import *
from chembl_webservices.targets import *
from chembl_webservices.bioactivities import *
from chembl_webservices.drugs import *
from django.conf import settings

DEFAULT_API_NAME='chemblws'

try:
    api_name = settings.WEBSERVICES_NAME
except AttributeError:
    api_name = DEFAULT_API_NAME

api = ChEMBLApi(api_name=api_name)

api.register(StatusResource())
api.register(CompoundsResource())
api.register(AssaysResource())
api.register(TargetsResource())
api.register(AssaysBioactivitiesResource())
api.register(CompoundsBioactivitiesResource())
api.register(TargetsBioactivitiesResource())
api.register(TargetApprovedDrugs())
api.register(CompoundMechanismsOfAction())
api.register(CompoundForms())

