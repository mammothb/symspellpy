==========
Installing
==========

Installing an official release
==============================

symspellpy and its dependencies are available as wheel packages for macOS,
Windows and Linux distributions::

  python -m pip install -U symspellpy

**NOTE**: symspellpy has only been tested on Windows and Linux systems and is
assumed to work on macOS.

Dictionary data
===============
The dictionary files that are shipped with symspellpy can be accesed using
`pkg_resources`::

  dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
  bigram_path = pkg_resources.resource_filename("symspellpy", "frequency_bigramdictionary_en_243_342.txt")

Alternatively, you can download the dictionary files from the repository and
add them to your project directory::

  curl -LJO https://raw.githubusercontent.com/mammothb/symspellpy/master/symspellpy/frequency_dictionary_en_82_765.txt
  curl -LJO https://raw.githubusercontent.com/mammothb/symspellpy/master/symspellpy/frequency_bigramdictionary_en_243_342.txt

You could end up with a project directory layout like::

  project_dir
  +-frequency_bigramdictionary_en_243_342.txt
  +-frequency_dictionary_en_82_765.txt
  \-project.py
