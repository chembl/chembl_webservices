__author__ = 'mnowotka'

from tastypie.cache import SimpleCache

#TODO: This class is ultra lame. Proper solution would be upgrading tastypie
class ChemblCache(SimpleCache):
    def set(self, key, value, timeout=30000000):
        super(ChemblCache, self).set(key, value, 30000000)

