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

import argparse
import collections
import sys
import unittest

import mock
import six

import file_indexer


class TokenizeTextTest(unittest.TestCase):
    def test_base(self):
        text = 'This is A TEST OF the!!!!tok3n! !izer!'
        expected = ['This', 'is', 'A', 'TEST', 'OF', 'the', 'tok3n', 'izer']

        result = list(file_indexer._tokenize_text(text))

        self.assertEqual(result, expected)


class TokenizeTest(unittest.TestCase):
    def test_base(self):
        fh = six.StringIO('This is A TEST OF\n\nthe!!!!\ntok3n!\n!izer!')
        expected = ['This', 'is', 'A', 'TEST', 'OF', 'the', 'tok3n', 'izer']

        result = list(file_indexer.tokenize(fh))

        self.assertEqual(result, expected)


def make_fh():
    """
    Test suite helper to create a file handle.
    """

    fh = mock.MagicMock()
    fh.__enter__.return_value = fh
    fh.__exit__.return_value = None

    return fh


class HistogramTest(unittest.TestCase):
    def test_init(self):
        result = file_indexer.Histogram()

        self.assertIsInstance(result._words, collections.defaultdict)
        self.assertEqual(result._words, {})
        self.assertEqual(result._words['spam'], 0)  # test the lambda
        self.assertEqual(result._total, 0)

    def test_iadd_bad_other(self):
        obj = file_indexer.Histogram()

        result = obj.__iadd__('other')

        self.assertEqual(result, NotImplemented)

    def test_iadd_base(self):
        obj1 = file_indexer.Histogram()
        obj1._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj1._total = 150
        obj2 = file_indexer.Histogram()
        obj2._words.update({
            'word2': 20,
            'word4': 50,
            'word6': 80,
        })
        obj2._total = 150

        obj1 += obj2

        self.assertEqual(obj1._words, {
            'word1': 50,
            'word2': 60,
            'word3': 30,
            'word4': 70,
            'word5': 10,
            'word6': 80,
        })
        self.assertEqual(obj1._total, 300)
        self.assertEqual(obj2._words, {
            'word2': 20,
            'word4': 50,
            'word6': 80,
        })
        self.assertEqual(obj2._total, 150)

    def test_dunder_add_bad_other(self):
        obj = file_indexer.Histogram()

        result = obj.__add__('other')

        self.assertEqual(result, NotImplemented)

    def test_dunder_add_base(self):
        obj1 = file_indexer.Histogram()
        obj1._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj1._total = 150
        obj2 = file_indexer.Histogram()
        obj2._words.update({
            'word2': 20,
            'word4': 50,
            'word6': 80,
        })
        obj2._total = 150

        result = obj1 + obj2

        self.assertEqual(result._words, {
            'word1': 50,
            'word2': 60,
            'word3': 30,
            'word4': 70,
            'word5': 10,
            'word6': 80,
        })
        self.assertEqual(result._total, 300)
        self.assertEqual(obj1._words, {
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        self.assertEqual(obj1._total, 150)
        self.assertEqual(obj2._words, {
            'word2': 20,
            'word4': 50,
            'word6': 80,
        })
        self.assertEqual(obj2._total, 150)

    def test_add(self):
        obj = file_indexer.Histogram()

        obj.add('SpAm')
        obj.add('sPaM')
        obj.add('spam')
        obj.add('spammER')

        self.assertEqual(obj._words, {
            'spam': 3,
            'spammer': 1,
        })
        self.assertEqual(obj._total, 4)

    def test_top_words_too_few(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj._total = 150

        result = obj.top_words()  # default word count is 10

        self.assertEqual(result, [
            ('word1', 50),
            ('word2', 40),
            ('word3', 30),
            ('word4', 20),
            ('word5', 10),
        ])

    def test_top_words_exact_count(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj._total = 150

        result = obj.top_words(5)

        self.assertEqual(result, [
            ('word1', 50),
            ('word2', 40),
            ('word3', 30),
            ('word4', 20),
            ('word5', 10),
        ])

    def test_top_words_small_count(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj._total = 150

        result = obj.top_words(4)

        self.assertEqual(result, [
            ('word1', 50),
            ('word2', 40),
            ('word3', 30),
            ('word4', 20),
        ])

    def test_top_words_small_count_with_tie(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 40,
            'word4': 40,
            'word5': 10,
        })
        obj._total = 150

        result = obj.top_words(3)

        self.assertEqual(result, [
            ('word1', 50),
            ('word4', 40),  # words will be lexicographically sorted
            ('word3', 40),
            ('word2', 40),
        ])

    def test_total_words(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj._total = 150

        self.assertEqual(obj.total_words, 150)

    def test_distinct_words(self):
        obj = file_indexer.Histogram()
        obj._words.update({
            'word1': 50,
            'word2': 40,
            'word3': 30,
            'word4': 20,
            'word5': 10,
        })
        obj._total = 150

        self.assertEqual(obj.distinct_words, 5)


class HistogramFromFileTest(unittest.TestCase):
    @mock.patch.object(sys, 'stdin', make_fh())
    @mock.patch.object(file_indexer, 'open', return_value=make_fh())
    @mock.patch.object(file_indexer, 'tokenize',
                       return_value=['one', 'two', 'three'])
    @mock.patch.object(file_indexer.Histogram, '__init__', return_value=None)
    @mock.patch.object(file_indexer.Histogram, 'add')
    def test_stdin(self, mock_add, mock_init, mock_tokenize, mock_open):
        result = file_indexer.histogram_from_file()

        self.assertIsInstance(result, file_indexer.Histogram)
        mock_init.assert_called_once_with()
        self.assertFalse(mock_open.called)
        mock_tokenize.assert_called_once_with(sys.stdin)
        mock_add.assert_has_calls([
            mock.call('one'),
            mock.call('two'),
            mock.call('three'),
        ])
        self.assertEqual(mock_add.call_count, 3)
        self.assertFalse(sys.stdin.__exit__.called)

    @mock.patch.object(sys, 'stdin', make_fh())
    @mock.patch.object(file_indexer, 'open', return_value=make_fh())
    @mock.patch.object(file_indexer, 'tokenize',
                       return_value=['one', 'two', 'three'])
    @mock.patch.object(file_indexer.Histogram, '__init__', return_value=None)
    @mock.patch.object(file_indexer.Histogram, 'add')
    def test_name(self, mock_add, mock_init, mock_tokenize, mock_open):
        result = file_indexer.histogram_from_file('fname')

        self.assertIsInstance(result, file_indexer.Histogram)
        mock_init.assert_called_once_with()
        mock_open.assert_called_once_with('fname')
        mock_tokenize.assert_called_once_with(mock_open.return_value)
        mock_add.assert_has_calls([
            mock.call('one'),
            mock.call('two'),
            mock.call('three'),
        ])
        self.assertEqual(mock_add.call_count, 3)
        mock_open.return_value.__exit__.assert_called_once_with(
            None, None, None)


class MainTest(unittest.TestCase):
    def make_results(self, file_cnt=5):
        result = [file_indexer.Histogram() for i in range(file_cnt)]
        for hist in result:
            hist._words.update({
                'word1': 50,
                'word2': 40,
                'word3': 30,
                'word4': 20,
                'word5': 10,
            })
            hist._total = 150

        return result

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_base(self, mock_from_file, mock_Pool, mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = []
        mock_from_file.side_effect = self.make_results()

        file_indexer.main(files, out)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 250\n'
                         '    word2: 200\n'
                         '    word3: 150\n'
                         '    word4: 100\n'
                         '    word5: 50\n')
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        mock_from_file.assert_has_calls([mock.call(fname) for fname in files])
        self.assertEqual(mock_from_file.call_count, len(files))

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_percentage(self, mock_from_file, mock_Pool, mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = []
        mock_from_file.side_effect = self.make_results()

        file_indexer.main(files, out, percentages=True)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 33.33%\n'
                         '    word2: 26.67%\n'
                         '    word3: 20.00%\n'
                         '    word4: 13.33%\n'
                         '    word5: 6.67%\n')
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        mock_from_file.assert_has_calls([mock.call(fname) for fname in files])
        self.assertEqual(mock_from_file.call_count, len(files))

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_multi_stdin(self, mock_from_file, mock_Pool, mock_cpu_count):
        files = ['file0', '-', 'file2', '-', 'file4']
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = []
        mock_from_file.side_effect = self.make_results()

        self.assertRaises(ValueError, file_indexer.main, files, out)
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        self.assertFalse(mock_from_file.called)

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_with_stdin(self, mock_from_file, mock_Pool, mock_cpu_count):
        files = ['file0', '-', 'file2', 'file3', 'file4']
        expected = ['file0', None, 'file2', 'file3', 'file4']
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = []
        mock_from_file.side_effect = self.make_results()

        file_indexer.main(files, out)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 250\n'
                         '    word2: 200\n'
                         '    word3: 150\n'
                         '    word4: 100\n'
                         '    word5: 50\n')
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        mock_from_file.assert_has_calls([mock.call(fname)
                                         for fname in expected])
        self.assertEqual(mock_from_file.call_count, len(expected))

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_noninteger_workers(self, mock_from_file, mock_Pool,
                                mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = self.make_results()
        mock_from_file.side_effect = lambda x: file_indexer.Histogram()

        self.assertRaises(ValueError, file_indexer.main, files, out,
                          workers='workers')
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        self.assertFalse(mock_from_file.called)

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_negative_workers(self, mock_from_file, mock_Pool, mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = self.make_results()
        mock_from_file.side_effect = lambda x: file_indexer.Histogram()

        self.assertRaises(ValueError, file_indexer.main, files, out,
                          workers=-1)
        self.assertFalse(mock_cpu_count.called)
        self.assertFalse(mock_Pool.called)
        self.assertFalse(mock_from_file.called)

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_workers_cpu_count(self, mock_from_file, mock_Pool,
                               mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = self.make_results()
        mock_from_file.side_effect = lambda x: file_indexer.Histogram()

        file_indexer.main(files, out, workers=0)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 250\n'
                         '    word2: 200\n'
                         '    word3: 150\n'
                         '    word4: 100\n'
                         '    word5: 50\n')
        mock_cpu_count.assert_called_once_with()
        mock_Pool.assert_called_once_with(2)
        mock_Pool.return_value.map.assert_called_once_with(
            file_indexer.histogram_from_file, files)
        self.assertFalse(mock_from_file.called)

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       side_effect=NotImplementedError())
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_workers_cpu_count_unimplemented(self, mock_from_file, mock_Pool,
                                             mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = self.make_results()
        mock_from_file.side_effect = lambda x: file_indexer.Histogram()

        file_indexer.main(files, out, workers=0)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 250\n'
                         '    word2: 200\n'
                         '    word3: 150\n'
                         '    word4: 100\n'
                         '    word5: 50\n')
        mock_cpu_count.assert_called_once_with()
        mock_Pool.assert_called_once_with(4)
        mock_Pool.return_value.map.assert_called_once_with(
            file_indexer.histogram_from_file, files)
        self.assertFalse(mock_from_file.called)

    @mock.patch.object(file_indexer.multiprocessing, 'cpu_count',
                       return_value=2)
    @mock.patch.object(file_indexer.multiprocessing, 'Pool')
    @mock.patch.object(file_indexer, 'histogram_from_file')
    def test_workers_specified(self, mock_from_file, mock_Pool,
                               mock_cpu_count):
        files = ['file%d' % i for i in range(5)]
        out = six.StringIO()
        mock_Pool.return_value.map.return_value = self.make_results()
        mock_from_file.side_effect = lambda x: file_indexer.Histogram()

        file_indexer.main(files, out, workers=7)

        self.assertEqual(out.getvalue(),
                         'Total number of words: 750\n'
                         'Total distinct words: 5\n'
                         '\n'
                         'Top 5 word(s):\n'
                         '    word1: 250\n'
                         '    word2: 200\n'
                         '    word3: 150\n'
                         '    word4: 100\n'
                         '    word5: 50\n')
        self.assertFalse(mock_cpu_count.called)
        mock_Pool.assert_called_once_with(7)
        mock_Pool.return_value.map.assert_called_once_with(
            file_indexer.histogram_from_file, files)
        self.assertFalse(mock_from_file.called)


class ProcessorTest(unittest.TestCase):
    @mock.patch.object(sys, 'stdout')
    @mock.patch.object(file_indexer, 'open')
    def test_no_output(self, mock_open, mock_stdout):
        args = argparse.Namespace(output='')

        gen = file_indexer._processor(args)
        six.next(gen)

        self.assertFalse(mock_open.called)
        self.assertEqual(args.out, mock_stdout)
        self.assertFalse(mock_stdout.close.called)
        self.assertFalse(mock_open.return_value.close.called)

        self.assertRaises(StopIteration, six.next, gen)

        self.assertFalse(mock_stdout.close.called)
        self.assertFalse(mock_open.return_value.close.called)

    @mock.patch.object(sys, 'stdout')
    @mock.patch.object(file_indexer, 'open')
    def test_dash_output(self, mock_open, mock_stdout):
        args = argparse.Namespace(output='-')

        gen = file_indexer._processor(args)
        six.next(gen)

        self.assertFalse(mock_open.called)
        self.assertEqual(args.out, mock_stdout)
        self.assertFalse(mock_stdout.close.called)
        self.assertFalse(mock_open.return_value.close.called)

        self.assertRaises(StopIteration, six.next, gen)

        self.assertFalse(mock_stdout.close.called)
        self.assertFalse(mock_open.return_value.close.called)

    @mock.patch.object(sys, 'stdout')
    @mock.patch.object(file_indexer, 'open')
    def test_file_output(self, mock_open, mock_stdout):
        args = argparse.Namespace(output='file')

        gen = file_indexer._processor(args)
        six.next(gen)

        mock_open.assert_called_once_with('file', 'w')
        self.assertEqual(args.out, mock_open.return_value)
        self.assertFalse(mock_stdout.close.called)
        self.assertFalse(mock_open.return_value.close.called)

        self.assertRaises(StopIteration, six.next, gen)

        self.assertFalse(mock_stdout.close.called)
        mock_open.return_value.close.assert_called_once_with()
