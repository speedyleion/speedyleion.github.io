---
layout: post
title:  "Invoking Poetry from a Script"
date:   2021-11-19 20:40:03 -0800
categories: python poetry
---

We have a common python script that is used for doing various development tasks.
The script has sub commands similar to git or [poetry][poetry].

For example, if our script is named `foo.py`, we might have commands like:

```
    foo.py make-coffee --with-cream --with-sugar
    foo.py get-lunch --vegan
```

The details of what it does isn't really important, just that we have this
python script, it depends on various python packages, and we don't use a virtual
environment.  _Insert every shock and awe emoji you can think of here_

Since this post is about [poetry][poetry] and the development script, hopefully
you can see that I'm trying to rectify the no virtual environment practice.  I
wanted a virtual environment tool that would handle pinning transitive
dependencies in a somewhat automatic fashion.  There are a few other solutions
such as [pipenv][pipenv] and [pip-tools][pip-tools].  For our uses I think any
of these may be viable options.

I want to ease the transition to virtual environments as much as possible.  The
team is not comprised of python developers.  We need to support code branches
going back years, so we want to make it easy for developers to jump back and
forth between branches without having to directly interact with too many
oddities of each branch.

All that to say, I would like to avoid devlopers having to do:
```
    poetry run foo.py make-coffee
```
in some branches, but then having to do:
```
    foo.py make-coffee
```
in other branches.  One might say "just pull the changes into the other
branches".  You'll have to trust me when I tell you that, with our current
tooling, it's not as practical as it could be.

The Investigation
=================

With the desire of keeping the developer workflow to invoking `foo.py` directly,
I decided to investigate how one might invoke [poetry][poetry] from a wrapper
script.

When [poetry][poetry] is installed it's installed as an executable.  Knowing
what little I know about python packaging that implied to me that when it's
packaged the executable is a generated wrapper for a script.  So I did some
quick digging into the [poetry repo][poetry-repo] and found the `pyproject.toml`
with the following entry:

```
    [tool.poetry.scripts]
    poetry = "poetry.console.application:main"
```

This implies to me that there is a `main()` function in
`poetry.console.application` and sure enough I found:

{% highlight python %}
def main() -> int:
    return Application().run()
{% endhighlight %}

From prior experience with argparse, I'm looking for the use of `argv` or
`sys.argv`.  My thought is that I should somehow be able to invoke the main
[poetry][poetry] entry point and pass it arguments.  I could probably get away
with overriding `sys.argv` and calling `Application().run()` in my script, but
if possible I would like a way to pass arguments.

Even though I was using VSCode in the browser in the Github repo, I wasn't able
to jump directly to the implementation of `run()`, so I did the more manual
process.  In the same file there was an `Application` class that derives from
`BaseApplication`.  

{% highlight python %}
class Application(BaseApplication):
    def __init__(self) -> None:
        super().__init__("poetry", __version__)
{% endhighlight %}

Looking at the top of the file there was a nice import

{% highlight python %}
from cleo.application import Application as BaseApplication
{% endhighlight %}

Cleo
----

I hadn't ran across [Cleo][cleo] before.  It's another take on a command line
parser. Now that I'm investing more in virtual environments, maybe I'll finally
start looking at things outside of argparse.

