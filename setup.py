import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

cwd = os.path.realpath(os.path.dirname(__file__))

class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


# "setup.py publish" shortcut.
if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel")
    os.system("twine upload dist/*")
    sys.exit()

packages = ["symspellpy"]

requires = [
    "numpy>=1.13.1"
]
test_requirements = [
    'pytest-cov',
    'pytest>=3.7.1'
]

about = {}
with open(os.path.join(cwd, "symspellpy", "__version__.py"), "r",
          encoding="utf-8") as infile:
    exec(infile.read(), about)

with open("README.md", "r", encoding="utf-8") as infile:
    readme = infile.read()
with open("CHANGELOG.md", "r", encoding="utf-8") as infile:
    changelog = infile.read()

setup(
    name=about["__title__"],
    version=about["__version__"],
    description=about["__description__"],
    long_description=readme + "\n\n" + changelog,
    long_description_content_type="text/markdown",
    author=about["__author__"],
    author_email=about["__author_email__"],
    url=about["__url__"],
    packages=packages,
    package_data={"": ["LICENSE", "NOTICE"], "requests": ["*.pem"]},
    package_dir={"requests": "requests"},
    include_package_data=True,
    python_requires=">=3.4",
    install_requires=requires,
    license=about["__license__"],
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
    cmdclass={"test": PyTest},
    tests_require=test_requirements,
)
