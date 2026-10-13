# click

Python CLI library. Source in `src/click/`, tests in `tests/` (pytest).

## Commands
- Run tests: `python -m pytest tests/<file>.py -q` (full suite: `python -m pytest -q`, ~10s)
- `PYTHONPATH` already points at `src/`; do not pip install anything.

## Module map
- `core.py` – Context, Command, Group, Parameter/Option/Argument, value resolution
- `types.py` – ParamType and built-in types (Choice, IntRange, Path, UUID…)
- `parser.py` – low-level argv parsing
- `formatting.py` – help text layout (HelpFormatter, join_options)
- `shell_completion.py` – completion classes, split_arg_string
- `decorators.py` – @command, @option, @argument
- `testing.py` – CliRunner

## Conventions
- New public names must be exported in `src/click/__init__.py`.
- Add or update a test next to related tests for every change.
- Keep changes minimal; do not reformat unrelated code.
