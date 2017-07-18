#!/usr/bin/env python3

import os

from setuptools import setup, find_packages

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

version = None
exec(open('mupushservice/__init__.py').read())

with open('./requirements.txt') as reqs_txt:
    requirements = list(iter(reqs_txt))


with open('./requirements-test.txt') as test_reqs_txt:
    test_requirements = list(iter(test_reqs_txt))


setup(
    name="mupushservice",
    version=version,
    description="A microservice that opens a WebSocket that push messages "
                "of resource update of mu-cl-resources to the clients",
    url='https://github.com/tenforce/mu-push-service',
    packages=find_packages(exclude=["tests.*", "tests"]),
    install_requires=requirements,
    tests_require=test_requirements,
    zip_safe=False,
    test_suite='tests',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
    ],
    maintainer='Cecile Tonglet',
    maintainer_email='cecile.tonglet@gmail.com',
)
