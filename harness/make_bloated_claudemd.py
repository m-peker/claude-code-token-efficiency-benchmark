"""Generate the 'bloated' CLAUDE.md variant.

It mimics a common real-world pattern: the lean essentials buried under generic
engineering advice and documentation pasted in "so Claude knows everything".
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "template" / "docs"
OUT = Path(__file__).resolve().parent / "claudemd" / "bloated.md"

GENERIC = """
## Engineering principles (READ CAREFULLY, ALWAYS FOLLOW)
- Always think step by step before writing any code. Consider every edge case.
- Write clean, readable, maintainable, well-documented code following SOLID, DRY, KISS and YAGNI.
- Prefer composition over inheritance. Prefer pure functions. Avoid global state.
- Every function must have a docstring explaining parameters, return values and exceptions.
- Use type hints everywhere. Run mypy and pyright mentally before submitting.
- Never introduce breaking changes to the public API without a deprecation period.
- Follow PEP 8, PEP 257 and PEP 484. Lines must not exceed 88 characters.
- Be careful with Windows, macOS and Linux differences (paths, encodings, terminals).
- Consider Unicode, bytes vs str, and locale issues in every change.
- Consider performance implications; avoid quadratic algorithms on user input.
- Think about security: never use eval, never trust user input, validate everything.
- When fixing a bug, first reproduce it, then write a failing test, then fix it, then refactor.
- Keep pull requests small and focused. Write descriptive commit messages in the imperative mood.
- Update CHANGES.md for every user-visible change, under the unreleased version.
- Update the documentation in docs/ for every new feature or behavior change.
- Never leave commented-out code, debug prints, or TODOs without an issue number.
- Respect the existing code style even if you disagree with it.
- Be thorough: read related modules fully before changing anything.
- Double-check your work. Then check it again.
- If something is unclear, investigate the codebase extensively before asking.
"""

HISTORY = """
## Project history and context
Click was created by Armin Ronacher in 2014 as part of the Pallets projects, alongside Flask,
Jinja, Werkzeug, MarkupSafe and ItsDangerous. It was designed to support Flask's command line
interface and has since become one of the most popular CLI libraries in the Python ecosystem.
Version 7 dropped Python 2.6 support, version 8 dropped Python 2 entirely and introduced type
hints, shell completion rewrites, and a new parameter source tracking mechanism. Version 8.2
moved several parser internals, deprecated some parser classes, and refined flag handling.
Subsequent releases continued to modernize typing, tighten behavior around defaults and flags,
and improve the testing utilities. The project is maintained by volunteers; please be mindful of
their time and keep changes conservative and well-justified.
"""


def main() -> None:
    lean = (Path(__file__).resolve().parent / "claudemd" / "lean.md").read_text(encoding="utf-8")
    parts = [lean, GENERIC, HISTORY, "\n## Reference documentation (pasted from docs/)\n"]
    for name in ("quickstart.md", "parameters.md", "options.md"):
        parts.append(f"\n### docs/{name}\n\n" + (DOCS / name).read_text(encoding="utf-8"))
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"{OUT}: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
