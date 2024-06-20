from setuptools import setup, find_packages

setup(
    name='echo-downloader',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'echo-downloader = echo_downloader.main:main',
        ],
    },
    package_data={
        '': ['config.yaml'],
    },
)
