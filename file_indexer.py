# Copyright 2016 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the
#    License. You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing,
#    software distributed under the License is distributed on an "AS
#    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#    express or implied. See the License for the specific language
#    governing permissions and limitations under the License.

from __future__ import print_function

import collections
import multiprocessing
import re
import sys

import cli_tools
import six


# Default number of workers to use if we're using workers, but can't
# determine the number of CPUs on the system
DEFAULT_WORKERS = 4


# A regular expression that matches a word.
WORD_RE = re.compile('[a-zA-Z0-9]+')


# Note: Ordinarily, I'd combine this logic with the tokenize()
# function below; I've written it as a separate function because the
# dev test requested a function to tokenize a blob of text, rather
# than to tokenize a file.
def _tokenize_text(text):
    """
    Tokenize the text into a sequence of words.  This is implemented
    as a generator function to minimize the resources required.

    :param text: The text to tokenize.

    :returns: An iterator over the words in the text.
    """

    # Iterate over all matches in the text.
    for match in WORD_RE.finditer(text):
        yield match.group(0)


def tokenize(fh):
    """
    Tokenize a file into a sequence of words.  This is implemented as
    a generator function to minimize the resources required.

    :param fh: A file handle for a file to tokenize.

    :returns: An iterator over the words in the file.
    """

    # To limit resource usage, read the file line by line
    for line in fh:
        for word in _tokenize_text(line):
            yield word


def _zero():
    """
    A helper function for use with ``collections.defaultdict`` in
    ``Histogram``.  While the ``defaultdict`` used by ``Histogram``
    could be constructed with a simple ``lambda``, the resulting
    object cannot be pickled, which could cause difficulty with using
    the ``multiprocessing`` library.

    :returns: The fixed value 0.
    """

    return 0  # pragma: no cover


class Histogram(object):
    """
    A helper class to collect a histogram of word frequency.  This
    class provides the ``add()`` method--to add mention of a word--and
    the ``top_words()`` method--to return a list of the top n words
    encountered, along with the associated counts.  The properties
    ``total_words`` and ``distinct_words`` are also provided, giving
    the total number of words added and the number of distinct words
    added, respectively.  That is, if ``add()`` is called twice for
    the word "foo" and once for the word "bar", ``total_words`` would
    be 3, while ``distinct_words`` would be 2.
    """

    def __init__(self):
        """
        Initialize a ``Histogram`` object.
        """

        self._words = collections.defaultdict(_zero)
        self._total = 0

    def __iadd__(self, other):
        """
        Combine another ``Histogram`` object with this one.  This adds all
        the word counts from ``other`` to this object.

        :param other: Another ``Histogram`` object.

        :returns: If ``other`` is not an instance of ``Histogram``,
                  the Python singleton ``NotImplemented`` is returned;
                  otherwise, returns this object with all counts
                  updated.
        """

        # Only allow in-place adds if other is a Histogram
        if not isinstance(other, Histogram):
            return NotImplemented

        # Add all the words from other to this Histogram
        for word, count in six.iteritems(other._words):
            self._words[word] += count

        # Also update the total
        self._total += other._total

        # Have to return self to satisfy Python
        return self

    def __add__(self, other):
        """
        Combine two ``Histogram`` objects.  This sums all the word counts
        in each ``Histogram`` and returns a new ``Histogram`` object.

        :param other: Another ``Histogram`` object.

        :returns: If ``other`` is not an instance of ``Histogram``,
                  the Python singleton ``NotImplemented`` is returned;
                  otherwise, returns a new ``Histogram`` having the
                  sum of the counts from this ``Histogram`` instance
                  and ``other``.
        """

        # Only allow adds if other is a Histogram
        if not isinstance(other, Histogram):
            return NotImplemented

        # This method returns a new Histogram, so create it
        new_hist = self.__class__()

        # Delegate to __iadd__()
        new_hist += self
        new_hist += other

        return new_hist

    def add(self, word):
        """
        Add a designated word to the ``Histogram``.

        :param word: The word to add.  Note that the case of this word
                     is ignored; that is, "foo" and "FOO" are treated
                     as the same word.
        """

        # Coerce the word to lowercase
        word = word.lower()

        # Increment the total
        self._total += 1

        # And increment the word count for that word
        self._words[word] += 1

    def top_words(self, count=10):
        """
        Generate a list of the top words in the histogram.

        :param count: The number of top words to return.  Defaults to
                      10.  Note that, if there is a tie for last
                      place, additional words could be returned.

        :returns: A list of tuples.  The first element of each tuple
                  will be a word, and the second element will be the
                  count of the number of times that word was added to
                  the ``Histogram`` object.  The list is ordered from
                  most freqent to least frequent.  Note that this list
                  could be longer than specified by the ``count``
                  argument, if there is a tie for last place.  Also
                  note that, if counts match up, the words will be
                  sorted lexicographically.
        """

        # First, generate a list of word/count tuples, sorted by count
        word_list = [(k, v) for k, v in sorted(six.iteritems(self._words),
                                               key=lambda x: (x[1], x[0]),
                                               reverse=True)]

        # If there are fewer entries than count, we're all done
        if len(word_list) < count:
            return word_list

        # We could have a tie at last place; my interpretation is that
        # we should include all the tied words
        last_count = word_list[count - 1][1]
        while count < len(word_list):
            if word_list[count][1] == last_count:
                count += 1
            else:
                break

        # Return count entries
        return word_list[:count]

    @property
    def total_words(self):
        """
        The total number of words added to the ``Histogram`` object.  This
        is identical to the number of times the ``add()`` method has
        been called.
        """

        return self._total

    @property
    def distinct_words(self):
        """
        The total number of distinct words added to the ``Histogram``
        object.
        """

        return len(self._words)


