---
layout: post
title:  "Reducing Bullseye Coverage Build Times"
date:   2021-01-21 09:31:03 -0800
categories: cmake build-systems
---

**TL;DR** Only instrument the files to be measured.

Intro to Bullseye
=================

We currently utilize [BullseyeCoverage][BullseyeCoverage] for measuring code
coverage in C files. BullseyeCoverage works well with the multiple
compilation toolchains we use.

One of the ways that BullseyeCoverage integrates with compilation toolchains
is via compiler interceptors. The interceptors work by having the same
executable name as the compiler, but being first in the system path. This
means the interceptor is invoked instead of the real compiler. When coverage
is enabled the interceptor invokes [covc][covc] to do the necessary
pre-processing on the source file(s) to insert the coverage probes, and then
forwards this pre-processed version to the real compiler. When coverage is
not enabled the interceptor just passes directly through to the real
compiler.

These compiler interceptors make it easy to integrate BullseyeCoverage into
one's build. Often times there is little to no modification to the build
system, only updating the environment of the build machines.  

The interceptors have a couple of downsides:
- Enabling and disabling of coverage is generally a system wide environment
  setting. This means either all build tasks are running with coverage or all
  build tasks are running without coverage. It is possible to use
  ``COVBUILDZONE``s with BullseyeCoverage's [cov01][cov01] command to limit
  this some.
- All built files end up being processed by bullseye. Even utilizing
  ``COVBUILDZONE``s any and all files being compiled will be passed through
  BullseyeCoverage.  

Investigating BullseyeCoverage Build Times
==========================================

While investigating changing our underlying build system we were focusing on
what, if any, improvements in compilation times we might gain. Historically
builds with BullseyeCoverage had been slow. In our particular profiling
scenario it took 1 minute to build a unit test and all dependencies from
scratch. When we did the same build with BullseyeCoverage the time went to 2
minutes and 30 seconds.  The bullseye documentation does say:
> Instrumenting with BullseyeCoverage typically increases [...] compile time
> to 1.7x with most Microsoft C++ projects, 3-8x with other compilers.
So this 2.5x increase in compile times was not unexpected.

We don't utilize pre-built libraries, we build all of our dependencies. While
investigating the build times we quickly realized the code we were interested
in instrumenting only accounted for about 6 seconds of the overall 1 minute
build. If we only built this smaller subset of code with BullseyeCoverage, it
took 16 seconds. 

How We Reduced Bullseye Build Times
===================================

With the realization that we could save almost 50% of our BullseyeCoverage
build times by only building the code of interest, we decided to find ways to
make it happen.

Our current process utilized a configuration file that would be picked up
when the compiler interceptor invoked [covc][covc]. This configuration file
would specify the [regions][region] to be captured in the resultant coverage
report. If one looks at the docs for [covc][covc], there is a mention for
exclusion regions:
> Normally you should use the Coverage Browser or covselect to exclude code
> rather than this option.
There is no clarification of why one might use the ``covselect`` tool over
exclusion regions.  

We specified only the code we cared about in the [regions][region], and
probably some of us thought that meant BullseyeCoverage would not bother
processing other files.  This was a false assumption.

Since we were migrating to CMake we decided to utilize the
[C_COMPILER_LAUNCHER][compiler_launcher].

[BullseyeCoverage]: https://www.bullseye.com/
[cov01]: https://www.bullseye.com/help/ref-cov01.html
[region]: https://www.bullseye.com/help/ref-regions.html
[covc]: https://www.bullseye.com/help/ref-covc.html
[compiler_launcher]: https://cmake.org/cmake/help/latest/prop_tgt/LANG_COMPILER_LAUNCHER.html

