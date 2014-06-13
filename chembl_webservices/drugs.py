__author__ = 'mnowotka'

from django.db.utils import DatabaseError
from django.db import transaction
from django.db import connection
from django.core.exceptions import FieldError
from chembl_webservices.compounds import CompoundsResource
from chembl_webservices.targets import TargetsResource
from chembl_webservices.base import ChEMBLApiSerializer
from tastypie.authorization import Authorization
from chembl_webservices.cache import ChemblCache
from chembl_webservices.derivativeResource import DerivativeResource

try:
    from chembl_compatibility.models import MoleculeDictionary
    from chembl_compatibility.models import CompoundMols
    from chembl_compatibility.models import MoleculeHierarchy
    from chembl_compatibility.models import TargetDictionary
except ImportError:
    from chembl_core_model.models import MoleculeDictionary
    from chembl_core_model.models import CompoundMols
    from chembl_core_model.models import MoleculeHierarchy
    from chembl_core_model.models import TargetDictionary

#-----------------------------------------------------------------------------------------------------------------------

class CompoundDerivativeResource(DerivativeResource):
    def __init__(self):
        super(CompoundDerivativeResource, self).__init__()
        self.downgraded_missing = False

    def getCoreResources(self, pk):
        if self.downgraded_missing:
            return MoleculeDictionary.objects.filter(chembl_id=pk)
        else:

            if connection.vendor == 'postgresql':
                transaction.commit_unless_managed()
                transaction.enter_transaction_management()
                transaction.managed(True)

            try:
                MoleculeDictionary.objects.filter(chembl_id=pk, downgraded=False).exists()
            except DatabaseError:
                if connection.vendor == 'postgresql':
                    transaction.rollback()
                self.downgraded_missing = True

            if connection.vendor == 'postgresql':
                transaction.commit()
                transaction.leave_transaction_management()

        if self.downgraded_missing:
            return MoleculeDictionary.objects.filter(chembl_id=pk)
        else:
            return MoleculeDictionary.objects.filter(chembl_id=pk, downgraded=False)

#-----------------------------------------------------------------------------------------------------------------------

class CompoundMechanismsOfAction(CompoundDerivativeResource):
    def __init__(self):
        super(CompoundMechanismsOfAction, self).__init__()
        self.parent_resource_name = CompoundsResource._meta.resource_name

    def get_bundle(self, objs):
        ret = []
        mechanism_fileds = ['chembl_id', 'drugmechanism__mechanism_of_action',
                                                'drugmechanism__target__chembl_id', 'drugmechanism__target__pref_name']
        mechs = objs.values_list(*mechanism_fileds)
        for chemblid, mechanism_of_action, target_chemblid, target_name in mechs:
            if mechanism_of_action and target_chemblid and target_name:
                m = {'mechanismOfAction': mechanism_of_action, 'chemblId' : target_chemblid, 'name': target_name}
                ret.append(m)
        return ret

    class Meta:
        resource_name = 'drugMechanism'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer(resource_name)
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------

class TargetApprovedDrugs(DerivativeResource):
    def __init__(self):
        super(TargetApprovedDrugs, self).__init__()
        self.parent_resource_name = TargetsResource._meta.resource_name

    def getCoreResources(self, pk):
        try:
            return TargetDictionary.objects.filter(chembl_id=pk, in_starlite=True)
        except FieldError:
            return TargetDictionary.objects.filter(chembl_id=pk)

    def get_bundle(self, objs):
        ret = []
        for tid, mechanism_of_action, pref_name, chemblid in objs.values_list('tid',
            'drugmechanism__mechanism_of_action', 'drugmechanism__molecule__pref_name',
            'drugmechanism__molecule__chembl_id'):
            if mechanism_of_action and pref_name:
                drug = {'chemblId':chemblid, 'name': pref_name, 'mechanismOfAction': mechanism_of_action}
                ret.append(drug)
        return ret

    class Meta:
        resource_name = 'approvedDrug'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer(resource_name)
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------

class CompoundForms(CompoundDerivativeResource):
    def __init__(self):
        super(CompoundForms, self).__init__()
        self.parent_resource_name = CompoundsResource._meta.resource_name

    def get_bundle(self, objs):
        if not objs.exists():
            return []
        forms = set()
        has_parent, parent_chemblID = objs.values_list("moleculehierarchy__parent_molecule",
                                                                "moleculehierarchy__parent_molecule__chembl_id")[0]
        if has_parent:
            parent = has_parent
        else:
            parent, parent_chemblID = objs.values_list('pk', 'chembl_id')[0]
        forms.add(parent_chemblID)

        if not self.downgraded_missing:
            forms.update(MoleculeDictionary.objects.filter(downgraded=False,
                                    moleculehierarchy__parent_molecule=parent).values_list("chembl_id", flat=True))
        else:
            forms.update(MoleculeDictionary.objects.filter(
                                    moleculehierarchy__parent_molecule=parent).values_list("chembl_id", flat=True))

        return map(lambda chemblid: {'chemblId':chemblid, 'parent': False if chemblid != parent_chemblID else True},
                                                                                                                forms)

    class Meta:
        resource_name = 'form'
        authorization = Authorization()
        include_resource_uri = False
        serializer = ChEMBLApiSerializer(resource_name)
        paginator_class = None
        allowed_methods = ['get']
        default_format = 'application/xml'
        cache = ChemblCache()

#-----------------------------------------------------------------------------------------------------------------------