__author__ = 'mnowotka'

from tastypie.resources import Resource
from tastypie.serializers import Serializer
from tastypie.serializers import XML_ENCODING
from tastypie.api import Api
from tastypie.exceptions import ImmediateHttpResponse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastypie import http
from chembl_core_db.utils import plural
from tastypie.exceptions import UnsupportedFormat
from tastypie.exceptions import BadRequest
from StringIO import StringIO
from django.core.exceptions import ImproperlyConfigured
import mimeparse
from tastypie.utils.mime import build_content_type
import simplejson
from django.utils import six
from django.http import HttpResponse
from django.http import HttpResponseRedirect

import time
import logging
import django
import urlparse
from django.conf import settings
from django.http import HttpResponseNotFound
from tastypie.exceptions import NotFound

# If ``csrf_exempt`` isn't present, stub it.
try:
    from django.views.decorators.csrf import csrf_exempt
except ImportError:
    def csrf_exempt(func):
        return func

try:
    import defusedxml.lxml as lxml
    from defusedxml.common import DefusedXmlException
    from defusedxml.lxml import parse as parse_xml
    from lxml.etree import Element, tostring, LxmlError, XMLParser
except ImportError:
    lxml = None

try:
    TOP_LEVEL_PAGE = settings.TASTYPIE_TOP_LEVEL_PAGE
except AttributeError:
    TOP_LEVEL_PAGE = 'https://www.ebi.ac.uk/chembl/ws'

try:
    WS_DEBUG = settings.WS_DEBUG
except AttributeError:
    WS_DEBUG = False
#-----------------------------------------------------------------------------------------------------------------------

class ChEMBLApi(Api):
        def top_level(self, request, api_name=None):
            return HttpResponseRedirect(TOP_LEVEL_PAGE)

#-----------------------------------------------------------------------------------------------------------------------


