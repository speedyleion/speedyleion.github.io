---
layout: post
title:  "WinMain and Console Out"
date:   2021-07-11 17:16:03 -0700
categories: c c++ windows
---

> This post assumes readers are aware of the `main()` function present in most c and
c++ programs.

Two Flavors of `main()`
=======================

When developing C/C++ programs for Windows, one needs to be aware of the two
versions of `main`:

- There is the traditional `main()`.  The entry point for a console based
program.
- Then there is [`WinMain()`][WinMain].  The entry point for a Windows
graphical program.

The important distinction between the two entry points is, console versus
graphical.  

Console
-------

A console program provides standard out and standard error back to the console
which started the program.  When one starts the program via the icon in Windows
explorer, a console window will be created and persist while the program is
running.

Graphical
---------

A graphical program does not normally provide the standard out and standard
error streams.  This means things like `printf()` or `std::cout` may not go
anywhere.  When launched from Windows explorer, a console is not created.
Unless something is explicitly provided by the program, there is nowhere for
standard out and standard error to go.  When a graphical program is launched
from a console, standard out and standard error will not be redirected to the
console.

WinMain Standard Out and the Console
====================================

Let us play around with a [`WinMain()`][WinMain] program and see what things
happen.

We'll create a simple [Catch2] test and use `WinMain()`.

> This is using [Catch2] version 2.

{% highlight c++ %}
#define CATCH_CONFIG_RUNNER
#include "catch2/catch.hpp"
#include <Windows.h>

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow) {
    int result = Catch::Session().run(__argc, __wargv);
    return result;
}

TEST_CASE("Testing GUI app"){
    REQUIRE(3==4);
}
{% endhighlight %}

The contents of `WinMain()` is from the guidance in [Catch2]'s documentation for
[providing your own `main()` implementation][Catch2-own-main].
We're using `WinMain()` instead.  The [`__argc`][__argc-__argv] and
[`__wargv`][__argc-__argv] variables are Windows specific syntactic sugar.
They're being used here since `WinMain()` doesn't provide them.  Be sure and
define `UNICODE` in order for the `__wargv` version to work with the `run()`
method from [Catch2]'s Session instance.

The `TEST_CASE` is [Catch2]'s form of a test case.  The `REQUIRE` is
intentionally written to fail since `3` is not equivalent to `4`.  We want a
failure, because [Catch2] will provide output about the failure by default.

> When building you will most likely need to specify this is a Windows graphical
program.  For example if one is using CMake one needs to provide the `WIN32`
argument to [`add_executable()`][CMake-add_executable].

Running this program from a console will result in no output, even though there
is a failure.  

```
User@machine MSYS /c/some/dir/winmain (main)
$ build/tests/Debug/test_winmain.exe

User@machine MSYS /c/some/dir/winmain (main)
$
```

An interesting thing happens if we pipe the output. 

```
User@machine MSYS /c/some/dir/winmain (main)
$ build/tests/Debug/test_winmain.exe | tee.exe output.txt

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
test_winmain.exe is a Catch v2.13.3 host application.
Run with -? for options

-------------------------------------------------------------------------------
Testing GUI app
-------------------------------------------------------------------------------
C:\some\dir\winmain\tests\TestWinMain.cpp(10)
...............................................................................

C:\some\dir\winmain\tests\TestWinMain.cpp(11): FAILED:
  REQUIRE( 3==4 )
with expansion:
  3 == 4

===============================================================================
test cases: 1 | 1 failed
assertions: 1 | 1 failed
```

I used `tee.exe` so that one could see the output and not have to also read back
`output.txt`.  It appears the output is being directed through the pipe.

Attaching Back to a Console
===========================

Doing some searching on the googles for `WinMain()` and standard out will lead
to some suggestions for addressing the problem.  I'll admit I don't have a full
understanding of all of the suggested solutions, however the simplest one I
found was from [http://maoserr.com/notes/win32gui_console/](http://maoserr.com/notes/win32gui_console/).

Modifying our `WinMain()` with the suggested solution:

{% highlight c++ %}
int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow) {
    if(AttachConsole(ATTACH_PARENT_PROCESS)){
            freopen("CONOUT$","wb",stdout);
            freopen("CONOUT$","wb",stderr);
    }
    int result = Catch::Session().run(__argc, __wargv);
    return result;
}
{% endhighlight %}

If we look up [AttachConsole] on MSDN, we can see that it says:
> Attaches the calling process to the console of the specified process as a client application.

And looking at the `ATTACH_PARENT_PROCESS` argument it says:
> Use the console of the parent of the current process.

So that seems to imply this will attempt to attach our program to the parent
process's console.

[`freopen`][freopen] is a C library function which closes `stdout`, and
`stderr`, then reopens them to output to [`CONOUT$`][CONOUT].
[`CONOUT$`][CONOUT] is a Windows specific filename for the current console.

Sumarizing; this attaches the program to the parent's console and redirects
`stdout` and `stderr` to the parent console.

