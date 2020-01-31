from setuptools import setup
from setuptools import find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

packages = find_packages()

extras_require = {
    'ssh': ['paramiko==2.6.0']
}

setup(
    name='adhesive',
    version='0.1.feature_cancel-running-task',
    description='adhesive',
    long_description=readme,
    author='Bogdan Mustiata',
    author_email='bogdan.mustiata@gmail.com',
    license='BSD',
    entry_points={
        "console_scripts": [
            "adhesive = adhesive.mainapp:__main"
        ]
    },
    install_requires=[
        "addict",
        "networkx==2.3",
        "npyscreen==4.10.5",
        "colorama==0.4.1",
        "termcolor==1.1.0",
        "termcolor_util==1.2.0",
        "PyYAML >=5.1, <5.2",
        "click==7.0",
        "schedule==0.6.0",
        "python-dateutil==2.8.1",
        "yamldict==1.1.0",
        "Pebble==4.5.0"],
    extras_require=extras_require,
    packages=packages,
    package_data={
        '': ['*.txt', '*.rst'],
        'adhesive': ['py.typed'],
    })
