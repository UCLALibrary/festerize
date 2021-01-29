import re

from click.testing import CliRunner

from festerize import festerize


def test_cli_help():
    """Tests the --help option."""
    result = CliRunner().invoke(festerize, ["--help"])

    assert result.exit_code == 0

    # There may be line breaks and indentation whitespace between the words.
    assert (
        re.search("with" + "\\s+" + "Universal" + "\\s+" + "Viewer", result.output)
        is not None
    )
    assert (
        re.search("with" + "\\s+" + "Mirador" + "\\s+" + "3", result.output) is not None
    )


def test_cli_version():
    """Tests the --version option."""
    result = CliRunner().invoke(festerize, ["--version"])

    assert result.exit_code == 0
    assert re.match("Festerize v", result.output) is not None
