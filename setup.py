"""Setup configuration for Python Publisher-Subscriber system."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="Python.Publisher.Subscriber",
    version="1.0.0",
    author="venantvr",
    author_email="venantvr@gmail.com",
    description="A real-time Publisher-Subscriber system using WebSockets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/venantvr/Python.Publisher.Subscriber",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Flask==3.0.0",
        "flask-socketio==5.3.6",
        "eventlet==0.40.3",
        "python-socketio[client]==5.10.0",
        "requests==2.32.4",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            "pre-commit>=3.3.3",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pubsub-server=pubsub_ws:main",
            "pubsub-client=client:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)