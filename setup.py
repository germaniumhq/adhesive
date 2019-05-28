from setuptools import setup
from setuptools import find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

packages = find_packages()

setup(
    name='adhesive',
    version='0.2.15',
    description='adhesive',
    long_description=readme,
    author='Bogdan Mustiata',
    author_email='bogdan.mustiata@gmail.com',
    license='BSD',
    entry_points={
        "console_scripts": [
            "adhesive = adhesive.mainapp:main"
        ]
    },
    install_requires=[
        "networkx==2.3",
        "npyscreen==4.10.5",
        "colorama==0.4.1",
        "termcolor==1.1.0",
        "termcolor_util==1.0.1",
        "PyYAML >=5.1, <5.2"],
    packages=packages,
    package_data={
        '': ['*.txt', '*.rst']
    })
