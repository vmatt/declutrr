from setuptools import setup, find_packages

setup(
    name="declutrr",
    packages=find_packages(),
    install_requires=[
        'Pillow>=11.0.0',
    ],
    entry_points={
        'console_scripts': [
            'declutrr=declutrr.declutrr:main',
        ],
    },
)