Running the tests with this solution results in:
```
User@machine MSYS /c/some/dir/winmain (main)
$ build/tests/Debug/test_winmain.exe 

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
test_winmain.exe is a Catch v2.13.3 host application.
Run with -? for options

-------------------------------------------------------------------------------
Testing GUI app
-------------------------------------------------------------------------------
C:\some\dir\winmain\tests\TestWinMain.cpp(14)
...............................................................................

C:\some\dir\winmain\tests\TestWinMain.cpp(15): FAILED:
  REQUIRE( 3==4 )
with expansion:
  3 == 4

===============================================================================
test cases: 1 | 1 failed
assertions: 1 | 1 failed
```

Hopefully you also have some colorization in your output too.

The Gotcha of Always Attaching
------------------------------

So it seemed pretty easy to attach a Windows GUI app to a console.  However a
downside started to show up.  There are some programs, such as [ctest], which
want to capture the output of other programs.  If we run this test program
through ctest we get:

```
User@machine MSYS /c/some/dir/winmain/build (main)
$ ctest -C debug
Test project C:/some/dir/winmain/build
    Start 1: test_winmain

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
test_winmain.exe is a Catch v2.13.3 host application.
Run with -? for options

-------------------------------------------------------------------------------
Testing GUI app
-------------------------------------------------------------------------------
C:\some\dir\winmain\tests\TestWinMain.cpp(14)
...............................................................................

C:\some\dir\winmain\tests\TestWinMain.cpp(15): FAILED:
  REQUIRE( 3==4 )
with expansion:
  3 == 4

===============================================================================
test cases: 1 | 1 failed
assertions: 1 | 1 failed

1/1 Test #1: test_winmain .....................***Failed    0.10 sec

0% tests passed, 1 tests failed out of 1

Total Test time (real) =   0.12 sec

The following tests FAILED:
          1 - test_winmain (Failed)
Errors while running CTest
```

For those unfamiliar with [ctest] this may seem expected, however the purpose of
[ctest] is to run multiple tests and provide a test summary.  By defualt [ctest]
shouldn't be providing individual test case failures.  The expected output from
[ctest] is:

```
User@machine MSYS /c/some/dir/winmain/build (main)
$ ctest -C debug
Test project C:/some/dir/winmain/build
    Start 1: test_winmain
1/1 Test #1: test_winmain .....................***Failed    0.94 sec

0% tests passed, 1 tests failed out of 1

Total Test time (real) =   0.94 sec

The following tests FAILED:
          1 - test_winmain (Failed)
Errors while running CTest
```

This seems to imply that we are attaching to the console which launched [ctest]
and bypassing [ctest]'s capturing of the standard out and standard error
streams.

Conditionally Attaching
-----------------------

Doing some searching on the googles [GetStdHandle] was encountered.  The
important pieces to note are:
> If the function succeeds, the return value is a handle to the specified device.

and
> If an application does not have associated standard handles [...] the return value is NULL.

So let us further expand our [WinMain] to only conditionally reopen the `stdout`
and `stderr` streams.  This is only looking at standard out, it would probably
be more robust to check each handle and only attach the handles that aren't
attached yet.

{% highlight c++ %}
int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PWSTR pCmdLine, int nCmdShow) {
    if(!GetStdHandle(STD_OUTPUT_HANDLE)){
        if(AttachConsole(ATTACH_PARENT_PROCESS)){
            freopen("CONOUT$","wb",stdout);
            freopen("CONOUT$","wb",stderr);
        }
    }

    int result = Catch::Session().run(__argc, __wargv);
    return result;
}
{% endhighlight %}

Now if we build and run this with [ctest] we get the expected output:
```
User@machine MSYS /c/some/dir/winmain/build (main)
$ ctest -C debug
Test project C:/some/dir/winmain/build
    Start 1: test_winmain
1/1 Test #1: test_winmain .....................***Failed    0.65 sec

0% tests passed, 1 tests failed out of 1

Total Test time (real) =   0.94 sec

The following tests FAILED:
          1 - test_winmain (Failed)
Errors while running CTest
```

If we go back and run the test program directly from the command line we
still get the full [Catch2] ouptut.

Summary
=======

Normally Windows graphical programs do not write to a console's standard out and
standard error.  If attempting to attach standard out and standard error to the
console, be sure that they aren't already attached to something from whatever
may be invoking the program.


[WinMain]: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-winmain
[Catch2]: https://github.com/catchorg/Catch2
[Catch2-own-main]: https://github.com/catchorg/Catch2/blob/devel/docs/own-main.md#let-catch-take-full-control-of-args-and-config
[__argc-__argv]: https://docs.microsoft.com/en-us/cpp/c-runtime-library/argc-argv-wargv?view=msvc-160
[CMake-add_executable]: https://cmake.org/cmake/help/latest/command/add_executable.html
[AttachConsole]: https://docs.microsoft.com/en-us/windows/console/attachconsole?redirectedfrom=MSDN
[freopen]: https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/freopen-wfreopen?view=msvc-160
[CONOUT]: https://docs.microsoft.com/en-us/windows/console/console-handles
[ctest]: https://cmake.org/cmake/help/latest/manual/ctest.1.html
[GetStdHandle]: https://docs.microsoft.com/en-us/windows/console/getstdhandle