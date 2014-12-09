"""Tests for mool.common.utils.hive_reducer_shim."""
import common.utils.hive_reducer_shim as hive_reducer_shim

TEST_OUTPUT_KEY = 'key_count'


class _MemStdout(object):
    """In memory mockup of sys.stdout."""
    def __init__(self):
        """Initializer."""
        self.data = []

    def write(self, text):
        """Write api."""
        self.data.append(text)

    def get_value(self):
        """Get current value."""
        return ''.join(self.data)


class _TestReducer(object):
    """The test reducer class to drive the shim."""
    def __init__(self, lines, emitter):
        """Initializer."""
        self.key_columns = [0]
        self.reducer_shim = hive_reducer_shim.HiveReducerShim(
            self, lines, emitter)

    def get_key(self, row):
        """Get row key."""
        return [row[i] for i in self.key_columns]

    def do_reduce(self, key, rows):
        """Count the number of instances of every key."""
        self.reducer_shim.emit([key[0], len(list(rows))])


class _KeyCounterReducer():
    """A reducer that counts the number of keys.

    This reducer is used to verify that reducer classes do not need to
    enumerate through all rows passed to it.
    """
    def __init__(self, lines, emitter):
        """Initializer."""
        self.key_columns = [0]
        self.reducer_shim = hive_reducer_shim.HiveReducerShim(
            self, lines, emitter)
        self._count = 0

    def get_key(self, row):
        """Get row key."""
        return [row[i] for i in self.key_columns]

    def do_reduce(self, dummy, _):
        """Count the number of instances of every key."""
        self._count += 1

    def close(self):
        """Emits the count of keys at the end of the reducer phase."""
        self.reducer_shim.emit([TEST_OUTPUT_KEY, self._count])


def test_reducer():
    """Test reducer shim using _TestReducer implemnentation."""
    def _template(expected_out, mapper_output, test_reducer_class):
        """Template for test."""
        sorted_mapper_output = sorted(mapper_output)
        reducer_input = ['\t'.join([str(i) for i in x]) + '\n'
                         for x in sorted_mapper_output]
        writer = _MemStdout()
        test_reducer = test_reducer_class(reducer_input, writer)
        test_reducer.reducer_shim.process()
        expected_out = ['\t'.join([str(i) for i in x]) for x in expected_out]
        expected_out = '\n'.join(expected_out)
        if expected_out:
            expected_out += '\n'
        assert expected_out == writer.get_value()

    _template([], [], _TestReducer)
    _template([[0, 2], [1, 3], [2, 4]],
              [[0, 'a', 2], [0, 'b', 0], [1, 'c', 3], [1, 'd', 0],
               [1, 'e', 1], [2, 'f', 3], [2, 'g', 1], [2, 'h', 0],
               [2, 'i', 0]], _TestReducer)
    _template([[TEST_OUTPUT_KEY, 3]],
              [[0, 'a', 2], [0, 'b', 0], [1, 'c', 3], [1, 'd', 0],
               [1, 'e', 1], [2, 'f', 3], [2, 'g', 1], [2, 'h', 0],
               [2, 'i', 0]], _KeyCounterReducer)
