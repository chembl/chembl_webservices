__author__ = 'mnowotka'

from chembl_webservices import api
from chembl_core_db.testing.tastypieTest import ResourceTestCase, TestApiClient
from chembl_webservices.base import ChEMBLApiSerializer
from chembl_webservices.compounds import DEFAULT_SYNONYM_SEPARATOR as DEFAULT_COMPOUND_SEPARATOR
from chembl_webservices.targets import DEFAULT_SYNONYM_SEPARATOR as DEFAULT_TARGET_SEPARATOR

class EntryResourceTest(ResourceTestCase):
    # Use ``fixtures`` & ``urls`` as normal. See Django's ``TestCase``
    # documentation for the gory details.
    fixtures = ['test_entries.json']

#-----------------------------------------------------------------------------------------------------------------------

    def setUp(self):
        super(EntryResourceTest, self).setUp()
        self.serializer = ChEMBLApiSerializer()
        self.api_client = TestApiClient(self.serializer)
        self.apiPath = "/chembl_webservices/" + api.api_name

#-----------------------------------------------------------------------------------------------------------------------

    def deserialize(self, resp, format=None, tag=None):
        form = format
        if not form:
            form = resp['Content-Type']

        return self.serializer.deserialize(resp.content, format=form, tag=tag)

#-----------------------------------------------------------------------------------------------------------------------

    def test_status(self):

        url = self.apiPath + '/status/'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        self.assertEquals(self.deserialize(resp, format='application/xml', tag='service')['status'], 'UP')
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        self.assertEquals(self.deserialize(resp, format='application/json')['service']['status'], 'UP')
        url = self.apiPath + '/status.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        self.assertEquals(self.deserialize(resp, format='application/json')['service']['status'], 'UP')
        url = self.apiPath + '/status.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        self.assertEquals(self.deserialize(resp, format='application/xml', tag='service')['status'], 'UP')

