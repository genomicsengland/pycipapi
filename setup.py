from setuptools import find_packages, setup

setup(
    name='pycipapi',
    version='0.12.1',
    packages=find_packages(),
    scripts=[],
    url='https://github.com/genomicsengland/pycipapi',
    license='',
    author='antonior,priesgo',
    author_email='antonio.rueda-martin@genomicsengland.co.uk',
    description='',
    install_requires=[
        'requests==2.31.0',
        'GelReportModels==7.7.1'
    ]
)
