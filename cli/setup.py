#!/usr/bin/env python3
"""
Setup script for API Orchestrator CLI
Makes it installable via pip as 'api-orchestrator-cli'
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_file(filename):
    try:
        with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "API Orchestrator CLI - The ultimate API testing tool"

setup(
    name="api-orchestrator-cli",
    version="5.0.0",
    author="Chinmay Shrivastava",
    author_email="support@streamapi.dev",
    description="The ultimate API testing CLI - Newman killer with AI-powered features",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/JonSnow1807/api-orchestrator",
    project_urls={
        "Homepage": "https://streamapi.dev",
        "Documentation": "https://docs.streamapi.dev",
        "Source": "https://github.com/JonSnow1807/api-orchestrator",
        "Bug Tracker": "https://github.com/JonSnow1807/api-orchestrator/issues",
    },
    packages=find_packages(),
    py_modules=["api_orchestrator_cli_enhanced"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Environment :: Console",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "tabulate>=0.9.0",
        "colorama>=0.4.6",
        "jsonpath-ng>=1.6.0",
        "jsonschema>=4.17.0",
        "deepdiff>=6.7.0",
        "faker>=20.0.0",
        "jinja2>=3.1.0",
        "requests>=2.31.0",
        "tqdm>=4.66.0",
        "rich>=13.0.0",
        "websocket-client>=1.5.0",
        "watchdog>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "ci": [
            "junit-xml>=1.9",
            "allure-pytest>=2.12.0",
        ],
        "performance": [
            "locust>=2.15.0",
            "matplotlib>=3.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "api-orchestrator=api_orchestrator_cli_enhanced:cli",
            "aorchestrator=api_orchestrator_cli_enhanced:cli",
            "aorch=api_orchestrator_cli_enhanced:cli",
        ],
    },
    include_package_data=True,
    keywords=[
        "api", "testing", "postman", "newman", "cli", "automation", "ci-cd",
        "openapi", "swagger", "http", "rest", "graphql", "websocket",
        "mock", "server", "ai", "intelligence", "orchestrator"
    ],
)