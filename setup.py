from setuptools import find_packages, setup

setup(
    name='pycipapi',
    version='0.7.0',
    packages=find_packages(),
    scripts=[],
    url='',
    license='',
    author='antonior,priesgo',
    author_email='pablo.ferreiro@genomicsengland.co.uk',
    description='',
    install_requires=[
        'requests',
        'GelReportModels>=7.2'
    ]
)
