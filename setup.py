from distutils.core import setup
from setuptools import find_packages

setup(
    name='pycipapi',
    version='0.2.0',
    packages=find_packages(),
    scripts=[],
    url='',
    license='',
    author='priesgo',
    author_email='pablo.ferreiro@genomicsengland.co.uk',
    description='',
    install_requires=[
        'requests',
        'GelReportModels>=7.0,<7.1',
        'pythoncommonlibs'
    ]
)
