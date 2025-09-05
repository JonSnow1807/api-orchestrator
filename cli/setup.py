from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="api-orchestrator",
    version="1.0.0",
    author="API Orchestrator Team",
    author_email="support@api-orchestrator.com",
    description="AI-powered API development platform - Transform any codebase into production-ready APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonSnow1807/api-orchestrator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "websocket-client>=1.5.0",
        "watchdog>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "api-orchestrator=api_orchestrator:cli",
            "apo=api_orchestrator:cli",  # Short alias
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/JonSnow1807/api-orchestrator/issues",
        "Source": "https://github.com/JonSnow1807/api-orchestrator",
        "Documentation": "https://api-orchestrator.com/docs",
    },
)