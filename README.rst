============
File Indexer
============

A tool to generate a histogram of words in a given set of files and
report the top *N* words encountered.

Installing the File Indexer
===========================

Installing the file indexer is as simple as "python ./setup.py
install", or alternatively, invoking "pip install .".  The latter may
be preferable, as the Python "pip" tool allows packages to be
installed in the user's directory, whereas the "python ./setup.py
install" method may require root privileges.

Testing the File Indexer
========================

A full suite of unit tests is provided.  To run the test suite
requires that the Python package "tox" be installed ("pip install
tox").  The "tox" executable reads the "tox.ini" configuration file
contained in this directory and will run the unit tests under all the
configured versions of Python that are also available on the system,
followed by running the "pep8" style tests.  (Note: "tox" builds and
uses Python virtual environments, so no requirements other than "tox"
need to be installed to run the test suite.)  To run the default set
of tests, simply invoke "tox" from the command line, with no
arguments.

The tests can also be run in a mode that allows determination of the
code covered by the test suite.  To invoke the code coverage test, use
the command "tox -e cover".

Running the File Indexer
========================

The file indexer is a fully installable Python package, which installs
a command line executable named "file_indexer".  The command line
executable includes extensive help for its command line options;
simply invoke the command as "file_indexer --help" to view the help
text.

Under normal circumstances, it would be necessary to install the
package--either into the system or into a Python virtual
environment--in order to invoke it.  As a convenience, a
"file_indexer.sh" script is provided that will construct a virtual
environment (in the ".venv" subdirectory of the source tree) and run
the command line tool from that virtual environment.  Any arguments
passed to the shell script will be passed through to the underlying
executable.

Details of the Implementation
=============================

The implementation consists of a ``_tokenize_text()`` function, which
uses a regular expression and the ``re.finditer()`` method to tokenize
the text into individual words.  This function is then used by the
``tokenize()`` function to tokenize an entire file.  (Note:
ordinarily, I'd combine ``_tokenize_text()`` and ``tokenize()`` into a
single function; however, the test specifically requested logic to
tokenize a blob of text, which I interpreted as a specific function to
perform that task.)  The ``tokenize()`` function is called by the
``histogram_from_file()`` function, which generates a ``Histogram``
instance.  This ``Histogram`` instance is then used by the ``main()``
function to isolate the top *N* words.

In my design, I chose to have the tool report not only the words and
the number of times they appear, but to also have it report the total
number of words and the number of distinct words.  I also provided an
option to report word percentages, as opposed to counts.  Finally, I
made an interpretation in the logic that selects the top words: if
there is a tie for last place in the list of top words, the routine
will return *all* words having that same count, sorted
lexicographically.  This is the only case in which more words than *N*
will be returned.

To allow the tool to execute concurrently, I used the
``multiprocessing.Pool`` functionality to allow spreading the work
across multiple worker processes.  (I chose ``multiprocessing`` to
allow the use of multiple CPUs; the implementation of threading in
Python has some limitations due to Python's use of a "Global
Interpreter Lock" (GIL), which essentially causes Python to act as if
it were single threaded.

Additional Notes
================

To generate the command line interface, I chose to use my
``cli_tools`` project and Python's support for the "console_scripts"
entrypoint.