def histogram_from_file(fname=None):
    """
    Generate a ``Histogram`` object based on the contents of a named
    file.

    :param fname: The name of the file to digest.  If not
                  provided, standard input will be digested.

    :returns: An instance of ``Histogram`` containing the word
              counts for the file designated by ``fname``.
    """

    # Allocate a Histogram
    hist = Histogram()

    # Handle the request for stdin
    if fname is None:
        for word in tokenize(sys.stdin):
            hist.add(word)
    else:
        # Open the file
        with open(fname) as fh:
            for word in tokenize(fh):
                hist.add(word)

    # Return the Histogram object
    return hist


@cli_tools.argument(
    'files',
    nargs='+',
    help='Input files to process.  At least one file must be provided.  To '
    'read from standard input, use the file name "-"; this must not appear '
    'more than once in the list of files.',
)
@cli_tools.argument(
    '--output', '-o',
    default='-',
    help='Output file.  If not provided, or if "-" is provided, output will '
    'be sent to standard output.',
)
@cli_tools.argument(
    '--count', '-c',
    default=10,
    type=int,
    help='Number of words to report.  The total number reported may be '
    'larger than this value if there is a tie for last place in the result.  '
    'Note that words will be in lexicographic order for any ties.  Default: '
    '%(default)s.',
)
@cli_tools.argument(
    '--percentages', '-p',
    default=False,
    action='store_true',
    help='Report word frequency as percentages rather than counts.  '
    'Percentages will be reported to 2 decimal places.  Default is to report '
    'word counts.',
)
@cli_tools.argument(
    '--workers', '-w',
    default=None,
    type=int,
    help='Number of workers to utilize.  If not provided, input files are '
    'processed synchronously, and no workers are forked.  If set to "0", '
    'a best effort is made to create one worker per CPU on the system.  '
    '(The value "4" will be used if this information cannot be determined '
    'programmatically.)  Any other integer value will set the number of '
    'workers to that value.',
)
def main(files, out, count=10, percentages=False, workers=None):
    """
    Generate a histogram of words in a given set of files and report
    the top N words encountered.

    :param files: A list of file names to read.
    :param out: The file handle to which to send output.  Must be
                opened in "text" mode.
    :param count: A count of the number of top words to report.
                  Defaults to 10.  Note that the number of words
                  reported may be larger than this count if there is a
                  tie for last place.
    :param percentages: If ``True``, percentages to 2 decimal places
                        will be reported, as opposed to simple word
                        counts.
    :param workers: An optional integer specifying the number of
                    worker processes to use.  A value of "0" will be
                    converted into a best guess at the number of CPUs
                    on the system (with "4" being used if no guess is
                    available).  Any other value will fork that many
                    worker processes.

    :raises ValueError:
        The value of ``workers`` is invalid, or "-" is specified
        multiple times in ``files``.
    """

    # Sanity-check and appropriately massage the list of files
    if files.count('-') > 1:
        raise ValueError('The special file "-" may only be specified once.')
    files = [None if f == '-' else f for f in files]

    # Are we using workers?
    if workers is not None:
        if not isinstance(workers, six.integer_types):
            raise ValueError('Non-integer value for workers: %r' % workers)
        elif workers < 0:
            raise ValueError('Number of workers must be >= 0')

        # If workers is 0, use our best guess
        if workers == 0:
            try:
                workers = multiprocessing.cpu_count()
            except NotImplementedError:
                workers = DEFAULT_WORKERS

        # Create the pool
        pool = multiprocessing.Pool(workers)

        # Collect all the Histogram results
        results = pool.map(histogram_from_file, files)
    else:
        # Collect all the Histogram results without using workers
        results = [histogram_from_file(f) for f in files]

    # Sum together all the results
    final_result = sum(results, Histogram())

    # Report the total number of words:
    print('Total number of words: %d' % final_result.total_words, file=out)
    print('Total distinct words: %d' % final_result.distinct_words, file=out)

    # Collect the top words
    top_words = final_result.top_words(count)

    # Emit statistics for the top words
    print('\nTop %d word(s):' % len(top_words), file=out)
    for word, word_cnt in top_words:
        # Pick the appropriate display value
        if percentages:
            percent = (word_cnt * 100.0) / final_result.total_words
            print('    %s: %.2f%%' % (word, percent), file=out)
        else:
            print('    %s: %d' % (word, word_cnt), file=out)


@main.processor
def _processor(args):
    """
    A ``cli_tools`` processor function that interfaces between the
    command line and the ``main()`` function.  This function is
    responsible for opening and closing the output file as needed.

    :param args: The ``argparse.Namespace`` object containing the
                 results of argument processing.
    """

    # Set up the correct output file handle
    if not args.output or args.output == '-':
        args.out = sys.stdout
        close_out = False
    else:
        args.out = open(args.output, 'w')
        close_out = True

    # Yield to the main() function
    try:
        yield

    # Make sure the file gets closed properly
    finally:
        if close_out:
            args.out.close()
