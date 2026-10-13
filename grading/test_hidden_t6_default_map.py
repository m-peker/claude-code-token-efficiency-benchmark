import click
from click.testing import CliRunner


def test_default_maps():
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name", default="normal")
    def foo(name):
        click.echo(name)

    result = CliRunner().invoke(cli, ["foo"], default_map={"foo": {"name": "changed"}})
    assert not result.exception
    assert result.output == "changed\n"


def test_group_add_command_name():
    cli = click.Group("cli")
    cmd = click.Command("a", params=[click.Option(["-x"], required=True)])
    cli.add_command(cmd, "b")
    result = CliRunner().invoke(cli, ["b"], default_map={"b": {"x": 3}})
    assert result.exit_code == 0


def test_nested_groups():
    @click.group()
    def cli():
        pass

    @cli.group()
    def db():
        pass

    @db.command()
    @click.option("--retries", default=1, type=int)
    def sync(retries):
        click.echo(retries)

    result = CliRunner().invoke(cli, ["db", "sync"], default_map={"db": {"sync": {"retries": 5}}})
    assert result.output == "5\n"


def test_flag_default_map():
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option("--name/--no-name", is_flag=True, show_default=True, help="name flag")
    def foo(name):
        click.echo(name)

    result = CliRunner().invoke(cli, ["foo"], default_map={"foo": {"name": True}})
    assert "True" in result.output
    result = CliRunner().invoke(cli, ["foo", "--help"], default_map={"foo": {"name": True}})
    assert "default: name" in result.output
