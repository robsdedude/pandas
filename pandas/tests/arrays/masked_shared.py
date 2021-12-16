"""
Tests shared by MaskedArray subclasses.
"""

import pandas as pd
import pandas._testing as tm
from pandas.tests.extension.base import BaseOpsUtil


class ComparisonOps(BaseOpsUtil):
    def _compare_other(self, data, op, other):

        # array
        result = pd.Series(op(data, other))
        expected = pd.Series(op(data._data, other), dtype="boolean")

        # fill the nan locations
        expected[data._mask] = pd.NA

        tm.assert_series_equal(result, expected)

        # series
        ser = pd.Series(data)
        result = op(ser, other)

        expected = op(pd.Series(data._data), other)

        # fill the nan locations
        expected[data._mask] = pd.NA
        expected = expected.astype("boolean")

        tm.assert_series_equal(result, expected)

    # subclass will override to parametrize 'other'
    def test_scalar(self, other, comparison_op, dtype):
        op = comparison_op
        left = pd.array([1, 0, None], dtype=dtype)

        result = op(left, other)

        if other is pd.NA:
            expected = pd.array([None, None, None], dtype="boolean")
        else:
            values = op(left._data, other)
            expected = pd.arrays.BooleanArray(values, left._mask, copy=True)
        tm.assert_extension_array_equal(result, expected)

        # ensure we haven't mutated anything inplace
        result[0] = pd.NA
        tm.assert_extension_array_equal(left, pd.array([1, 0, None], dtype=dtype))


class NumericOps:
    # Shared by IntegerArray and FloatingArray, not BooleanArray

    def test_no_shared_mask(self, data):
        result = data + 1
        assert not tm.shares_memory(result, data)

    def test_array(self, comparison_op, dtype):
        op = comparison_op

        left = pd.array([0, 1, 2, None, None, None], dtype=dtype)
        right = pd.array([0, 1, None, 0, 1, None], dtype=dtype)

        result = op(left, right)
        values = op(left._data, right._data)
        mask = left._mask | right._mask

        expected = pd.arrays.BooleanArray(values, mask)
        tm.assert_extension_array_equal(result, expected)

        # ensure we haven't mutated anything inplace
        result[0] = pd.NA
        tm.assert_extension_array_equal(
            left, pd.array([0, 1, 2, None, None, None], dtype=dtype)
        )
        tm.assert_extension_array_equal(
            right, pd.array([0, 1, None, 0, 1, None], dtype=dtype)
        )

    def test_compare_with_booleanarray(self, comparison_op, dtype):
        op = comparison_op

        left = pd.array([True, False, None] * 3, dtype="boolean")
        right = pd.array([0] * 3 + [1] * 3 + [None] * 3, dtype=dtype)
        other = pd.array([False] * 3 + [True] * 3 + [None] * 3, dtype="boolean")

        expected = op(left, other)
        result = op(left, right)
        tm.assert_extension_array_equal(result, expected)

        # reversed op
        expected = op(other, left)
        result = op(right, left)
        tm.assert_extension_array_equal(result, expected)

    def test_compare_to_string(self, dtype):
        # GH#28930
        ser = pd.Series([1, None], dtype=dtype)
        result = ser == "a"
        expected = pd.Series([False, pd.NA], dtype="boolean")

        self.assert_series_equal(result, expected)