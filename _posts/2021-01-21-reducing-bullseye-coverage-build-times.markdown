---
layout: post
title:  "Reducing Bullseye Coverage Build Times"
date:   2021-01-21 09:31:03 -0800
categories: cmake build-systems code-coverage bullseye
---

**TL;DR** Use [covc] directly, instead of using the provided compiler interceptors.

Intro to Bullseye
=================

We currently utilize [BullseyeCoverage][BullseyeCoverage] for measuring code
coverage in C files. BullseyeCoverage works well with the multiple
compilation toolchains we use.

One of the ways that BullseyeCoverage integrates with compilation toolchains
is via compiler interceptors. The interceptors work by having the same
executable name as the compiler, but being first in the system path. This
means the interceptor is invoked instead of the real compiler. When coverage
is enabled the interceptor invokes [covc] to do the necessary pre-processing
on the source file(s) to insert the coverage probes, and then forwards this
pre-processed version to the real compiler. When coverage is not enabled the
interceptor just passes directly through to the real compiler.

These compiler interceptors make it easy to integrate BullseyeCoverage into
one's build. Often times there is little to no modification to the build
system, only updating the environment of the build machines.  

The interceptors have a couple of downsides:
- Enabling and disabling of coverage is generally a system wide environment
  setting. This means either all build tasks are running with coverage or all
  build tasks are running without coverage. It is possible to use
  ``COVBUILDZONE``s with BullseyeCoverage's [cov01][cov01] command to limit
  this some.
- All built files end up being processed by bullseye. Even if utilizing
  ``COVBUILDZONE``s, any and all files being compiled will be passed through
  BullseyeCoverage.  

Investigating BullseyeCoverage Build Times
==========================================

While investigating changing our underlying build system one of the areas of
focus was, what improvements in compilation times could be gained.
Historically builds with BullseyeCoverage had been slow. In our particular
profiling scenario it took 1 minute to build a unit test and all dependencies
from scratch. Doing the same build with BullseyeCoverage took 2 minutes and
30 seconds. The bullseye documentation says:

> Instrumenting with BullseyeCoverage typically increases [...] compile time
> to 1.7x with most Microsoft C++ projects, 3-8x with other compilers.

So this 2.5x increase in compilation time was not unexpected.

We don't utilize pre-built libraries, we build all of our dependencies. While
investigating the build times it was quickly realized the code needing to be
instrumented only accounted for about 6 seconds of the overall 1 minute
build. Building only this smaller subset of code with BullseyeCoverage took
16 seconds.

How We Reduced Bullseye Build Times
===================================

With the realization that a reduction of more than 50% could be achieved when
using BullseyeCoverage, we decided to find a way to make it happen.

Our current process utilized a configuration file that would be picked up
when the compiler interceptor invoked [covc]. This configuration file would
specify the [regions][region] to be captured in the coverage report. If one
looks at the docs for [covc], there is a note about exclusion regions:

> Normally you should use the Coverage Browser or covselect to exclude code
> rather than this option.

There is no clarification as to why one might use the ``covselect`` tool over
exclusion regions.

Since the report had been limited to only the files of interest, we thought
that BullseyeCoverage would not bother processing other files. This was a
false assumption.

Since the region limitation was not preventing our code form being processed
by BullseyeCoverage, we next looked to limiting it via the build system.
We were migrating to CMake so were able to utilize the
[C_COMPILER_LAUNCHER][compiler_launcher] property to directly call [covc] for
only the targets that we wanted to instrument. The naive approach is simply:
{% highlight cmake %}
set_target_properties(target_to_get_coverage_for
                      PROPERTIES C_COMPILER_LAUNCHER "path/to/bullseye/covc")
)
{% endhighlight %}

I won't go into the full details of the implementation. I'll just say we
modeled some of the interface off of [CMake-codecov].

In the end directly invoking [covc], for only the files to be instrumented,
resulted in only a 10 second increase in our overall build times. Utilizing
[C_COMPILER_LAUNCHER][compiler_launcher] limits coverage builds to the
[Ninja] and Makefile generators, but this was a compromise we were willing to
accept in favor of overall build time speed up.

{% include note.html content="I haven't used [CMake-codecov].
Initial inspection of it's API looks to be nice if one is using gcov or
lcov." %}

[BullseyeCoverage]: https://www.bullseye.com/
[cov01]: https://www.bullseye.com/help/ref-cov01.html
[region]: https://www.bullseye.com/help/ref-regions.html
[covc]: https://www.bullseye.com/help/ref-covc.html
[compiler_launcher]: https://cmake.org/cmake/help/latest/prop_tgt/LANG_COMPILER_LAUNCHER.html
[CMake-codecov]: https://github.com/RWTH-HPC/CMake-codecov
[Ninja]: https://ninja-build.org/

