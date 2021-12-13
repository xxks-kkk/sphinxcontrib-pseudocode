# -*- coding: utf-8 -*-

import io
from setuptools import setup, find_packages

readme = io.open('README.md', encoding="utf-8").read()
version = '0.0.1'

setup(
    name='sphinxcontrib-pseudocode',
    version=version,
    url='https://github.com/xxks-kkk/sphinxcontrib-algo/',
    download_url='https://pypi.python.org/pypi/sphinxcontrib-mermaid',
    license='BSD',
    author=u'Zeyuan Hu',
    author_email='zeyuan.zack.hu@gmail.com',
    description='Use pseudocode.js natively in yours Sphinx powered docs',
    long_description="""Use pseudocode.js natively in sphinx-doc""",
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
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['sphinxcontrib'],
)
