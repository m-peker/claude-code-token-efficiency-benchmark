import click
from click.testing import CliRunner


def test_exported():
    assert hasattr(click, "KeyValue")
    assert isinstance(click.KeyValue(), click.ParamType)


def test_convert():
    kv = click.KeyValue()
    assert kv.convert("name=alice", None, None) == ("name", "alice")
    assert kv.convert("url=http://x?a=b", None, None) == ("url", "http://x?a=b")
    assert kv.convert("empty=", None, None) == ("empty", "")


def test_cli_success_and_multiple():
    @click.command()
    @click.option("--set", "pairs", type=click.KeyValue(), multiple=True)
    def cmd(pairs):
        click.echo(repr(pairs))

    result = CliRunner().invoke(cmd, ["--set", "a=1", "--set", "b=2"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "(('a', '1'), ('b', '2'))"


def test_cli_failure():
    @click.command()
    @click.option("--set", "pair", type=click.KeyValue())
    def cmd(pair):
        pass

    for bad in ("novalue", "=value"):
        result = CliRunner().invoke(cmd, ["--set", bad])
        assert result.exit_code == 2
        assert "is not a valid key=value pair" in result.output
