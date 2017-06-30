from setuptools import setup, find_packages


setup(
    name="AzureSearchEmulator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "pyparsing",
        "defusedxml"
    ],
    entry_points={
        'console_scripts': [
            'AzureSearchEmulator = AzureSearchEmulator.main:main'
        ]
    }
)
