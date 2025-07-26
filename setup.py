#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="terminai",
    version="0.1.0",
    author="Terminai Team",
    description="An intelligent terminal with LLM integration and MCP support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "httpx>=0.25.0",
        "python-dotenv>=1.0.0",
        "click>=8.0.0",
        "mcp>=0.1.0",
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "google-generativeai>=0.3.0",
        "pyyaml>=6.0",
        "keyring>=24.0.0",
    ],
    entry_points={
        "console_scripts": [
            "terminai=terminai.main:main",
        ],
    },
)