#-----------------------------------------------------------------------------------------------------------------------

    def test_compounds(self):

        url = self.apiPath + '/compounds/CHEMBL1'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        url = self.apiPath + '/compounds/CHEMBL1.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        url = self.apiPath + '/compounds/CHEMBL1.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/compounds/CHEMBL1'
        resp = self.api_client.get(url, format='json')
        compound = self.deserialize(resp, format='application/json')['compound']
        self.assertEquals(compound['smiles'],
                    'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56')
        self.assertEquals(compound['chemblId'], 'CHEMBL1')
        self.assertEquals(compound['medChemFriendly'], 'Yes')
        self.assertEquals(compound['molecularWeight'], 544.59)
        self.assertEquals(compound['molecularFormula'], 'C32H32O8')
        self.assertEquals(compound['acdLogp'], 7.67)
        empty = False
        try:
            compound['synonyms']
        except KeyError:
            empty = True
        self.assertTrue(empty)
        self.assertEquals(compound['stdInChiKey'], 'GHBOEFUAGSHXPO-XZOTUCIWSA-N')
        self.assertEquals(compound['knownDrug'], 'No')
        self.assertEquals(compound['passesRuleOfThree'], 'No')
        self.assertEquals(compound['rotatableBonds'], 2)

        empty = False
        try:
            compound['acdAcidicPka']
        except KeyError:
            empty = True
        self.assertTrue(empty)

        self.assertEquals(compound['alogp'], 3.63)
        self.assertEquals(compound['acdLogd'], 7.67)

        url = self.apiPath + '/compounds/CHEMBLX'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL1642'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/compounds/CHEMBL1000000000'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

        url = self.apiPath + '/compounds/CHEMBL1235452'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

        url = self.apiPath + '/compounds/stdinchikey/QFFGVLORLPOAEC-SNVBAGLBSA-N'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compound = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(compound['chemblId'], 'CHEMBL1201760')
        self.assertEquals(compound['preferredCompoundName'], 'BESIFLOXACIN')
        self.assertEquals(compound['synonyms'], 'Besifloxacin')
        self.assertEquals(compound['knownDrug'], 'Yes')
        self.assertEquals(compound['medChemFriendly'], 'No')
        self.assertEquals(compound['passesRuleOfThree'], 'No')
        self.assertEquals(compound['molecularFormula'], 'C19H21ClFN3O3')
        self.assertEquals(compound['smiles'], 'N[C@@H]1CCCCN(C1)c2c(F)cc3C(=O)C(=CN(C4CC4)c3c2Cl)C(=O)O')
        self.assertEquals(compound['stdInChiKey'], 'QFFGVLORLPOAEC-SNVBAGLBSA-N')
        self.assertEquals(compound['species'], 'ZWITTERION')
        self.assertEquals(compound['numRo5Violations'], '0')
        self.assertEquals(compound['rotatableBonds'], '3')
        self.assertEquals(compound['molecularWeight'], '393.84')
        self.assertEquals(compound['alogp'], '0.32')
        self.assertEquals(compound['acdAcidicPka'], '6.41')
        self.assertEquals(compound['acdBasicPka'], '10.22')
        self.assertEquals(compound['acdLogp'], '3.40')
        self.assertEquals(compound['acdLogd'], '0.90')

        url = self.apiPath + '/compounds/stdinchikey/QFFGVLORLPOAEC-'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/stdinchikey/QFFGVLORLPOAEK-SNVBAGLBSA-N'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc9cc(OC)ccc9[C@H]56'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles/Nc1cccc2C(=O)N(C3CCC(=O)NC3=O)C(=O)c12'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 3)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        compound = compounds[1]
        self.assertEquals(compound['chemblId'], 'CHEMBL1')
        self.assertEquals(compound['knownDrug'], 'No')
        self.assertEquals(compound['medChemFriendly'], 'Yes')
        self.assertEquals(compound['passesRuleOfThree'], 'No')
        self.assertEquals(compound['molecularFormula'], 'C32H32O8')
        self.assertEquals(compound['smiles'], 'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56')
        self.assertEquals(compound['stdInChiKey'], 'GHBOEFUAGSHXPO-XZOTUCIWSA-N')
        self.assertEquals(compound['numRo5Violations'], '1')
        self.assertEquals(compound['rotatableBonds'], '2')
        self.assertEquals(compound['molecularWeight'], '544.59')
        self.assertEquals(compound['alogp'], '3.63')
        self.assertEquals(compound['acdLogp'], '7.67')
        self.assertEquals(compound['acdLogd'], '7.67')

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/smiles/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC=C3C(=O)C(=O)C'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 0)

        url = self.apiPath + '/compounds/smiles/xxxxx'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/smiles.json'
        resp = self.api_client.post(url, format='html',
            data={'smiles':
                      'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 2)
        compound = compounds[1]
        self.assertEquals(compound['chemblId'], 'CHEMBL1')
        self.assertEquals(compound['knownDrug'], 'No')
        self.assertEquals(compound['medChemFriendly'], 'Yes')
        self.assertEquals(compound['passesRuleOfThree'], 'No')
        self.assertEquals(compound['molecularFormula'], 'C32H32O8')
        self.assertEquals(compound['smiles'],
            'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56')
        self.assertEquals(compound['stdInChiKey'], 'GHBOEFUAGSHXPO-XZOTUCIWSA-N')
        self.assertEquals(compound['numRo5Violations'], 1)
        self.assertEquals(compound['rotatableBonds'], 2)
        self.assertEquals(compound['molecularWeight'], 544.59)
        self.assertEquals(compound['alogp'], 3.63)
        self.assertEquals(compound['acdLogp'], 7.67)
        self.assertEquals(compound['acdLogd'], 7.67)

        url = self.apiPath + '/compounds/smiles.xml'
        resp = self.api_client.post(url, format='html',
            data={'smiles':
                      'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles'
        resp = self.api_client.post(url, format='html',
            data={'smiles':
                      'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles'
        resp = self.api_client.post(url, format='xml',
            data={'smiles':
                      'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds/smiles'
        resp = self.api_client.post(url, format='json',
            data={'smiles':
                      'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 2)

#-----------------------------------------------------------------------------------------------------------------------

    def test_substructure(self):

        url = self.apiPath + '/compounds/substructure/CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure/CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure/CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure/CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure/CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure.json'
        resp = self.api_client.post(url, format='html',
            data={'smiles':'CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure.xml'
        resp = self.api_client.post(url, format='html',
            data={'smiles':'CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure'
        resp = self.api_client.post(url, format='html',
            data={'smiles':'CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure'
        resp = self.api_client.post(url, format='json',
            data={'smiles':'CCCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4'})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 28)

        url = self.apiPath + '/compounds/substructure/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 0)

#-----------------------------------------------------------------------------------------------------------------------


    def test_similarity(self):

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/95'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/95'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        for compound in compounds:
            self.assertTrue(95 <= compound['similarity'] <= 100)
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/95'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/95.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/95.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity.json'
        resp = self.api_client.post(url, format='html', data={'smiles':'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 'simscore': 95})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity.xml'
        resp = self.api_client.post(url, format='html', data={'smiles':'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 'simscore': 95})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity'
        resp = self.api_client.post(url, format='html', data={'smiles':'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 'simscore': 95})
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity'
        resp = self.api_client.post(url, format='json', data={'smiles':'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 'simscore': 95})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity'
        resp = self.api_client.post(url, format='json', content_type='json', data={'smiles':'COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56', 'simscore': 95})
        self.assertValidJSONResponse(resp, url)
        compounds = self.deserialize(resp, format='application/json')['compounds']
        self.assertEquals(len(compounds), 9)

        url = self.apiPath + '/compounds/similarity/CCc1nn(C)c2C(=O)NC(=Nc12)c3cc(ccc3OCC)S(=O)(=O)N4CCN(C)CC4/100'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 0)

        url = self.apiPath + '/compounds/similarity/CCc1nn(C)c2C(=O)NC(=Nc12)c3cc(/100'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/69'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/101'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/similarity/COc1ccc2[C@@H]3[C@H](COc2c1)C(C)(C)OC4=C3C(=O)C(=O)C5=C4OC(C)(C)[C@@H]6COc7cc(OC)ccc7[C@H]56/bla'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_image(self):

        url = self.apiPath + '/compounds/CHEMBL192/image'
        resp = self.api_client.get(url, format='html')
        self.assertHttpOK(resp)
        self.assertEquals(resp['Content-Type'], 'image/png')

        url = self.apiPath + '/compounds/CHEMBL192/image?dimensions=200'
        resp = self.api_client.get(url, format='html')
        self.assertHttpOK(resp)
        self.assertEquals(resp['Content-Type'], 'image/png')

        url = self.apiPath + '/compounds/CHEMBL192/image?dimensions=0'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL192/image?dimensions=550'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBLX/image'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL10000000000/image'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_compound_bioactivities(self):

        url = self.apiPath + '/compounds/CHEMBL2/bioactivities'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 900)

        url = self.apiPath + '/compounds/CHEMBL2/bioactivities'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 900)

        url = self.apiPath + '/compounds/CHEMBL2/bioactivities.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 900)

        url = self.apiPath + '/compounds/CHEMBL2/bioactivities.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertTrue(len(bioactivities) > 900)

        url = self.apiPath + '/compounds/CHEMBL2/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertTrue(len(bioactivities) > 900)

        url = self.apiPath + '/compounds/CHEMBL101/bioactivities.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/compounds/CHEMBLX/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL10000000000/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertEquals(len(bioactivities), 0)

#-----------------------------------------------------------------------------------------------------------------------

    def test_targets(self):

        url = self.apiPath + '/targets/CHEMBL2477'
        resp = self.api_client.get(url, format='xml')
        self.assertHttpNotFound(resp)

        url = self.apiPath + '/targets/CHEMBL2478'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/CHEMBL2478'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/CHEMBL2478.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/CHEMBL2478.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/targets/CHEMBL2478'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/targets/CHEMBL2478'
        resp = self.api_client.get(url, format='json')
        target = self.deserialize(resp, format='application/json')['target']
        self.assertEquals(target['chemblId'], 'CHEMBL2478')
        self.assertEquals(target['targetType'], 'SINGLE PROTEIN')
        self.assertEquals(target['preferredName'], 'Salivary alpha-amylase')
        self.assertEquals(target['proteinAccession'], 'P04745')
        self.assertEquals(set(target['synonyms'].split(DEFAULT_TARGET_SEPARATOR)), set(['Salivary alpha-amylase',
'andAMY1','Alpha-amylase 1','AMY1','4-alpha-D-glucan glucanohydrolase 1','AMY1C','1', '3.2.1.1',]))
        self.assertEquals(target['organism'], 'Homo sapiens')
        self.assertEquals(target['description'], 'Salivary alpha-amylase')
        self.assertEquals(target['geneNames'], 'Unspecified')
        self.assertEquals(target['compoundCount'], 29)
        self.assertEquals(target['bioactivityCount'], 52)

        url = self.apiPath + '/targets/CHEMBLX'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/targets/CHEMBL1000000000'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_targets_uniprot(self):
        url = self.apiPath + '/targets/uniprot/Q13936'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/uniprot/Q13936'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/uniprot/Q13936.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/targets/uniprot/Q13936.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/targets/uniprot/Q13936'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/targets/uniprot_all/Q13936'
        resp = self.api_client.get(url, format='xml')
        targets = self.deserialize(resp, format='application/xml', tag='target')
        self.assertEquals(len(targets), 3)
        target = targets[0]
        self.assertEquals(target['chemblId'], 'CHEMBL1940')
        self.assertEquals(target['targetType'], 'SINGLE PROTEIN')
        self.assertEquals(target['preferredName'], 'Voltage-gated L-type calcium channel alpha-1C subunit')
        self.assertEquals(target['proteinAccession'], 'Q13936')
        self.assertEquals(set(target['synonyms'].split(DEFAULT_TARGET_SEPARATOR)), set(['CACH2 ','CACN2',
            'Voltage-gated calcium channel subunit alpha Cav1.2','CACNA1C','Calcium channel',' L type',
            ' alpha-1 polypeptide',' isoform 1',' cardiac muscle','CCHL1A1','CACNL1A1',
            'Voltage-dependent L-type calcium channel subunit alpha-1C']))
        self.assertEquals(target['organism'], 'Homo sapiens')
        self.assertEquals(target['description'], 'Voltage-gated L-type calcium channel alpha-1C subunit')
        self.assertEquals(target['geneNames'], 'Unspecified')
        self.assertTrue(target['compoundCount'] > '170')
        self.assertTrue(target['bioactivityCount'] > '200')

        url = self.apiPath + '/targets/uniprot/Q13936'
        resp = self.api_client.get(url, format='xml')
        target = self.deserialize(resp, format='application/xml', tag='target')
        self.assertEquals(target['chemblId'], 'CHEMBL1940')
        self.assertEquals(target['targetType'], 'SINGLE PROTEIN')
        self.assertEquals(target['preferredName'], 'Voltage-gated L-type calcium channel alpha-1C subunit')
        self.assertEquals(target['proteinAccession'], 'Q13936')
        self.assertEquals(set(target['synonyms'].split(DEFAULT_TARGET_SEPARATOR)), set(['CACH2 ','CACN2',
            'Voltage-gated calcium channel subunit alpha Cav1.2','CACNA1C','Calcium channel',' L type',
            ' alpha-1 polypeptide',' isoform 1',' cardiac muscle','CCHL1A1','CACNL1A1',
            'Voltage-dependent L-type calcium channel subunit alpha-1C']))
        self.assertEquals(target['organism'], 'Homo sapiens')
        self.assertEquals(target['description'], 'Voltage-gated L-type calcium channel alpha-1C subunit')
        self.assertEquals(target['geneNames'], 'Unspecified')
        self.assertTrue(target['compoundCount'] > '170')
        self.assertTrue(target['bioactivityCount'] > '230')

        url = self.apiPath + '/targets/uniprot/Q139367'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/targets/uniprot/Q03936'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_targets_refseq(self):
        '''
        refseq shuld be removed
        '''

        url = self.apiPath + '/targets/refseq/P_001128722'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/targets/refseq/NP_001128722'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_target_bioactivities(self):

        url = self.apiPath + '/targets/CHEMBL241/bioactivities'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 600)

        url = self.apiPath + '/targets/CHEMBL241/bioactivities'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 600)

        url = self.apiPath + '/targets/CHEMBL241/bioactivities.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertTrue(len(bioactivities) > 600)

        url = self.apiPath + '/targets/CHEMBL241/bioactivities.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertTrue(len(bioactivities) > 600)

        url = self.apiPath + '/targets/CHEMBL241/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertTrue(len(bioactivities) > 600)

        url = self.apiPath + '/targets/CHEMBLX/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/targets/CHEMBL10000000000/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertEquals(len(bioactivities), 0)

#-----------------------------------------------------------------------------------------------------------------------

    def test_assays(self):

        url = self.apiPath + '/assays/CHEMBL1217643'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/assays/CHEMBL1217643'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/assays/CHEMBL1217643.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/assays/CHEMBL1217643.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/assays/CHEMBL1217643'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)

        url = self.apiPath + '/assays/CHEMBL1217643'
        resp = self.api_client.get(url, format='json')
        assay = self.deserialize(resp, format='application/json')['assay']
        self.assertEquals(assay['chemblId'], 'CHEMBL1217643')
        self.assertEquals(assay['assayType'], 'B')
        self.assertEquals(assay['journal'], 'Bioorg. Med. Chem. Lett.')
        self.assertEquals(assay['assayOrganism'], 'Homo sapiens')
        self.assertEquals(assay['assayStrain'], 'Unspecified')
        self.assertEquals(assay['assayDescription'], 'Inhibition of human hERG')
        self.assertEquals(assay['numBioactivities'], 1)

        url = self.apiPath + '/assays/CHEMBLX'
        resp = self.api_client.get(url, format='html')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/assays/CHEMBL1000000000'
        resp = self.api_client.get(url, format='html')
        self.assertHttpNotFound(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_assay_bioactivities(self):

        url = self.apiPath + '/assays/CHEMBL1217643/bioactivities'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertEquals(len(bioactivities), 1)

        bioactivity = bioactivities[0]
        self.assertEquals(bioactivity['parent__cmpd__chemblid'], 'CHEMBL1214402')
        self.assertEquals(bioactivity['ingredient__cmpd__chemblid'], 'CHEMBL1214402')
        self.assertEquals(bioactivity['target__chemblid'], 'CHEMBL240')
        self.assertEquals(bioactivity['target__confidence'], '9')
        self.assertEquals(bioactivity['target__name'], 'HERG')
        self.assertEquals(bioactivity['reference'], 'Bioorg. Med. Chem. Lett., (2010) 20:15:4359')
        self.assertEquals(bioactivity['name__in__reference'], '26')
        self.assertEquals(bioactivity['organism'], 'Homo sapiens')
        self.assertEquals(bioactivity['bioactivity__type'], 'IC50')
        self.assertEquals(bioactivity['activity__comment'], 'Unspecified')
        self.assertEquals(bioactivity['operator'], '=')
        self.assertEquals(bioactivity['units'], 'nM')
        self.assertEquals(bioactivity['assay__chemblid'], 'CHEMBL1217643')
        self.assertEquals(bioactivity['assay__type'], 'B')
        self.assertEquals(bioactivity['assay__description'], 'Inhibition of human hERG')
        self.assertEquals(bioactivity['value'], '5900')

        url = self.apiPath + '/assays/CHEMBL1217643/bioactivities'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertEquals(len(bioactivities), 1)

        url = self.apiPath + '/assays/CHEMBL1217643/bioactivities.xml'
        resp = self.api_client.get(url, format='html')
        self.assertValidXMLResponse(resp)
        bioactivities = self.deserialize(resp, format='application/xml', tag='bioactivity')
        self.assertEquals(len(bioactivities), 1)

        url = self.apiPath + '/assays/CHEMBL1217643/bioactivities.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertEquals(len(bioactivities), 1)

        url = self.apiPath + '/assays/CHEMBL1217643/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertEquals(len(bioactivities), 1)

        url = self.apiPath + '/assays/CHEMBLX/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/assays/CHEMBL10000000000/bioactivities'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        bioactivities = self.deserialize(resp, format='application/json')['bioactivities']
        self.assertEquals(len(bioactivities), 0)

#-----------------------------------------------------------------------------------------------------------------------

    def test_explode(self):
        url = self.apiPath + '/compounds.xml?chemblid=CHEMBL104&explode_synonyms=true'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

        url = self.apiPath + '/compounds.xml?chemblid=CHEMBL104'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compound = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(set(compound['synonyms'].split(DEFAULT_COMPOUND_SEPARATOR)),
                set(['Gynix','GNF-Pf-3499',
                     'Gyne-Lotrimin 3 Combination Pack','Canesten','Gyne-lotrimin','BAY-5097',
                     'Gyne-Lotrimin 3','Gyne-Lotrimin Combination Pack','Mycelex-7 Combination Pack',
                     'Mycelex-G','Clotrimazole',
                     'Gyne-Lotrimin','Mycelex-7','Trivagizole 3','Mycelex','SID90340692', 'SID85230973',
                     ]))

        url = self.apiPath + '/compounds.xml?smiles=CN1CCN(Cc2ccc(cc2)C(=O)Nc3ccc(C)c(Nc4nccc(n4)c5cccnc5)c3)CC1&explode_synonyms=true'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        compounds = self.deserialize(resp, format='application/xml', tag='compound')
        self.assertEquals(len(compounds), 2)

        url = self.apiPath + '/compounds.xml?stdinchikey=LFQSCWFLJHTTHZ-UHFFFAOYSA-N&explode_synonyms=true'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)

#-----------------------------------------------------------------------------------------------------------------------

    def test_compound_drug_mechinsims(self):

        url = self.apiPath + '/compounds/CHEMBL1200550/drugMechanism'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        drug_mechanisms = self.deserialize(resp, format='application/xml', tag='drugMechanism')
        self.assertEquals(len(drug_mechanisms), 1)

        mechanism = drug_mechanisms[0]
        self.assertEquals(mechanism['chemblId'], 'CHEMBL231')
        self.assertEquals(mechanism['name'], 'Histamine H1 receptor')
        self.assertEquals(mechanism['mechanismOfAction'], 'Histamine H1 receptor antagonist')

        url = self.apiPath + '/compounds/CHEMBL1642/drugMechanism.json'
        resp = self.api_client.get(url, format='html')
        self.assertValidJSONResponse(resp, url)
        drug_mechanisms = self.deserialize(resp, format='application/json')['drugMechanisms']
        self.assertEquals(len(drug_mechanisms), 3)

        url = self.apiPath + '/compounds/CHEMBL941/drugMechanism'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        drug_mechanisms = self.deserialize(resp, format='application/json')['drugMechanisms']
        self.assertEquals(len(drug_mechanisms), 0)

        url = self.apiPath + '/compounds/CHEMBLX/drugMechanism'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL10000000000/drugMechanism'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        drug_mechanisms = self.deserialize(resp, format='application/json')['drugMechanisms']
        self.assertEquals(len(drug_mechanisms), 0)

#-----------------------------------------------------------------------------------------------------------------------

    def test_target_approved_drugs(self):

        url = self.apiPath + '/targets/CHEMBL1824/approvedDrug.xml'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        approved_drugs = self.deserialize(resp, format='application/xml', tag='approvedDrug')
        self.assertTrue(len(approved_drugs) >= 4)

        drug = approved_drugs[0]
        self.assertEquals(drug['chemblId'], 'CHEMBL1201585')
        self.assertEquals(drug['name'], 'TRASTUZUMAB')
        self.assertEquals(drug['mechanismOfAction'], 'Receptor protein-tyrosine kinase erbB-2 inhibitor')

        url = self.apiPath + '/targets/CHEMBLX/approvedDrug'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/targets/CHEMBL10000000000/approvedDrug'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        drug_mechanisms = self.deserialize(resp, format='application/json')['approvedDrugs']
        self.assertEquals(len(drug_mechanisms), 0)

#-----------------------------------------------------------------------------------------------------------------------

    def test_compound_forms(self):

        url = self.apiPath + '/compounds/CHEMBL2107333/form.xml'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        forms = self.deserialize(resp, format='application/xml', tag='form')
        self.assertEquals(len(forms), 1)

        form  = forms[0]
        self.assertEquals(form['chemblId'], 'CHEMBL2107333')

        url = self.apiPath + '/compounds/CHEMBL415863/form.xml'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        forms = self.deserialize(resp, format='application/xml', tag='form')
        self.assertEquals(len(forms), 2)
        form_1, form_2 = forms
        self.assertEquals(form_1['chemblId'], 'CHEMBL1207563')
        self.assertEquals(form_1['parent'], 'True')
        self.assertEquals(form_2['parent'], 'False')
        self.assertEquals(form_2['chemblId'], 'CHEMBL415863')

        url = self.apiPath + '/compounds/CHEMBL278020/form'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        forms = self.deserialize(resp, format='application/json')['forms']
        self.assertEquals(len(forms), 3)
        form_1, form_2, form_3 = forms
        self.assertEquals(form_1['chemblId'], 'CHEMBL211471')
        self.assertEquals(form_2['chemblId'], 'CHEMBL54126')
        self.assertEquals(form_3['chemblId'], 'CHEMBL278020')

        url = self.apiPath + '/compounds/CHEMBL1207563/form'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        forms = self.deserialize(resp, format='application/json')['forms']
        self.assertEquals(len(forms), 2)
        form_1, form_2 = forms
        self.assertEquals(form_1['chemblId'], 'CHEMBL1207563')
        self.assertTrue(form_1['parent'])
        self.assertFalse(form_2['parent'])
        self.assertEquals(form_2['chemblId'], 'CHEMBL415863')

        url = self.apiPath + '/compounds/CHEMBL1078826/form'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        forms = self.deserialize(resp, format='application/json')['forms']
        self.assertTrue('CHEMBL1236196' in map(lambda x: x['chemblId'], forms))
        for form in forms:
            if form['chemblId'] == 'CHEMBL1236196':
                self.assertTrue(form['parent'])
            else:
                self.assertFalse(form['parent'])
        self.assertEquals(len(forms), 17)

        url = self.apiPath + '/compounds/CHEMBL941/form'
        resp = self.api_client.get(url, format='xml')
        self.assertValidXMLResponse(resp)
        forms = self.deserialize(resp, format='application/xml', tag='form')
        self.assertEquals(len(forms), 2)

        url = self.apiPath + '/compounds/CHEMBLX/form'
        resp = self.api_client.get(url, format='json')
        self.assertHttpBadRequest(resp)

        url = self.apiPath + '/compounds/CHEMBL10000000000/form'
        resp = self.api_client.get(url, format='json')
        self.assertValidJSONResponse(resp, url)
        forms = self.deserialize(resp, format='application/json')['forms']
        self.assertEquals(len(forms), 0)

#-----------------------------------------------------------------------------------------------------------------------