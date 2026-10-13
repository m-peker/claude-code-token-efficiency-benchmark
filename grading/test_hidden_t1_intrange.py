import pytest

import click


@pytest.mark.parametrize(
    ("type", "value", "expect"),
    [
        (click.IntRange(0, min_open=True, clamp=True), "0", 1),
        (click.IntRange(max=5, max_open=True, clamp=True), "5", 4),
        (click.IntRange(0, 10, min_open=True, clamp=True), "-5", 1),
        (click.IntRange(0, 10, max_open=True, clamp=True), "99", 9),
        (click.IntRange(0, 10, clamp=True), "-5", 0),
    ],
)
def test_int_range_clamp_open(type, value, expect):
    assert type.convert(value, None, None) == expect
