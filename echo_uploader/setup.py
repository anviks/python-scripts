from setuptools import setup, find_packages

setup(
    name='echo-uploader',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'echo-uploader = echo_uploader.main:main',
        ],
    },
    package_data={
        '': ['config.yaml'],
    },
)
