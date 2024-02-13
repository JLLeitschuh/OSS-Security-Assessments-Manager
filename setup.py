#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="oss-security-assessments-manager",
    version="0.0.1",
    author="Jonathan Leitschuh",
    author_email="Jonathan.Leitschuh@gmail.com",
    description="A manager for the `OSS-Security-Assessments` GitHub Organization.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OSS-Security-AssessmentsOSS-Security-Assessments-Manager",
    package_dir={'': 'src'},
    packages=find_packages(where="src"),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.11',
    install_requires=[
        "PyYAML>=6.0",
        "PyGithub>=2.1.1",
        "selenium>=4.16.0",
        "pyotp>=2.9.0",
    ],
    extras_require={
        "cli": [
            "rich>=11.0.0",
            "rich-argparse>=1.0.0",
            "python-dotenv>=1.0.0",
        ],
        "test": [
            "pytest>=6",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "oss-security-assessments-manager=oss_security_assessments.__main__:cli",
        ],
    },
)
