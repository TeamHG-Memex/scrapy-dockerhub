from setuptools import setup, find_packages

setup(
    name='scrapy_dockerhub',
    version='0.1',
    packages=find_packages(),
    scripts=[
        'scripts/dockerhub-patch-settings'
    ],
    install_requires=['scrapy', 'fabric']
)
