#!/usr/bin/env python3
"""
Setup script for Brand Analyzer CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Get the current directory (src)
current_dir = Path(__file__).parent

with open(current_dir / "README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(current_dir / "requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="brand-analyzer",
    version="1.0.0",
    author="Brand Analyzer Team",
    description="Comprehensive brand analysis using LLM-powered web search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="."),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "brand-analyzer=brand_analyzer.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
