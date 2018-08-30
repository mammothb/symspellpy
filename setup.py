import os
import setuptools

cwd = os.path.realpath(os.path.dirname(__file__))

with open("README.md", "r") as infile:
    long_description = infile.read()

about = {}
with open(os.path.join(cwd, "symspellpy", "__version__.py"), "r",
          encoding="utf-8") as infile:
    exec(infile.read(), about)

with open("README.md", "r", encoding="utf-8") as infile:
    readme = infile.read()

# setup(
#     name=about["__title__"],
#     version=about["__version__"],
#     description=about["__description__"],
#     long_description=readme,
#     long_description_content_type="text/markdown",
#     author=about["__author__"],
#     author_email=about["__author_email__"],
#     url=about["__url__"],
#     packages=packages,
#     package_data={"": ["LICENSE", "NOTICE"], "requests": ["*.pem"]},
#     package_dir={"requests": "requests"},
#     include_package_data=True,
#     python_requires=">=3.4",
#     install_requires=requires,
#     license=about["__license__"],
#     zip_safe=False,
#     classifiers=[
#         "Development Status :: 5 - Production/Stable",
#         "Intended Audience :: Developers",
#         "Natural Language :: English",
#         "License :: OSI Approved :: Apache Software License",
#         "Programming Language :: Python",
#         "Programming Language :: Python :: 3",
#         "Programming Language :: Python :: 3.4",
#         "Programming Language :: Python :: 3.5",
#         "Programming Language :: Python :: 3.6",
#         "Programming Language :: Python :: 3.7"
#     ],
#     cmdclass={"test": PyTest},
#     tests_require=test_requirements,
# )