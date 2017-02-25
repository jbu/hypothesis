# coding=utf-8
#
# This file is part of Hypothesis, which may be found at
# https://github.com/HypothesisWorks/hypothesis-python
#
# Most of this work is copyright (C) 2013-2016 David R. MacIver
# (david@drmaciver.com), but it contains contributions by others. See
# CONTRIBUTING.rst for a full list of people who may hold copyright, and
# consult the git log if you need to determine who owns an individual
# contribution.
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
#
# END HEADER

from __future__ import division, print_function, absolute_import

import numpy as np

import hypothesis.strategies as st
from hypothesis.errors import InvalidArgument
from hypothesis.searchstrategy import SearchStrategy
from hypothesis.internal.compat import hrange, text_type, binary_type


def from_dtype(dtype):
    if dtype.kind == u'b':
        result = st.booleans()
    elif dtype.kind == u'f':
        result = st.floats()
    elif dtype.kind == u'c':
        result = st.complex_numbers()
    elif dtype.kind in (u'S', u'a', u'V'):
        result = st.binary()
    elif dtype.kind == u'u':
        result = st.integers(
            min_value=0, max_value=1 << (4 * dtype.itemsize) - 1)
    elif dtype.kind == u'i':
        min_integer = -1 << (4 * dtype.itemsize - 1)
        result = st.integers(min_value=min_integer, max_value=-min_integer - 1)
    elif dtype.kind == u'U':
        result = st.text()
    else:
        raise InvalidArgument(u'No strategy inference for {}'.format(dtype))
    return result.map(dtype.type)


def check_argument(condition, fail_message, *f_args, **f_kwargs):
    if not condition:
        raise InvalidArgument(fail_message.format(*f_args, **f_kwargs))


def order_check(name, floor, small, large):
    if floor is None:
        floor = -np.inf
    if floor > small > large:
        check_argument(u'min_{name} was {}, must be at least {} and not more '
                       u'than max_{name} (was {})', small, floor, large,
                       name=name, condition=False)


class ArrayStrategy(SearchStrategy):

    def __init__(self, element_strategy, shape, dtype):
        self.shape = tuple(shape)
        assert shape
        self.array_size = np.prod(shape)
        self.dtype = dtype
        self.element_strategy = element_strategy

    def do_draw(self, data):
        result = np.empty(dtype=self.dtype, shape=self.array_size)
        for i in hrange(self.array_size):
            result[i] = self.element_strategy.do_draw(data)
        return result.reshape(self.shape)


def is_scalar(spec):
    return spec in (
        int, bool, text_type, binary_type, float, complex
    )


def arrays(dtype, shape, elements=None):
    if not isinstance(dtype, np.dtype):
        dtype = np.dtype(dtype)
    if elements is None:
        elements = from_dtype(dtype)
    if isinstance(shape, int):
        shape = (shape,)
    shape = tuple(shape)
    if not shape:
        if dtype.kind != u'O':
            return elements
    else:
        return ArrayStrategy(
            shape=shape,
            dtype=dtype,
            element_strategy=elements
        )


@st.defines_strategy
def array_shapes(min_dims=1, max_dims=3, min_side=1, max_side=10):
    """Return a strategy for array shapes (tuples of int >= 1)."""
    order_check('dims', 1, min_dims, max_dims)
    order_check('side', 1, min_side, max_side)
    return st.lists(st.integers(min_side, max_side),
                    min_size=min_dims, max_size=max_dims).map(tuple)
