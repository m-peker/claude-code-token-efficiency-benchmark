import click
from click.testing import CliRunner


def test_short_option_listed_first():
    @click.command()
    @click.option("--verbose", "-v", is_flag=True, help="Be loud.")
    def cmd(verbose):
        pass

    result = CliRunner().invoke(cmd, ["--help"])
    assert "  -v, --verbose  Be loud." in result.output


def test_help_option_custom_names():
    @click.command()
    @click.help_option("-h", "--help")
    def cmd():
        pass

    result = CliRunner().invoke(cmd, ["-h"])
    assert "  -h, --help  Show this message and exit.\n" in result.output


def test_option_help_preserve_paragraphs():
    @click.command()
    @click.option(
        "-C",
        "--config",
        type=click.Path(),
        help="""Configuration file to use.

        If not given, the environment variable CONFIG_FILE is consulted
        and used if set. If neither are given, a default configuration
        file is loaded.""",
    )
    def cmd(config):
        pass

    result = CliRunner().invoke(cmd, ["--help"])
    i = " " * 21
    assert (
        "  -C, --config PATH  Configuration file to use.\n"
        f"{i}\n"
        f"{i}If not given, the environment variable CONFIG_FILE is\n"
        f"{i}consulted and used if set. If neither are given, a default\n"
        f"{i}configuration file is loaded."
    ) in result.output
