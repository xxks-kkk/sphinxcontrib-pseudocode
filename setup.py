# -*- coding: utf-8 -*-

import io
from setuptools import setup, find_namespace_packages

version = '0.3.0'

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='sphinxcontrib-pseudocode',
    version=version,
    url='https://github.com/xxks-kkk/sphinxcontrib-algo/',
    license='BSD',
    author=u'Zeyuan Hu',
    author_email='zeyuan.zack.hu@gmail.com',
    description='Use pseudocode.js natively in yours Sphinx powered docs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_namespace_packages(),
    include_package_data=True,
    namespace_packages=['sphinxcontrib'],
)
