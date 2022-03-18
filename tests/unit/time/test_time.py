#!/usr/bin/env python
# coding: utf-8

# Copyright (c) "Neo4j"
# Neo4j Sweden AB [http://neo4j.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from datetime import time
from decimal import Decimal
import itertools
import operator

import pytest
from pytz import (
    timezone,
    FixedOffset,
    utc,
)

from neo4j.time import Time
from neo4j.time.arithmetic import (
    nano_add,
    nano_div,
)


timezone_us_eastern = timezone("US/Eastern")
timezone_utc = timezone("UTC")


def seconds_options(seconds, nanoseconds):
    yield seconds, nanoseconds
    yield seconds + nanoseconds / 1000000000,


class TestTime:

    def test_bad_attribute(self):
        t = Time(12, 34, 56.789)
        with pytest.raises(AttributeError):
            _ = t.x

    def test_simple_time(self):
        t = Time(12, 34, 56.789)
        assert t.hour_minute_second == (12, 34, Decimal("56.789"))
        assert t.hour_minute_second_nanosecond == (12, 34, 56, 789000000)
        assert t.ticks == 45296.789
        assert t.hour == 12
        assert t.minute == 34
        assert t.second == Decimal("56.789")

    def test_midnight(self):
        t = Time(0, 0, 0)
        assert t.hour_minute_second == (0, 0, 0)
        assert t.ticks == 0
        assert t.hour == 0
        assert t.minute == 0
        assert t.second == 0

    def test_nanosecond_precision(self):
        t = Time(12, 34, 56.789123456)
        assert t.hour_minute_second == (12, 34, Decimal("56.789123456"))
        assert t.ticks == 45296.789123456
        assert t.hour == 12
        assert t.minute == 34
        assert t.second == Decimal("56.789123456")

    def test_str(self):
        t = Time(12, 34, 56, 789123456)
        assert str(t) == "12:34:56.789123456"

    def test_now_without_tz(self):
        t = Time.now()
        assert isinstance(t, Time)

    def test_now_with_tz(self):
        t = Time.now(tz=timezone_us_eastern)
        assert isinstance(t, Time)
        assert t.tzinfo == timezone_us_eastern

    def test_utc_now(self):
        t = Time.utc_now()
        assert isinstance(t, Time)

    def test_from_native(self):
        native = time(12, 34, 56, 789123)
        t = Time.from_native(native)
        assert t.hour == native.hour
        assert t.minute == native.minute
        assert t.second == \
               Decimal(native.second) + Decimal(native.microsecond) / 1000000

    def test_to_native(self):
        t = Time(12, 34, 56.789123456)
        native = t.to_native()
        assert t.hour == native.hour
        assert t.minute == native.minute
        assert 56.789123 == nano_add(native.second, nano_div(native.microsecond, 1000000))

    def test_iso_format(self):
        t = Time(12, 34, 56, 789123456)
        assert "12:34:56.789123456" == t.iso_format()

    def test_iso_format_with_trailing_zeroes(self):
        t = Time(12, 34, 56, 789000000)
        assert "12:34:56.789000000" == t.iso_format()

    def test_iso_format_with_leading_zeroes(self):
        t = Time(12, 34, 56, 789)
        assert "12:34:56.000000789" == t.iso_format()

    def test_from_iso_format_hour_only(self):
        expected = Time(12, 0, 0)
        actual = Time.from_iso_format("12")
        assert expected == actual

    def test_from_iso_format_hour_and_minute(self):
        expected = Time(12, 34, 0)
        actual = Time.from_iso_format("12:34")
        assert expected == actual

    def test_from_iso_format_hour_minute_second(self):
        expected = Time(12, 34, 56)
        actual = Time.from_iso_format("12:34:56")
        assert expected == actual

    def test_from_iso_format_hour_minute_second_milliseconds(self):
        expected = Time(12, 34, 56, 123000000)
        actual = Time.from_iso_format("12:34:56.123")
        assert expected == actual

    def test_from_iso_format_hour_minute_second_microseconds(self):
        expected = Time(12, 34, 56, 123456000)
        actual = Time.from_iso_format("12:34:56.123456")
        assert expected == actual

    def test_from_iso_format_hour_minute_second_nanosecond(self):
        expected = Time(12, 34, 56, 123456789)
        actual = Time.from_iso_format("12:34:56.123456789")
        assert expected == actual

    def test_from_iso_format_with_positive_tz(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(754))
        actual = Time.from_iso_format("12:34:56.123456789+12:34")
        assert expected == actual

    def test_from_iso_format_with_negative_tz(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(-754))
        actual = Time.from_iso_format("12:34:56.123456789-12:34")
        assert expected == actual

    def test_from_iso_format_with_positive_long_tz(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(754))
        actual = Time.from_iso_format("12:34:56.123456789+12:34:56.123456")
        assert expected == actual

    def test_from_iso_format_with_negative_long_tz(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(-754))
        actual = Time.from_iso_format("12:34:56.123456789-12:34:56.123456")
        assert expected == actual

    def test_from_iso_format_with_hour_only_tz(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(120))
        actual = Time.from_iso_format("12:34:56.123456789+02:00")
        assert expected == actual

    def test_utc_offset_fixed(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(-754))
        actual = -754 * 60
        assert expected.utc_offset().total_seconds() == actual

    def test_utc_offset_variable(self):
        expected = Time(12, 34, 56, 123456789, tzinfo=FixedOffset(-754))
        actual = -754 * 60
        assert expected.utc_offset().total_seconds() == actual

    def test_iso_format_with_time_zone_case_1(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_iso_format_with_time_zone_case_1
        expected = Time(7, 54, 2, 129790999, tzinfo=timezone_utc)
        assert expected.iso_format() == "07:54:02.129790999+00:00"
        assert expected.tzinfo == FixedOffset(0)
        actual = Time.from_iso_format("07:54:02.129790999+00:00")
        assert expected == actual

    def test_iso_format_with_time_zone_case_2(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_iso_format_with_time_zone_case_2
        expected = Time.from_iso_format("07:54:02.129790999+01:00")
        assert expected.tzinfo == FixedOffset(60)
        assert expected.iso_format() == "07:54:02.129790999+01:00"

    def test_to_native_case_1(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_to_native_case_1
        t = Time(12, 34, 56, 789123456)
        native = t.to_native()
        assert native.hour == t.hour
        assert native.minute == t.minute
        assert nano_add(native.second, nano_div(native.microsecond, 1000000)) \
               == 56.789123
        assert native.tzinfo is None
        assert native.isoformat() == "12:34:56.789123"

    def test_to_native_case_2(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_to_native_case_2
        t = Time(12, 34, 56, 789123456, tzinfo=timezone_utc)
        native = t.to_native()
        assert native.hour == t.hour
        assert native.minute == t.minute
        assert nano_add(native.second, nano_div(native.microsecond, 1000000)) \
               == 56.789123
        assert native.tzinfo == FixedOffset(0)
        assert native.isoformat() == "12:34:56.789123+00:00"

    def test_from_native_case_1(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_from_native_case_1
        native = time(12, 34, 56, 789123)
        t = Time.from_native(native)
        assert t.hour == native.hour
        assert t.minute == native.minute
        assert t.second == Decimal(native.microsecond) / 1000000 + native.second
        assert t.tzinfo is None

    def test_from_native_case_2(self):
        # python -m pytest tests/unit/time/test_time.py -s -v -k test_from_native_case_2
        native = time(12, 34, 56, 789123, FixedOffset(0))
        t = Time.from_native(native)
        assert t.hour == native.hour
        assert t.minute == native.minute
        assert t.second == Decimal(native.microsecond) / 1000000 + native.second
        assert t.tzinfo == FixedOffset(0)

    @pytest.mark.parametrize(("t1", "t2"), (
        (time(12, 34, 56, 789123), Time(12, 34, 56, 789123000)),
        (Time(12, 34, 56, 789123456), Time(12, 34, 56, 789123456)),
        (
            time(12, 34, 56, 789123, FixedOffset(1)),
            Time(12, 34, 56, 789123000, FixedOffset(1))
        ),
        (
            time(12, 34, 56, 789123, FixedOffset(-1)),
            Time(12, 34, 56, 789123000, FixedOffset(-1))
        ),
        (
            Time(12, 34, 56, 789123456, FixedOffset(1)),
            Time(12, 34, 56, 789123456, FixedOffset(1))
        ),
        (
            Time(12, 34, 56, 789123456, FixedOffset(-1)),
            Time(12, 34, 56, 789123456, FixedOffset(-1))
        ),
        (
            Time(12, 35, 56, 789123456, FixedOffset(1)),
            Time(12, 34, 56, 789123456, FixedOffset(0))
        ),
        (
            # Not testing our library directly, but asserting that Python's
            # time implementation is aligned with ours.
            time(12, 35, 56, 789123, FixedOffset(1)),
            time(12, 34, 56, 789123, FixedOffset(0))
        ),
        (
            time(12, 35, 56, 789123, FixedOffset(1)),
            Time(12, 34, 56, 789123000, FixedOffset(0))
        ),
        (
            Time(12, 35, 56, 789123123, FixedOffset(1)),
            Time(12, 34, 56, 789123123, FixedOffset(0))
        ),
    ))
    def test_equality(self, t1, t2):
        assert t1 == t2
        assert t2 == t1
        assert t1 <= t2
        assert t2 <= t1
        assert t1 >= t2
        assert t2 >= t1

    @pytest.mark.parametrize(("t1", "t2"), (
        (time(12, 34, 56, 789123), Time(12, 34, 56, 789123001)),
        (time(12, 34, 56, 789123), Time(12, 34, 56, 789124000)),
        (time(12, 34, 56, 789123), Time(12, 34, 57, 789123000)),
        (time(12, 34, 56, 789123), Time(12, 35, 56, 789123000)),
        (time(12, 34, 56, 789123), Time(13, 34, 56, 789123000)),
        (Time(12, 34, 56, 789123456), Time(12, 34, 56, 789123450)),
        (Time(12, 34, 56, 789123456), Time(12, 34, 57, 789123456)),
        (Time(12, 34, 56, 789123456), Time(12, 35, 56, 789123456)),
        (Time(12, 34, 56, 789123456), Time(13, 34, 56, 789123456)),
        (
            time(12, 34, 56, 789123, FixedOffset(2)),
            Time(12, 34, 56, 789123000, FixedOffset(1))
        ),
        (
            time(12, 34, 56, 789123, FixedOffset(-2)),
            Time(12, 34, 56, 789123000, FixedOffset(-1))
        ),
        (
            time(12, 34, 56, 789123),
            Time(12, 34, 56, 789123000, FixedOffset(0))
        ),
        (
            Time(12, 34, 56, 789123456, FixedOffset(2)),
            Time(12, 34, 56, 789123456, FixedOffset(1))
        ),
        (
            Time(12, 34, 56, 789123456, FixedOffset(-2)),
            Time(12, 34, 56, 789123456, FixedOffset(-1))
        ),
        (
            Time(12, 34, 56, 789123456),
            Time(12, 34, 56, 789123456, FixedOffset(0))
        ),
        (
            Time(13, 34, 56, 789123456, FixedOffset(1)),
            Time(12, 34, 56, 789123456, FixedOffset(0))
        ),
        (
            Time(11, 34, 56, 789123456, FixedOffset(1)),
            Time(12, 34, 56, 789123456, FixedOffset(0))
        ),
    ))
    def test_inequality(self, t1, t2):
        assert t1 != t2
        assert t2 != t1

    @pytest.mark.parametrize(
        ("t1", "t2"),
        itertools.product(
            (
                time(12, 34, 56, 789123),
                Time(12, 34, 56, 789123000),
                time(12, 34, 56, 789123, FixedOffset(0)),
                Time(12, 34, 56, 789123456, FixedOffset(0)),
                time(12, 35, 56, 789123, FixedOffset(1)),
                Time(12, 35, 56, 789123456, FixedOffset(1)),
                time(12, 34, 56, 789123, FixedOffset(-1)),
                Time(12, 34, 56, 789123456, FixedOffset(-1)),
                time(12, 34, 56, 789123, FixedOffset(60 * -16)),
                Time(12, 34, 56, 789123000, FixedOffset(60 * -16)),
                time(11, 34, 56, 789123, FixedOffset(60 * -17)),
                Time(11, 34, 56, 789123000, FixedOffset(60 * -17)),
                Time(12, 34, 56, 789123456, FixedOffset(60 * -16)),
                Time(11, 34, 56, 789123456, FixedOffset(60 * -17)),
            ),
            repeat=2
        )
    )
    def test_hashed_equality(self, t1, t2):
        if t1 == t2:
            s = {t1}
            assert t1 in s
            assert t2 in s
            s = {t2}
            assert t1 in s
            assert t2 in s
        else:
            s = {t1}
            assert t1 in s
            assert t2 not in s
            s = {t2}
            assert t1 not in s
            assert t2 in s

    @pytest.mark.parametrize(("t1", "t2"), (
        itertools.product(
            (
                time(12, 34, 56, 789123),
                Time(12, 34, 56, 789123000),
                Time(12, 34, 56, 789123001),
            ),
            repeat=2
        )
    ))
    @pytest.mark.parametrize("tz", (
        FixedOffset(0), FixedOffset(1), FixedOffset(-1), utc,
    ))
    @pytest.mark.parametrize("op", (
        operator.lt, operator.le, operator.gt, operator.ge,
    ))
    def test_comparison_with_only_one_naive_fails(self, t1, t2, tz, op):
        t1 = t1.replace(tzinfo=tz)
        with pytest.raises(TypeError, match="naive"):
            op(t1, t2)

    @pytest.mark.parametrize(
        ("t1", "t2"),
        itertools.product(
            (
                time(12, 34, 56, 789123),
                Time(12, 34, 56, 789123000),
                Time(12, 34, 56, 789123001),
            ),
            repeat=2
        )
    )
    @pytest.mark.parametrize("tz", (
        timezone("Europe/Paris"), timezone("Europe/Berlin"),
    ))
    @pytest.mark.parametrize("op", (
        operator.lt, operator.le, operator.gt, operator.ge,
    ))
    def test_comparison_with_one_naive_and_not_fixed_tz(self, t1, t2, tz, op):
        t1tz = t1.replace(tzinfo=tz)
        res = op(t1tz, t2)
        expected = op(t1, t2)
        assert res is expected

    @pytest.mark.parametrize(("t1", "t2"), (
        (time(12, 34, 56, 789123), time(12, 34, 56, 789124)),
        (Time(12, 34, 56, 789123000), time(12, 34, 56, 789124)),
        (time(12, 34, 56, 789123), Time(12, 34, 56, 789124000)),
        (Time(12, 34, 56, 789123000), Time(12, 34, 56, 789124000)),
        (
            time(12, 34, 56, 789123, FixedOffset(1)),
            time(12, 34, 56, 789124, FixedOffset(1)),
        ),
        (
            Time(12, 34, 56, 789123000, FixedOffset(1)),
            time(12, 34, 56, 789124, FixedOffset(1)),
        ),
        (
            Time(12, 34, 56, 789123000, FixedOffset(1)),
            Time(12, 34, 56, 789124000, FixedOffset(1)),
        ),
        (
            Time(12, 34, 56, 789123000, FixedOffset(1)),
            Time(12, 34, 56, 789123001, FixedOffset(1)),
        ),

        (
            time(12, 36, 56, 789123, FixedOffset(1)),
            time(12, 34, 56, 789124, FixedOffset(-1)),
        ),
        (
            Time(12, 36, 56, 789123000, FixedOffset(1)),
            time(12, 34, 56, 789124, FixedOffset(-1)),
        ),
        (
            Time(12, 36, 56, 789123000, FixedOffset(1)),
            Time(12, 34, 56, 789124000, FixedOffset(-1)),
        ),
        (
            Time(12, 36, 56, 789123000, FixedOffset(1)),
            Time(12, 34, 56, 789123001, FixedOffset(-1)),
        ),
    ))
    def test_comparison(self, t1, t2):
        assert t1 < t2
        assert not t2 < t1
        assert t1 <= t2
        assert not t2 <= t1
        assert t2 > t1
        assert not t1 > t2
        assert t2 >= t1
        assert not t1 >= t2
