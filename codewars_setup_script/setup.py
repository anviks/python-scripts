from setuptools import setup, find_packages

setup(
    name='codewars-init',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'codewars-init = codewars_init.main:main',
        ],
    },
    package_data={
        '': ['templates/*', 'history.json']
    },
)