[Cleo's][cleo] release at the time of this writing is `0.8.1`, while their
mainline has a pre-release.  So one must navigate through the `0.8.1` version as
that is what [poetry][poetry] depends on.
Navigating through the [Cleo repo][cleo-repo] I found the `Application` class

{% highlight python %}
class Application(ConsoleApplication, object):
    """
    An Application is the container for a collection of commands.

    This class is optimized for a standard CLI environment.

    Usage:
    >>> app = Application('myapp', '1.0 (stable)')
    >>> app.add(HelpCommand())
    >>> app.run()
    """
{% endhighlight %}

This derives from `ConsoleApplication` which comes from [clikit][clikit],
another package maintained by the same people as [Cleo][cleo].

{% highlight python %}
from clikit.console_application import ConsoleApplication
{% endhighlight %}

Looking at the `run()` method on `ConsoleApplication` one can see:

{% highlight python %}
    def run(
        self, args=None, input_stream=None, output_stream=None, error_stream=None
    ):  # type: (RawArgs, InputStream, OutputStream, OutputStream) -> int
        # Render errors to the preliminary IO until the final IO is created
        io = self._preliminary_io
        try:
            if args is None:
                args = ArgvArgs()

            io_factory = self._config.io_factory
{% endhighlight %}

> Only the first part of the method is displayed

The `args` variable and `ArgvArgs()` call look promising.  Navigating to the
definition for `ArgvArgs`:

{% highlight python %}
class ArgvArgs(RawArgs):
    """
    Console arguments passed via sys.argv.
    """

    def __init__(self, argv=None):  # type: (Optional[List[str]]) -> None
        if argv is None:
            argv = list(sys.argv)
{% endhighlight %}

There is the `sys.argv` I was looking for.  It looks like if nothign is passed
to the `ArgvArgs()` constructor than `sys.argv` will be used.  However one can
pass in a list of arguments to not use `sys.argv`.

Hypothesis
==========

I'm thinking I can create a `clikit.args.argv_args.ArgvArgs` instance.  During
the creation of this `ArgvArgs` I can pass in 
`["poetry", "run", "my_script.py"]` as the `argv` parameter.  Then pass this
`ArgvArgs` into [poetry's][poetry] `Application().run()` method.

The Test
--------

For the `foo.py` script we'll have:
{% highlight python %}
import os
venv = os.environ.get("VIRTUAL_ENV", "NO VENV SET")
print(venv)
{% endhighlight %}

For the test I'll use an alternative script to launch `foo.py`.  I'll call this
`bar.py`:
{% highlight python %}
import sys

from clikit.args.argv_args import ArgvArgs
from poetry.console.application import Application

args = ["poetry", "run", "foo.py"]
argv = ArgvArgs(args)
Application().run(argv)
{% endhighlight %}

The Results
-----------

First I tried to run `foo.py` directoy with python and [poetry][poetry] to
verify my logic.
Running `foo.py` directly with python resulted in the expected `"NO VENV SET"`.
Trying to run `foo.py` directly with [poetry][poetry] via `poetry run foo.py`
failed.  It looks like [poetry][poetry] will try to run this as an application,
so I had to change my command slightly to `poetry run python foo.py`.  Adding
`python` to the command resulted in outputing the path to a virtual environment
in my home directory.

> In retrospect I failed to read the poetry documentation correctly.  If one
> reads the documentation for 
> [Using poetry run](https://python-poetry.org/docs/basic-usage/#using-poetry-run)
> it shows an example of `poetry run python your_script.py`

With that knowledge, `bar.py` was modified slightly:

{% highlight python %}
args = ["poetry", "run", "python", "foo.py"]
{% endhighlight %}

Invoking `bar.py` directly provided the path to a virtual environment in my home
directory, just like when I did `poetry run python foo.py`.

Polishing The BootStrapper
==========================

In  my mind `bar.py` is a sort of bootstrapper.  It seems like it could be
reusable for other scripts that need to leverage poetry.  This will require a
little bit of rework.

The First Refactor Pass
-----------------------

The new contents of `bar.py`:

{% highlight python %}
import os
import sys

def launch(script_name):
    if os.environ.get("VIRTUAL_ENV"):
        return

    from clikit.args.argv_args import ArgvArgs
    from poetry.console.application import Application

    args = ["poetry", "run", "python", script_name]
    argv = ArgvArgs(args)
    sys.exit(Application().run(argv))
{% endhighlight %}

`bar.py` is now a module with functions and it will no longer be invokable
directly from the command line.  It has a new function `launch()`, which is
provided the name of the script to launch.  Passing in the script is important,
as this will prevent circular dependencies and make the bootstrapper re-usable
to other scripts.

One important piece to note is the `VIRTUAL_ENV` check, this should prevent
recursion from `foo.py`.  We also use `sys.exit()` at the bottom, which means
that `launch()` will try to exit the python process when outside of a virtual
environment. If a caller really wanted to, they could catch `SystemExit`.
Admitedly I'm not sure if I like this `sys.exit()` usage, but I like the idea of
callers not needing to have conditional logic around their use of `launch()`.

The thought did briefly creep into the back of my mind to do the logic when
importing `bar.py`. My better judgement prevailed here. It sounds nice
initially, but importing with side effects seems to never play out well in the
long run.

The new version of `foo.py` adds the importing of `bar.py` and calling the new
`launch()` function:
{% highlight python %}
import os
import bar
bar.launch("foo.py")
venv = os.environ.get("VIRTUAL_ENV", "NO VENV SET")
print(venv)
{% endhighlight %}

One may notice that it looks like this script will always print the
`VIRTUAL_ENV` variable, however `bar.launch()` will exit when `foo.py` is
invoked outside of a virtual environmeent.  As mentioned above, this might be
too magical of an interface, only time will tell.

The Second Refactor Pass
------------------------

The next refactor is going to ensure that all arguments get passed into
`launch()`, not just the script name.

Even though the command may be `poetry run python foo.py`, when the python
executable runs it will only provide `foo.py`, and any trailing arguments, in
`sys.argv`.  This means we can read `sys.argv` directly as if `foo.py` was
invoked on the command line.

{% highlight python %}
import os
import sys

def launch(argv=None):
    if os.environ.get("VIRTUAL_ENV"):
        return

    from clikit.args.argv_args import ArgvArgs
    from poetry.console.application import Application

    if argv is None:
        argv = sys.argv

    args = ["poetry", "run", "python"] + argv
    argv = ArgvArgs(args)
    sys.exit(Application().run(argv))
{% endhighlight %}

Like the `ArgvArgs` from [clikit][clikit], `launch()` can have the arguments
optionally passed in.  If they aren't provided then they will be grabbed from
`sys.argv`.

The change to `foo.py` is minor.  Removal of passing the script name:

{% highlight python %}
import os
import bar
bar.launch()
venv = os.environ.get("VIRTUAL_ENV", "NO VENV SET")
print(venv)
{% endhighlight %}

The Last Refactor
-----------------

As I mentioned before, most of the team members aren't python developers and I
want this transition to be as seemless as possible for them.  In order to
streamline this change I would like to avoid extra steps for the developers when
they move to a newer version of the code base.  This means I'm going to do
something that is debatable, the script will be installing [poetry][poetry] if
it's not there yet.

{% highlight python %}
import os
import sys

def ensure_poetry():
    try:
        import poetry
    except ImportError:
        import pip
        pip.main(["install", "poetry==1.1.11", "--user"])

def launch(argv=None):
    if os.environ.get("VIRTUAL_ENV"):
        return

    ensure_poetry()
    from poetry.__version__ import __version__ as poetry_version
    if not poetry_version == "1.1.11":
        return

    from clikit.args.argv_args import ArgvArgs
    from poetry.console.application import Application

    if argv is None:
        argv = sys.argv

    args = ["poetry", "run", "python"] + argv
    argv = ArgvArgs(args)
    sys.exit(Application().run(argv))
{% endhighlight %}

This will install a specific version of poetry if the user doesn't have it
installed yet. It will install into the `--user` directory to avoid admin
permissions and to make it easier to clean up later if need be.

After we `ensure_poetry` is installed there is a check against the version.
While this is a bit restrictive, I don't think any developers will have poetry
pre-installed so this will get us by for a time. I'll leave any compatibility
issues for future me.  Initially in researching this, I dug through
[Cleo's][cleo] unreleased version. There are going to be some changes coming to
how arguments are passed in the `Application` class, so this specific
implementation probably won't work on some future version of [poetry][poetry].  

Summary
-------

It is possible to wrap up [poetry][poetry] and invoke it from within another
python module.  While some of my current solution may be debatable, I'm hoping
that we can transition to using virtual environments without too much manual
user setup.  I will admit that I'm fairly new to [poetry][poetry], so there may
be a better way or even a documented way to achieve a similar solution.  I just
didn't see anything using my google fu.

The bootstrap script is fairly minimal to add to any standard python script:
{% highlight python %}
import bar
bar.launch()
{% endhighlight %}

> If you decide to copy this idea, I would suggest renaming from `bar.py`.

[poetry]: https://python-poetry.org/
[pipenv]: https://pipenv.pypa.io/en/latest/
[pip-tools]: https://github.com/jazzband/pip-tools
[poetry-repo]: https://github.com/python-poetry/poetry
[cleo]: https://cleo.readthedocs.io/en/latest/
[cleo-repo]: https://github.com/sdispater/cleo
[clikit]: https://github.com/sdispater/clikit