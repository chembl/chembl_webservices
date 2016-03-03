#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'mnowotka'

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='chembl_webservices',
    version='0.7.2',
    author='Michal Nowotka',
    author_email='mnowotka@ebi.ac.uk',
    description='Python package providing chembl webservices API.',
    url='https://www.ebi.ac.uk/chembldb/index.php/ws',
    license='Apache Software License',
    packages=['chembl_webservices'],
    long_description=open('README.rst').read(),
    install_requires=[
        'lxml',
        'defusedxml>=0.4.1',
        'simplejson==2.3.2',
        'Pillow>=2.1.0',
        'django-tastypie==0.10',
        'chembl_core_model>=0.7.0',
        'cairocffi>=0.5.1',
        'numpy>=1.7.1',
        'mimeparse',
        'raven>=3.5.0',
    ],
    include_package_data=True,
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Chemistry'],
    zip_safe=False,
)
