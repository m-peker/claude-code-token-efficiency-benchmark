import pytest

from click.shell_completion import split_arg_string


@pytest.mark.parametrize(
    ("value", "expect"),
    [
        ("cmd a#b", ["cmd", "a#b"]),
        ("cmd #tag", ["cmd", "#tag"]),
        ("cmd 'x # y' z", ["cmd", "x # y", "z"]),
        ("example 'my file", ["example", "my file"]),
    ],
)
def test_split_arg_string_keeps_hash(value, expect):
    assert split_arg_string(value) == expect
