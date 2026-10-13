"""Build the benchmark workspace template from a pinned click checkout.

The template is a fresh git repo (no upstream history, so `git log`/`git diff`
cannot reveal the injected bugs) with three injected bugs and the upstream
tests that would directly expose them removed (a realistic coverage gap).
The removed assertions live in grading/ as hidden tests.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream-click"
TEMPLATE = ROOT / "template"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        sys.exit(f"{path}: expected exactly one match for {old!r}, found {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    # Empty the directory rather than removing it: on Windows another process
    # may hold it as its working directory.
    TEMPLATE.mkdir(exist_ok=True)
    for child in TEMPLATE.iterdir():
        if child.is_dir():
            shutil.rmtree(child, onerror=lambda f, p, _: (Path(p).chmod(0o700), f(p)))
        else:
            child.unlink()
    shutil.copytree(UPSTREAM, TEMPLATE, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.egg-info"))
    src = TEMPLATE / "src" / "click"
    tests = TEMPLATE / "tests"

    # T1: IntRange clamps open bounds in the wrong direction.
    replace_once(src / "types.py", "            return bound\n\n        return bound + dir\n", "            return bound\n\n        return bound - dir\n")
    replace_once(tests / "test_types.py", '        (click.IntRange(0, min_open=True, clamp=True), "0", 1),\n', "")
    replace_once(tests / "test_types.py", '        (click.IntRange(max=5, max_open=True, clamp=True), "5", 4),\n', "")

    # T2: help output lists long options before short ones.
    replace_once(src / "formatting.py", "    rv.sort(key=lambda x: x[0])\n", "    rv.sort(key=lambda x: x[0], reverse=True)\n")
    opts = tests / "test_options.py"
    text = opts.read_text(encoding="utf-8")
    start = text.index("def test_option_help_preserve_paragraphs(runner):")
    end = text.index("def test_argument_custom_class(runner):")
    opts.write_text(text[:start] + text[end:], encoding="utf-8")
    replace_once(opts, '        (\n            ("-h", "--help"),\n            "  -h, --help  Show this message and exit.\\n",\n        ),\n', "")

    # T3: '#' inside completion input is treated as a comment.
    replace_once(src / "shell_completion.py", "    lex.whitespace_split = True\n    lex.commenters = \"\"\n", "    lex.whitespace_split = True\n")

    # T6: subcommands receive the parent's whole default_map instead of their own section.
    replace_once(src / "core.py", "            default_map = parent.default_map.get(info_name)\n", "            default_map = parent.default_map\n")
    cmds = tests / "test_commands.py"
    text = cmds.read_text(encoding="utf-8")
    for name, nxt in (("def test_default_maps(runner):", "@pytest.mark.parametrize("),
                      ("def test_group_add_command_name(runner):", "@pytest.mark.parametrize(")):
        start = text.index(name)
        text = text[:start] + text[text.index(nxt, start):]
    cmds.write_text(text, encoding="utf-8")
    replace_once(tests / "test_defaults.py",
                 '    result = runner.invoke(cli, ["foo"], default_map={"foo": {"name": True}})\n'
                 '    assert "True" in result.output\n\n'
                 '    result = runner.invoke(cli, ["foo", "--help"], default_map={"foo": {"name": True}})\n'
                 '    assert "default: name" in result.output\n', "")

    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                ["git", "-c", "user.name=bench", "-c", "user.email=bench@example.com", "commit", "-q", "-m", "Initial commit"]):
        subprocess.run(cmd, cwd=TEMPLATE, check=True)
    print(f"template ready: {TEMPLATE}")


if __name__ == "__main__":
    main()
