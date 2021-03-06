from setuptools import setup, find_packages

setup(
    name='nlelement',
    version='0.0.1',
    packages=find_packages(exclude=['tests']),
    author='rokurosatp',
    url='https://github.com/rokurosatp/nlelement',
    package_data={'nlelement': ['sqlcode/*.sql']},
    install_requires=['pydot-ng>=1.0.0',],
)