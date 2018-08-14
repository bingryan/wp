import json
from os.path import join, dirname
from setuptools import setup, find_packages

with open(join(dirname(__file__), 'wp/VERSION'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(
    name='wp',
    version=version,
    url='https://github.com/ycvbcvfu/wp',
    include_package_data=True,
    long_description=open('README.md').read(),
    license='GNU',
    author='ycvbcvfu',
    packages=find_packages(exclude=('tests', 'tests.*')),
    author_email='ice0096@gmail.com',
    classifiers=[],
    package_data={
        'wp': [
            '*.json',
            'images/*'
        ]
    },
    description='this is demo',
    keywords='wallpaper  python',
    entry_points={
        'console_scripts': [
            'wp = wp.cli:run',
        ],
    },
    install_requires=[
        'aiofile'
    ]
)
