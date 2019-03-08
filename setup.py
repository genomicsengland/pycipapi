from setuptools import find_packages, setup

setup(
    name='pycipapi',
    version='0.5.2',
    packages=find_packages(),
    scripts=[],
    url='',
    license='',
    author='priesgo',
    author_email='pablo.ferreiro@genomicsengland.co.uk',
    description='',
    install_requires=[
        'requests',
        'GelReportModels>=7.1,<7.2'
    ]
)
