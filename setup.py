from setuptools import setup, find_packages

VERSION = '0.0.2'

with open("README.md", "r") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

DESCRIPTION = ('A small library for getting info about Ukrainian banks ')


setup(
    name="fnw",
    version=VERSION,
    author="Solohub Illia",
    author_email="illa98994@gmail.com",
    license='MIT',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=required,
    packages=find_packages(),
    keywords=['python', 'exchange rate', 'minfin'],
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls={
        'Source': 'https://github.com/Mimkaa/Fiddling_with_minfin',
    },
)