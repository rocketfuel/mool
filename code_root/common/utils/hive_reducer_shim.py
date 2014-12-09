"""Hive reducer shim class.

This class can be used during hive mapper based map reduce jobs to split the
reducer input file into groups of separate keys.
"""
import itertools


def _hive_line_to_row(line):
    """Splits a row into list using tab delimiter."""
    if line.endswith('\n'):
        line = line[:-1]
    return line.split('\t')


class _HiveInputGenerator(object):
    """Build generator layer on top of hive input lines.

    This class slices the input lines and gives generator which in turn yields
    a generator of rows each for distinct keys in assuming sorted input.
    """
    def __init__(self, input_lines, reducer_obj):
        """Initializer."""
        self.input_lines = input_lines
        self.reducer_obj = reducer_obj
        self.current_key = None
        self.input_finished = False
        self.peeked_row = None
        self.input_row_generator = self._get_input_row_generator()

    def get_key_generator(self):
        """Yields generators for rows of each key."""
        def _keys_row_generator():
            """Yields a generator that moves over rows for one key."""
            while not self.input_finished:
                row = self._get_next_row()
                if not self.current_key:
                    self.current_key = self.reducer_obj.get_key(row)
                    yield row
                elif self.current_key == self.reducer_obj.get_key(row):
                    yield row
                else:
                    self.peeked_row = row
                    self.current_key = None
                    raise StopIteration()

        while not self.input_finished:
            current_keys_generator = _keys_row_generator()
            assert not self.current_key
            yield current_keys_generator
            # We need to consume any left over rows. This is needed so that we
            # don't call multiple reduce calls for same key.
            for dummy in current_keys_generator:
                pass

    def _get_input_row_generator(self):
        """Wraps the input as a generator.

        Yields a row from the input at a time.
        """
        for line in self.input_lines:
            yield _hive_line_to_row(line)
        self.input_finished = True

    def _get_next_row(self):
        """Returns the next row to be processed."""
        if self.peeked_row:
            row = self.peeked_row
            self.peeked_row = None
            return row
        else:
            return next(self.input_row_generator)


class HiveReducerShim(object):
    """Shim object for handling stdin based reducer semantics.

    The reducer_obj object is expected to support the following methods:
        def get_key(self, row):
            ...

        def do_reduce(self, key, rows):
            ...

        def do_close(): <optional>
            ...
    """
    def __init__(self, reducer_obj, lines, emitter):
        """Initializer."""
        self.reducer_obj = reducer_obj
        self.lines = lines
        self.emitter = emitter

    def process(self):
        """Applies reducer logic to a file of lines."""
        record_generator = _HiveInputGenerator(self.lines,
                                               self.reducer_obj)
        key_generator = record_generator.get_key_generator()
        for keys_row_generator in key_generator:
            # We need to peek the generator to get the key. This is done so
            # that we can maintain the normal API of reduce(key, values).
            try:
                row = next(keys_row_generator)
                key = record_generator.current_key
                self.reducer_obj.do_reduce(
                    key,
                    # Stitch back the peeked row to create the iterator to pass
                    # to the reducer object.
                    itertools.chain([row], keys_row_generator))
            except StopIteration:
                # This is a special case that should hit only if the input is
                # completely empty.
                pass
        # Implementing close is optional.
        if hasattr(self.reducer_obj, 'close'):
            self.reducer_obj.close()

    def emit(self, row):
        """Emit handler."""
        self.emitter.write('\t'.join([str(c) for c in row]) + '\n')