class ChEMBLApiSerializer(Serializer):

    formats = ['xml', 'json', 'jsonp', 'html']

    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'html': 'application/xml',
        'urlencode': 'application/x-www-form-urlencoded',
    }

    def __init__(self, name=False):
        self.objName = name
        self.objPlural = None
        if self.objName:
            self.objPlural = plural(self.objName)
        super(ChEMBLApiSerializer, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def get_mime_for_format(self, format):
        """
        Given a format, attempts to determine the correct MIME type.

        If not available on the current ``Serializer``, returns
        ``application/json`` by default.
        """
        try:
            return self.content_types[format]
        except KeyError:
            return ''

#-----------------------------------------------------------------------------------------------------------------------

    def deserialize(self, content, format='application/json', tag=None):
        """
        Given some data and a format, calls the correct method to deserialize
        the data and returns the result.
        """
        desired_format = None

        format = format.split(';')[0]

        for short_format, long_format in self.content_types.items():
            if format == long_format:
                if hasattr(self, "from_%s" % short_format):
                    desired_format = short_format
                    break

        if desired_format is None:
            raise UnsupportedFormat(
                "The format indicated '%s' had no available deserialization method. Please check your ``formats`` "
                "and ``content_types`` on your Serializer." % format)

        if desired_format == 'xml' and tag:
            deserialized = getattr(self, "from_%s" % desired_format)(content, tag)
        else:
            deserialized = getattr(self, "from_%s" % desired_format)(content)
        return deserialized

#-----------------------------------------------------------------------------------------------------------------------

    def from_urlencode(self, data, options=None):

        qs = dict((k, v if len(v) > 1 else v[0] )
                  for k, v in urlparse.parse_qs(data).iteritems())
        return qs

#-----------------------------------------------------------------------------------------------------------------------

    def to_urlencode(self, content):
        pass

#-----------------------------------------------------------------------------------------------------------------------

    def from_xml(self, content, tag=None, forbid_dtd=True, forbid_entities=True):
        """
        Given some XML data, returns a Python dictionary of the decoded data.
        """
        if lxml is None:
            raise ImproperlyConfigured("Usage of the XML aspects requires lxml and defusedxml.")

        try:
            # Stripping the encoding declaration. Because lxml.
            # See http://lxml.de/parsing.html, "Python unicode strings".
            content = XML_ENCODING.sub('', content)
            parsed = parse_xml(
                six.StringIO(content),
                forbid_dtd=forbid_dtd,
                forbid_entities=forbid_entities
            )
        except (LxmlError, DefusedXmlException):
            raise BadRequest()

        return self.from_etree(parsed.getroot(), tagName=tag)

#-----------------------------------------------------------------------------------------------------------------------

    def to_json(self, data, options=None):
        """
        Given some Python data, produces JSON output.
        """
        if self.objName:
            return simplejson.dumps(self.to_simple(data))
        return simplejson.dumps(data)

#-----------------------------------------------------------------------------------------------------------------------

    def to_etree(self, data, options=None, name=None, depth=0):
        """
        Given some data, converts that data to an ``etree.Element`` suitable
        for use in the XML output.
        """
        typ = type(data)

        if typ is not list:
            objName = name or self.objName or 'object'
            element = Element(objName)
            for field_name, field_object in data.items():
                if field_object is not None:
                    if type(field_object) is not list:
                        el = Element(field_name)
                        el.text = unicode(field_object)
                    else:
                        el = Element('synonyms')
                        for i in field_object:
                            elm = Element('synonym')
                            elm.text = unicode(i)
                            el.append(elm)
                    element.append(el)
        else:
            element = Element(name) if name else Element('list')
            for item in data:
                element.append(self.to_etree(item))

        return element

#-----------------------------------------------------------------------------------------------------------------------

    def from_etree(self, data, tagName=None):
        """
        Not the smartest deserializer on the planet. At the request level,
        it first tries to output the deserialized subelement called "object"
        or "objects" and falls back to deserializing based on hinted types in
        the XML element attribute "type".
        """

        if data.tag == 'request':
            # if "object" or "objects" exists, return deserialized forms.
            elements = data.getchildren()
            for element in elements:
                if element.tag in ('object', 'objects'):
                    return self.from_etree(element, tagName)
            return dict((element.tag, self.from_etree(element, tagName)) for element in elements)
        elif data.tag == 'object' or data.get('type') == 'hash' or (tagName and data.tag == tagName):
            return dict((element.tag, self.from_etree(element, tagName)) for element in data.getchildren())
        elif data.tag == 'objects' or data.get('type') == 'list' or data.tag == 'list':
            return [self.from_etree(element, tagName) for element in data.getchildren()]
        else:
            type_string = data.get('type')
            if type_string in ('string', None):
                return data.text
            elif type_string == 'integer':
                return int(data.text)
            elif type_string == 'float':
                return float(data.text)
            elif type_string == 'boolean':
                if data.text == 'True':
                    return True
                else:
                    return False
            else:
                return None

#-----------------------------------------------------------------------------------------------------------------------

    def to_simple(self, data, depth=0):
        """
        For a piece of data, attempts to recognize it and provide a simplified
        form of something complex.

        This brings complex Python data structures down to native types of the
        serialization format(s).
        """
        typ = type(data)

        if typ is list:
            if depth == 0:
                return {self.objPlural: self.to_simple(data, depth=depth+1)}
        if typ is dict:
            return dict(
                    ((self.objName, dict((key, val) for (key, val) in data.iteritems() if val is not None)),))
        else:
            return data

#-----------------------------------------------------------------------------------------------------------------------


def convert_post_to_VERB(request, verb):
    """
    Force Django to process the VERB.
    """
    if request.method == verb:
        if hasattr(request, '_post'):
            del(request._post)
            del(request._files)

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = verb
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = verb

        setattr(request, verb, request.POST)

    return request


def convert_post_to_put(request):
    return convert_post_to_VERB(request, verb='PUT')

#-----------------------------------------------------------------------------------------------------------------------

class ChEMBLApiBase(Resource):

#-----------------------------------------------------------------------------------------------------------------------

    def __init__(self):
        self.log = logging.getLogger(__name__)
        super(Resource, self).__init__()

#-----------------------------------------------------------------------------------------------------------------------

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            request.format = kwargs.pop('format', None)

            if request.method == 'GET':
                kwargs.update(request.GET.dict())

            elif request.method == 'POST':
                if request.META.get('CONTENT_TYPE', 'application/json').startswith(
                    ('multipart/form-data', 'multipart/form-data')):
                    post_arg = request.POST.dict()
                else:
                    post_arg = self.deserialize(request, request.body,
                        format=request.META.get('CONTENT_TYPE', 'application/json'))
                kwargs.update(post_arg)

            wrapped_view = super(ChEMBLApiBase, self).wrap_view(view)
            return wrapped_view(request, *args, **kwargs)

        return wrapper

#-----------------------------------------------------------------------------------------------------------------------

    def dispatch(self, request_type, request, **kwargs):
        """
        Handles the common operations (allowed HTTP method, authentication,
        throttling, method lookup) surrounding most CRUD interactions.
        """
        allowed_methods = getattr(self._meta, "%s_allowed_methods" % request_type, None)
        request_method = self.method_check(request, allowed=allowed_methods)

        method = getattr(self, "%s_%s" % (request_method, request_type), None)

        if method is None:
            raise ImmediateHttpResponse(response=http.HttpNotImplemented())

        # All clear. Process the request.
        request = convert_post_to_put(request)
        response = method(request, **kwargs)

        # If what comes back isn't a ``HttpResponse``, assume that the
        # request was accepted and that some action occurred. This also
        # prevents Django from freaking out.
        if not isinstance(response, HttpResponse):
            return http.HttpNoContent()

        return response

#-----------------------------------------------------------------------------------------------------------------------

    def determine_format(self, request):
        """
        Tries to "smartly" determine which output format is desired.

        First attempts to find a ``format`` override from the request and supplies
        that if found.

        If no request format was demanded, it falls back to ``mimeparse`` and the
        ``Accepts`` header, allowing specification that way.

        If still no format is found, returns the ``default_format`` (which defaults
        to ``application/json`` if not provided).
        """
        # First, check if they forced the format.

        serializer = self._meta.serializer
        default_format = self._meta.default_format
        best_format = ''

        if request.GET.get('format'):
            if request.GET['format'] in serializer.formats:
                best_format =  serializer.get_mime_for_format(request.GET['format'])

        elif hasattr(request, 'format') and request.format:
            if request.format in serializer.formats:
                best_format =  serializer.get_mime_for_format(request.format)

        # If callback parameter is present, use JSONP.
        elif request.GET.has_key('callback'):
            best_format =  serializer.get_mime_for_format('jsonp')

        # Try to fallback on the Accepts header.
        elif request.META.get('HTTP_ACCEPT', '*/*') != '*/*':
            formats = list(serializer.supported_formats) or []
            # Reverse the list, because mimeparse is weird like that. See also
            # https://github.com/toastdriven/django-tastypie/issues#issue/12 for
            # more information.
            formats.reverse()
            best_format = mimeparse.best_match(formats, request.META['HTTP_ACCEPT'])

        if best_format:
            return best_format

        # No valid 'Accept' header/formats. Sane default.
        return default_format

#-----------------------------------------------------------------------------------------------------------------------

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        #       impossible.
        start = time.time()
        objects, in_cache = self.cached_obj_get_list(request=request, **self.remove_api_resource_names(kwargs))
        end = time.time()
        if type(objects) == http.HttpNotFound:
            res = objects
        else:
            res = self.create_response(request, objects)
        if WS_DEBUG:
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start
        return res

#-----------------------------------------------------------------------------------------------------------------------

    def get_detail(self, request, **kwargs):
        """
        Returns a single serialized resource.

        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        try:
            start = time.time()
            obj, in_cache = self.cached_obj_get(request=request, **self.remove_api_resource_names(kwargs))
            end = time.time()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        if type(obj) == http.HttpNotFound:
            res = obj
        else:
            res = self.create_response(request, obj)
        if WS_DEBUG:
            res['X-ChEMBL-in-cache'] = in_cache
            res['X-ChEMBL-retrieval-time'] = end - start
        return res

#-----------------------------------------------------------------------------------------------------------------------

    def cached_obj_get_list(self, request=None, **kwargs):
        """
        A version of ``obj_get_list`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
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

    def cached_obj_get(self, request=None, **kwargs):
        """
        A version of ``obj_get`` that uses the cache as a means to get
        commonly-accessed data faster.
        """
        cache_key = self.generate_cache_key('detail', **kwargs)
        get_failed = False
        in_cache = True

        try:
            bundle = self._meta.cache.get(cache_key)
        except Exception:
            bundle = None
            get_failed = True
            self.log.error('Caching get exception', exc_info=True, extra={'request': request,})

        if bundle is None:
            in_cache = False
            bundle = self.obj_get(request=request, **kwargs)
            if not get_failed:
                try:
                    self._meta.cache.set(cache_key, bundle)
                except Exception:
                    self.log.error('Caching set exception', exc_info=True, extra={'request': request,})

        return bundle, in_cache

#-----------------------------------------------------------------------------------------------------------------------

    def _handle_500(self, request, exception):
        import traceback
        import sys

        the_trace = '\n'.join(traceback.format_exception(*(sys.exc_info())))
        response_class = http.HttpApplicationError

        if isinstance(exception, (NotFound, ObjectDoesNotExist)):
            response_class = HttpResponseNotFound

        if settings.DEBUG:
            data = {
                "error_message": unicode(exception),
                "traceback": the_trace,
            }
            desired_format = self.determine_format(request)
            serialized = self.serialize(request, data, desired_format)
            return response_class(content=serialized, content_type=build_content_type(desired_format))

        # When DEBUG is False, send an error message to the admins (unless it's
        # a 404, in which case we check the setting).
        if not isinstance(exception, (NotFound, ObjectDoesNotExist)):
            log = logging.getLogger('sentry.errors')
            log.error('Internal Server Error: %s' % request.path, exc_info=sys.exc_info(),
                      extra={'status_code': 500, 'request': request})

            if django.VERSION < (1, 3, 0) and getattr(settings, 'SEND_BROKEN_LINK_EMAILS', False):
                from django.core.mail import mail_admins

                subject = 'Error (%s IP): %s' % (
                (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
                try:
                    request_repr = repr(request)
                except:
                    request_repr = "Request repr() unavailable"

                message = "%s\n\n%s" % (the_trace, request_repr)
                mail_admins(subject, message, fail_silently=True)

        # Prep the data going out.
        data = {
            "exception": getattr(settings, 'TASTYPIE_CANNED_ERROR',
                                 "Sorry, this request could not be processed. Please try again later."),
        }
        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=build_content_type(desired_format))

#-----------------------------------------------------------------------------------------------------------------------
