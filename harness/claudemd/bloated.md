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

## Reference documentation (pasted from docs/)

### docs/quickstart.md

# Quickstart

```{currentmodule} click
```

## Install

Install from PyPI:

```console
pip install click
```

Installing into a virtual environment is highly recommended. We suggest {ref}`virtualenv-heading`.

## Examples

Some standalone examples of Click applications are packaged with Click. They are available in the
[examples folder](https://github.com/pallets/click/tree/main/examples) of the repo.

- [inout](https://github.com/pallets/click/tree/main/examples/inout) : A very simple example of an application that can
  read from files and write to files and also accept input from stdin or write to stdout.
- [validation](https://github.com/pallets/click/tree/main/examples/validation) : A simple example of an application that
  performs custom validation of parameters in different ways.
- [naval](https://github.com/pallets/click/tree/main/examples/naval) : Port of the [docopt](http://docopt.org/) naval
  example.
- [colors](https://github.com/pallets/click/tree/main/examples/colors) : A simple example that colorizes text.
- [aliases](https://github.com/pallets/click/tree/main/examples/aliases) : An advanced example that implements
  {ref}`aliases`.
- [imagepipe](https://github.com/pallets/click/tree/main/examples/imagepipe) : A complex example that implements some
  {ref}`command-pipelines` . It chains together image processing instructions. Requires pillow.
- [repo](https://github.com/pallets/click/tree/main/examples/repo) : An advanced example that implements a
  Git-/Mercurial-like command line interface.
- [complex](https://github.com/pallets/click/tree/main/examples/complex) : A very advanced example that implements
  loading subcommands dynamically from a plugin folder.
- [termui](https://github.com/pallets/click/tree/main/examples/termui) : A simple example that showcases terminal UI
  helpers provided by click.

## Basic Concepts - Creating a Command

Click is based on declaring commands through decorators. Internally, there is a non-decorator interface for advanced use
cases, but it's discouraged for high-level usage.

A function becomes a Click command line tool by decorating it through {func}`command`. At its simplest, just
decorating a function with this decorator will make it into a callable script:


```{eval-rst}
.. click:example::
    import click

    @click.command()
    def hello():
        click.echo('Hello World!')

What's happening is that the decorator converts the function into a :class:`Command` which then can be invoked:

.. click:example::
    if __name__ == '__main__':
        hello()

And what it looks like:

.. click:run::
    invoke(hello, args=[], prog_name='python hello.py')

And the corresponding help page:

.. click:run::
    invoke(hello, args=['--help'], prog_name='python hello.py')
```

## Echoing

Why does this example use {func}`echo` instead of the regular {func}`print` function? The answer to this question is
that Click attempts to support different environments consistently and to be very robust even when the environment is
misconfigured. Click wants to be functional at least on a basic level even if everything is completely broken.

What this means is that the {func}`echo` function applies some error correction in case the terminal is misconfigured
instead of dying with a {exc}`UnicodeError`.

The echo function also supports color and other styles in output. It will automatically remove styles if the output
stream is a file. See {ref}`ansi-colors`.

If you don't need this, you can also use the `print()` construct / function.

## Nesting Commands

Commands can be attached to other commands of type {class}`Group`. This allows arbitrary nesting of scripts. As an
example here is a script that implements two commands for managing databases:

```{eval-rst}
.. click:example::
    @click.group()
    def cli():
        pass

    @click.command()
    def initdb():
        click.echo('Initialized the database')

    @click.command()
    def dropdb():
        click.echo('Dropped the database')

    cli.add_command(initdb)
    cli.add_command(dropdb)
```

As you can see, the {func}`group` decorator works like the {func}`command` decorator, but creates a {class}`Group`
object instead which can be given multiple subcommands that can be attached with {meth}`Group.add_command`.

For simple scripts, it's also possible to automatically attach and create a command by using the {meth}`Group.command`
decorator instead. The above script can instead be written like this:

```{eval-rst}
.. click:example::
    @click.group()
    def cli():
        pass

    @cli.command()
    def initdb():
        click.echo('Initialized the database')

    @cli.command()
    def dropdb():
        click.echo('Dropped the database')

You would then invoke the :class:`Group` in your entry points or other invocations:

.. click:example::
    if __name__ == '__main__':
        cli()
```

## Registering Commands Later

Instead of using the `@group.command()` decorator, commands can be decorated with the plain `@command()` decorator
and registered with a group later with `group.add_command()`. This could be used to split commands into multiple Python
modules.

```{code-block} python
@click.command()
def greet():
    click.echo("Hello, World!")
```

```{code-block} python
@click.group()
def group():
    pass

group.add_command(greet)
```

## Adding Parameters

To add parameters, use the {func}`option` and {func}`argument` decorators:

```{eval-rst}
.. click:example::
    @click.command()
    @click.option('--count', default=1, help='number of greetings')
    @click.argument('name')
    def hello(count, name):
        for x in range(count):
            click.echo(f"Hello {name}!")

What it looks like:

.. click:run::
    invoke(hello, args=['--help'], prog_name='python hello.py')
```

## Switching to Entry Points

In the code you wrote so far there is a block at the end of the file which looks like this:
`if __name__ == '__main__':`. This is traditionally how a standalone Python file looks like. With Click you can continue
doing that, but a better way is to package your app with an entry point.

There are two main (and many more) reasons for this:

The first one is that installers automatically generate executable wrappers for Windows so your command line utilities
work on Windows too.

The second reason is that entry point scripts work with virtualenv on Unix without the virtualenv having to be
activated. This is a very useful concept which allows you to bundle your scripts with all requirements into a
virtualenv.

Click is perfectly equipped to work with that and in fact the rest of the documentation will assume that you are writing
applications as distributed packages.

Look at the {doc}`entry-points` chapter before reading the rest as the examples assume that you will be using entry
points.

### docs/parameters.md

(parameters)=

# Parameters

```{currentmodule} click
```

Click supports only two principle types of parameters for scripts (by design): options and arguments.

## Options

- Are optional.
- Recommended to use for everything except subcommands, urls, or files.
- Can take a fixed number of arguments. The default is 1. They may be specified multiple times using {ref}`multiple-options`.
- Are fully documented by the help page.
- Have automatic prompting for missing input.
- Can act as flags (boolean or otherwise).
- Can be pulled from environment variables.

## Arguments

- Are optional within reason, but not entirely so.
- Recommended to use for subcommands, urls, or files.
- Can take an arbitrary number of arguments.
- Are not fully documented by the help page since they may be too specific to be automatically documented. For more see {ref}`documenting-arguments`.
- Can be pulled from environment variables but only explicitly named ones. For more see {ref}`environment-variables`.

On each principle type you can specify {ref}`parameter-types`. Specifying these types helps Click add details to your help pages and help with the handling of those types.

(parameter-names)=

## Parameter Names

Parameters (options and arguments) have a name that will be used as
the Python argument name when calling the decorated function with
values.

In the example, the argument's name is `filename`. The name must match the python arg name. To provide a different name for use in help text, see {ref}`doc-meta-variables`.
The option's names are `-t` and `--times`. More names are available for options and are covered in {ref}`options`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.argument('filename')
    @click.option('-t', '--times', type=int)
    def multi_echo(filename, times):
        """Print value filename multiple times."""
        for x in range(times):
            click.echo(filename)

.. click:run::

    invoke(multi_echo, ['--times=3', 'index.txt'], prog_name='multi_echo')
```

### docs/options.md

(options)=

# Options

```{eval-rst}
.. currentmodule:: click
```

Adding options to commands can be accomplished with the {func}`option`
decorator. At runtime the decorator invokes the {class}`Option` class. Options
in Click are distinct from {ref}`positional arguments <arguments>`.

Useful and often used kwargs are:

- `default`: Passes a default.
- `help`: Sets help message.
- `nargs`: Sets the number of arguments.
- `required`: Makes option required.
- `type`: Sets {ref}`parameter type <parameter-types>`

```{contents}
:depth: 2
:local: true
```

## Option Decorator

The {func}`option()` decorator is usually passed two positional arguments: the
option name and the decorated function argument name.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo', 'string_to_echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)


.. click:run::

    invoke(echo, args=['--help'])
```

However, if the decorated function argument name is not passed in, then Click
will try to infer it. A simple way to name the option so that Click will infer
it correctly is by taking the function argument, adding two dashes to the front
and converting underscores to dashes.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--string-to-echo')
    def echo(string_to_echo):
        click.echo(string_to_echo)

.. click:run::

    invoke(echo, args=['--string-to-echo', 'Hi!'])
```

More formally, Click will try to infer the decorated function argument name as
follows:

1. If a positional argument is a valid [Python identifier](https://docs.python.org/3/reference/lexical_analysis.html#identifiers) (and thus does not have dashes), it is chosen.
2. If multiple positional arguments are prefixed with `--`, the first one
  declared is chosen.
3. Otherwise, the first positional argument prefixed with `-` is chosen.

To get the argument name, the chosen positional argument is converted to lower
case, a leading `-` or `--` is removed if found, and any remaining `-`
characters are replaced with `_`.

```{eval-rst}
.. list-table:: Examples
    :widths: 15 15
    :header-rows: 1

    * - Decorator Arguments
      - Inferred Argument Name
    * - ``"-f", "--foo-bar"``
      - foo_bar
    * - ``"-x"``
      - x
    * - ``"-f", "--filename", "dest"``
      - dest
    * - ``"--CamelCase"``
      - camelcase
    * - ``"-f", "-fb"``
      - f
    * - ``"--f", "--foo-bar"``
      - f
    * - ``"---f"``
      - _f
```

## Basic Example

A simple {class}`click.Option` takes one option name. By default, it's assumed
that the decorated function argument is not required and the expected type is
`str`. If the decorated function takes a positional argument but the option is
not passed with the command, then `None` is passed.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--text')
    def print_this(text):
        click.echo(text)


.. click:run::

    invoke(print_this, args=['--text=this'])

    invoke(print_this, args=[])


.. click:run::

    invoke(print_this, args=['--help'])

```

## Setting a Default

Instead of setting the `type`, you may set a default and Click will try to infer
the type.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--n', default=1)
    def dots(n):
        click.echo('.' * n)

.. click:run::

    invoke(dots, args=['--help'])
```

## Multi Value Options

To make an option take multiple values, pass in `nargs`. Note you may pass in
any positive integer, but not -1. The values are passed to the decorated
function as a tuple.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--pos', nargs=2, type=float)
    def findme(pos):
        a, b = pos
        click.echo(f"{a} / {b}")

.. click:run::

    invoke(findme, args=['--pos', '2.0', '3.0'])

```

(tuple-type)=

## Multi Value Options as Tuples

```{versionadded} 4.0
```

By setting `nargs` to a specific number, each item in
the resulting tuple is of the same type. Alternatively, you might want to use
different types for different indexes in
the tuple. For this you can directly specify a tuple as `type`:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', type=(str, int))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")


And on the command line:

.. click:run::

    invoke(putitem, args=['--item', 'peter', '1338'])
```

By using a tuple literal as the `type`, `nargs` gets automatically set to the
length of the tuple and the {class}`click.Tuple` type is automatically
used. The above example is thus equivalent to this:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--item', nargs=2, type=click.Tuple([str, int]))
    def putitem(item):
        name, id = item
        click.echo(f"name={name} id={id}")
```

(multiple-options)=

## Multiple Options

The multiple options format allows options to take an arbitrary number of
arguments (which is called variadic). The arguments are passed to the decorated
function as a tuple. If set, `default` must be a list or tuple. Setting a string
as `default` will be interpreted as a list of characters.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--message', '-m', multiple=True)
    def commit(message):
        click.echo(message)
        for m in message:
            click.echo(m)

.. click:run::

    invoke(commit, args=['-m', 'foo', '-m', 'bar', '-m', 'here'])
```

## Combining short options

Short options made of a single character can be combined into one argument: `-abc` is equivalent to `-a -b -c`. This is the standard POSIX behavior for short option stacking, and it is the reason a repeated flag like `-vvv` works with the [Counting](#counting) feature.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-a', is_flag=True)
    @click.option('-b', is_flag=True)
    @click.option('-c', is_flag=True)
    def cli(a, b, c):
        click.echo(f"a={a} b={b} c={c}")

.. click:run::

    invoke(cli, args=['-a', '-b', '-c'])
    invoke(cli, args=['-abc'])
```

If the last option in the combination takes a value, the value can either follow as the next argument or be attached directly:

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-v', is_flag=True)
    @click.option('-n', type=int)
    def cli(v, n):
        click.echo(f"v={v} n={n}")

.. click:run::

    invoke(cli, args=['-v', '-n', '5'])
    invoke(cli, args=['-vn', '5'])
    invoke(cli, args=['-vn5'])
```

```{note}
Multi-character short option names are not supported. An argument like `-dbg` is interpreted as the combination of `-d`, `-b`, and `-g`, so Click reports `No such option: -d` if `-d` is not declared. For longer option names, use a long option with the `--` prefix (like `--debug`).
```

## Counting

To count the occurrence of an option, set `count=True`. If the option is not
passed on the command line, then the count is 0. Counting is commonly used for
verbosity.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('-v', '--verbose', count=True)
    def log(verbose):
        click.echo(f"Verbosity: {verbose}")

.. click:run::

    invoke(log, args=[])
    invoke(log, args=['-vvv'])
```

(option-boolean-flag)=

## Boolean

Boolean options (boolean flags) take the values `True` or `False`. The simplest
case sets the default value to `False` if the flag is not passed, and `True` if
it is.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout', is_flag=True)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)


.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])

```

To implement this more explicitly, declare `--{on-option}/--{off-option}`. Click
will automatically set `is_flag=True`.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info)
    invoke(info, args=['--shout'])
    invoke(info, args=['--no-shout'])
```

Use cases for this more explicit pattern include:

* The default can be dynamic so the user can explicitly specify the option with
  either on or off option, or pass in no option to use the dynamic default.
* Shell scripts sometimes want to be explicit even when it's the default
* Shell aliases can set a flag, then an invocation can add a negation of the
  flag

If a forward slash (`/`) is contained in your option name already, you can split
the parameters using `;`. In Windows `/` is commonly used as the prefix
character.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('/debug;/no-debug')
    def log(debug):
        click.echo(f"debug={debug}")
```

```{versionchanged} 6.0
```

If you want to define an alias for the second option only, then you will need to
use leading whitespace to disambiguate the format string.

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--shout/--no-shout', ' /-N', default=False)
    def info(shout):
        rv = sys.platform
        if shout:
            rv = rv.upper() + '!!!!111'
        click.echo(rv)

.. click:run::

    invoke(info, args=['--help'])
```

## Flag Value

To have a flag pass a value to the decorated function set `flag_value`. This
automatically sets `is_flag=True`. To mark the flag as default, set
`default=True`. Setting flag values can be used to create patterns like this:

```{eval-rst}
.. click:example::

    import sys

    @click.command()
    @click.option('--upper', 'transformation', flag_value='upper', default=True)
    @click.option('--lower', 'transformation', flag_value='lower')
    def info(transformation):
        click.echo(getattr(sys.platform, transformation)())

.. click:run::

    invoke(info, args=['--help'])
    invoke(info, args=['--upper'])
    invoke(info, args=['--lower'])
    invoke(info)
```

### How `default` and `flag_value` interact

The `default` value is given to the underlying function
as-is. So if you set `default=None`, the function receives
`None`. Same for any other type.

But there is a special case for **non-boolean** flags: if a
flag has a non-boolean `flag_value` (like a string or a
class), then `default=True` is interpreted as *the flag
should be activated by default*. The function receives the
`flag_value`, not the Python `True`.

Which means, in the example above, this option:

```python
@click.option('--upper', 'transformation', flag_value='upper', default=True)
```

is equivalent to:

```python
@click.option('--upper', 'transformation', flag_value='upper', default='upper')
```

Because the two are equivalent, it is recommended to always
use the second form and set `default` to the actual value
you want. This makes code more explicit and predictable.

This special case does **not** apply to boolean flags (where
`flag_value` is `True` or `False`). For boolean flags,
`default=True` is the literal Python value `True`.

The tables below show the value received by the function for
each combination of `default`, `flag_value`, and whether
the flag was passed on the command line.

#### Boolean flags (`is_flag=True`, boolean `flag_value`)

These are flags where `flag_value` is `True` or `False`.
The `default` value is always passed through literally
without any special substitution.

| `default` | `flag_value` | Not passed | `--flag` passed |
|-----------|--------------|------------|-----------------|
| *(unset)* | *(unset)*    | `False`    | `True`          |
| `True`    | *(unset)*    | `True`     | `True`          |
| `False`   | *(unset)*    | `False`    | `True`          |
| `None`    | *(unset)*    | `None`     | `True`          |
| `True`    | `True`       | `True`     | `True`          |
| `True`    | `False`      | `True`     | `False`         |
| `False`   | `True`       | `False`    | `True`          |
| `False`   | `False`      | `False`    | `False`         |
| `None`    | `True`       | `None`     | `True`          |
| `None`    | `False`      | `None`     | `False`         |

````{tip}
For a negative flag that defaults to off, prefer the
explicit pair form `--with-xyz/--without-xyz` over the
single-flag `flag_value=False, default=True`:

```python
@click.option('--with-xyz/--without-xyz', 'enable_xyz', default=True)
```
````

#### Boolean flag pairs (`--flag/--no-flag`)

These use secondary option names to provide both an on and
off switch. The `default` value is always literal.

| `default` | Not passed | `--flag` | `--no-flag` |
|-----------|------------|----------|-------------|
| *(unset)* | `False`    | `True`   | `False`     |
| `True`    | `True`     | `True`   | `False`     |
| `False`   | `False`    | `True`   | `False`     |
| `None`    | `None`     | `True`   | `False`     |

#### Non-boolean feature switches (`flag_value` is a string, class, etc.)

For these flags, `default=True` is a **special case**: it
means "activate this flag by default" and resolves to the
`flag_value`. All other `default` values are passed through
literally.

| `default`  | `flag_value` | Not passed  | `--flag` passed |
|------------|--------------|-------------|-----------------|
| *(unset)*  | `"upper"`    | `None`      | `"upper"`       |
| `True`     | `"upper"`    | `"upper"`¹  | `"upper"`       |
| `"lower"`  | `"upper"`    | `"lower"`   | `"upper"`       |
| `None`     | `"upper"`    | `None`      | `"upper"`       |

```{hint}
¹: `default=True` is substituted with `flag_value`.
```

#### Feature switch groups (multiple flags sharing one variable)

Several `flag_value` options can target the same parameter name to form a
feature switch group. The user picks one flag on the command line, and the
function receives the corresponding `flag_value`. When the user picks none,
Click falls back to whichever option claims the slot under the arbitration
rules described below.

##### Non-boolean groups

For non-boolean `flag_value` (strings, enum members, classes, ...), place
`default=True` on the option that should win when no flag is passed. The
substitution rule above resolves it to that option's `flag_value`. Any other
explicit `default` is passed through literally.

| Definition                                             | Not passed | `--upper` | `--lower` |
|--------------------------------------------------------|------------|-----------|-----------|
| `--upper` with `flag_value='upper'`, `default=True`    | `"upper"`  | `"upper"` | `"lower"` |
| `--upper` with `flag_value='upper'`, `default='upper'` | `"upper"`  | `"upper"` | `"lower"` |
| `--upper` with `flag_value='upper'`, `default=None`    | `None`     | `"upper"` | `"lower"` |
| Neither option carries a `default`                     | `None`     | `"upper"` | `"lower"` |

The third row is the three-state pattern: the function receives `None` when no
flag is passed, distinguishable from either explicit choice.

##### Boolean groups

When `flag_value` is `True` or `False`, the substitution rule does not apply:
`default=True` is the literal Python `True`. To make one flag in an
enable/disable pair the default, set its `default=True` explicitly:

```python
@click.option("--without-xyz", "enable_xyz", flag_value=False)
@click.option("--with-xyz", "enable_xyz", flag_value=True, default=True)
```

| Definition                                              | Not passed | `--with-xyz` | `--without-xyz` |
|---------------------------------------------------------|------------|--------------|-----------------|
| `--with-xyz` with `flag_value=True`, `default=True`     | `True`     | `True`       | `False`         |
| `--without-xyz` with `flag_value=False`, `default=False`| `False`    | `True`       | `False`         |
| `--with-xyz` with `flag_value=True`, `default=None`     | `None`     | `True`       | `False`         |
| Neither option carries a `default`                      | `False`    | `True`       | `False`         |

```{tip}
For most enable/disable cases, the pair form `--with-xyz/--without-xyz` is
shorter and equivalent. The multi-flag group form is useful when the on and off
flags need distinct names without a shared stem, or when each flag needs its
own help text.
```

##### Arbitration rules

When several options in a group resolve their values simultaneously, only one
wins the parameter slot. The full arbitration policy (source precedence,
explicit-beats-auto tie-break, last-declared fallback) is enumerated under
[Option value resolution](#option-value-resolution).

## Option value resolution

This section enumerates the rules Click applies when computing the value
delivered to the decorated function for every option. Rules are listed in the
order they fire during the parsing pipeline.

### Type inference

Without an explicit `type=`, Click infers the parameter type at construction:

1. If `flag_value` is `True` or `False`, the type is {class}`BoolParamType`.
2. If `flag_value` is an `int`, `float`, or `str`, the type is the matching
   basic type.
3. If `flag_value` is any other Python object (a class, an enum member, a
   `frozenset`, ...), the type is {data}`UNPROCESSED` so the value passes
   through unchanged.
4. Otherwise, the type is inferred from `default` if set, falling back to
   {class}`StringParamType` when neither hint is available.

### `default` interpretation

The literal value passed as `default=` is interpreted differently depending on
whether the option is a flag and what `flag_value` it carries:

1. `default=UNSET` (the absence sentinel) is treated as if `default` was not
   passed at all. It does not count as "the user picked nothing", and it does
   not count as an explicit default for arbitration purposes.
2. For a bare boolean flag (no `flag_value`, or `flag_value` of `True` or
   `False`), an unset `default` auto-derives to `False`.
3. For a non-boolean flag with a `flag_value`, `default=True` is substituted
   with `flag_value`. This is the "activate this flag by default" shorthand.
   Any non-`True` `default` is passed through literally.
4. For a boolean flag with `flag_value` set, `default=True` is the literal
   Python `True`. The substitution from rule 3 does not apply.
5. `default=None` is always a real explicit value, distinct from `UNSET`
   absence.
6. Any other `default` is delivered to the function unchanged after conversion
   through the parameter's type.

### Value sources

Click resolves the value of every option from the following
sources, in order of decreasing precedence:

1. **command line input** ({attr}`ParameterSource.COMMANDLINE`),
2. **environment variable** named in `envvar=` or derived from `auto_envvar_prefix`
   ({attr}`ParameterSource.ENVIRONMENT`),
3. **`default_map` entry** matching the parameter name on the active {class}`Context`
   ({attr}`ParameterSource.DEFAULT_MAP`),
4. **parameter default** ({attr}`ParameterSource.DEFAULT`).

The first source that produces a value wins. Environment variables and
`default_map` entries set to `Sentinel.UNSET` are skipped, so they fall through
to the next source rather than supplying `UNSET` to the function.

If after the four sources above no explicit value was found (or only a
`default_map`/`default` value was) and the option declares `prompt=`, Click
prompts the user for one. The resulting value is recorded as
{attr}`ParameterSource.PROMPT`, which ranks above every source listed above
for arbitration purposes (see [Slot arbitration](#slot-arbitration)).

### Slot arbitration

Several options can target the same `name` to form a feature switch group. When
they do, only one option's value reaches the function. Arbitration applies
these rules, in order:

1. **By source.** Whichever option resolved its value from the most explicit
   source wins, regardless of decorator order. Any command-line input beats any
   default, an environment variable beats a `default_map` entry, and so on.
2. **Within the default tier, explicit beats auto-derived.** An option that
   received an explicit `default=` keyword wins over one whose default came
   from `default` interpretation.
3. **Otherwise, last declared wins.** When all options in the group resolved
   from the same source and tier (all auto-derived defaults, or all explicit
   defaults), the option declared last in the source code keeps the slot.

## Values from Environment Variables

To pass in a value from a specific environment variable use `envvar`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar='USERNAME')
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'USERNAME': 'john'})
```

If a list is passed to `envvar`, the first environment variable found is picked.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('--username', envvar=['ALT_USERNAME', 'USERNAME'])
    def greet(username):
       click.echo(f"Hello {username}!")

.. click:run::

    invoke(greet, env={'ALT_USERNAME': 'Bill', 'USERNAME': 'john'})

```

Variable names are:
 - [Case-insensitive on Windows but not on other platforms](https://github.com/python/cpython/blob/aa9eb5f757ceff461e6e996f12c89e5d9b583b01/Lib/os.py#L777-L789).
 - Not stripped of whitespace and should match the exact name provided to the
   `envvar` argument.

For flag options, there are two concepts to consider: the activation of the flag
driven by the environment variable, and the value of the flag if it is
activated.

The values read from environment variables are always strings and will require
extra processing. We need to transform these strings into boolean values that
will determine if the flag is activated or not.

Here are the rules used to parse environment variable values for flag options:
   - `true`, `1`, `yes`, `on`, `t`, `y` are interpreted as activating the flag
   - `false`, `0`, `no`, `off`, `f`, `n` are interpreted as deactivating the
     flag
   - The presence of the environment variable without value is interpreted as
     deactivating the flag
   - Empty strings are interpreted as deactivating the flag
   - Values are case-insensitive, so the `True`, `TRUE`, `tRuE` strings are all
     interpreted as activating the flag
   - Values are stripped of leading and trailing whitespace before being
     interpreted, so the `" True "` string is transformed to `"true"` and thus
     activates the flag
   - If the flag option has a `flag_value` argument, passing that value in the
     environment variable will activate the flag, in addition to all the cases
     described above
   - Any other value is interpreted as deactivating the flag

```{caution}
For boolean flags with a pair of values, the only recognized environment variable is the one provided to the `envvar` argument.

So an option defined as `--flag/--no-flag`, with an `envvar="FLAG"` parameter, there is no magical `NO_FLAG=<anything>` variable that is recognized. Only the `FLAG=<anything>` environment variable is recognized.
```

If the flag is activated, its value is set to `flag_value`. Otherwise, the value
defaults to `None`.

## Multiple Options from Environment Values

As options can accept multiple values, pulling in such values from
environment variables (which are strings) is a bit more complex. Click handles
this by deferring customization of the behavior to the `type`. For both
`multiple` and `nargs` with values other than
`1`, Click will invoke the {meth}`ParamType.split_envvar_value` method to
perform the splitting.

The default implementation for all types is to split on whitespace. The
exceptions to this rule are the {class}`File` and {class}`Path` types
which both split according to the operating system's path splitting rules.
On Unix systems like Linux and OS X, the splitting happens on
every colon (`:`), and for Windows, splitting on every semicolon (`;`).

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('paths', '--path', envvar='PATHS', multiple=True,
                  type=click.Path())
    def perform(paths):
        for path in paths:
            click.echo(path)

    if __name__ == '__main__':
        perform()

.. click:run::

    import os
    invoke(perform, env={"PATHS": f"./foo/bar{os.path.pathsep}./test"})
```

## Other Prefix Characters

Click can deal with prefix characters besides `-` for options, including `/` and
`+`, as well as others. Note that alternative prefix characters are generally
used very sparingly if at all within POSIX.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option('+w/-w')
    def chmod(w):
        click.echo(f"writable={w}")

.. click:run::

    invoke(chmod, args=['+w'])
    invoke(chmod, args=['-w'])
```

There are special considerations for using `/` as prefix character. See
{ref}`option-boolean-flag` for more.

(optional-value)=

## Optional Value

Providing the value to an option can be made optional, in which case
providing only the option's flag without a value will either show a
prompt or use its `flag_value`.

Setting `is_flag=False, flag_value=value` tells Click that the option
can still be passed a value, but if only the flag is given, the
value will be `flag_value`.

```{eval-rst}
.. click:example::

    @click.command()
    @click.option("--name", is_flag=False, flag_value="Flag", default="Default")
    def hello(name):
        click.echo(f"Hello, {name}!")

.. click:run::

    invoke(hello, args=[])
    invoke(hello, args=["--name", "Value"])
    invoke(hello, args=["--name"])
```
