---
layout: post
title:  "C/C++ code generator in MSBuild (Part 0)"
date:   2021-01-26 18:59:03 -0800
categories: msbuild build-systems python
---

A while back I had need to create a C code generator for MSBuild. The desire
was to integrate with a native Visual Studio project. 

This series of posts will cover how to create an MSBuild task that invokes a
code generator which has unknown include dependencies. There will be a mix of
languages:
* C#, for the build task
* MSBuild XML, for integrating the build task with MSBuild and thus Visual
  Studio
* Python, code generator (Sorry about adding another, it just happens to be my
  go to language for these kinds of things.)
* C/C++, for the basic project example

First, a brief overview of common ways one may integrate a code generator with
MSBuild.

Custom Build Steps
==================

For simple code generators one can get away with using a 
[custom build step][custom-build-steps]. These are convenient in that they
can be easily set up through the Visual Studio GUI.
![Custom Build Step](/assets/custom_build_step_property_page.png)
For a code generator, one would need to ensure that the build step is
performed prior to the code compilation.

Custom build steps have a few limitations:
* There is no easy way to update dependencies at build time. So if the code
  generator includes other files as dependencies these must be known before
  hand and updated manually if any includes change.
* The GUI doesn't provide an easy way to tie the output as an input to the
  compilation phase.

Experience has shown that people start with a simple code generator and a
custom build step. Then as their code generator gets more complex the code
generator itself starts to turn into a mini build system due to the
limitations of a custom build step. Finally they may force the code generator
to always run in order to ensure it picks up dependencies that weren't able
to be communicated through the custom build step. Then the code generator
will conditionally output code only if it changed, so that anything it
depends on doesn't unnecessarily compile.

Just like the compiler will always turn a code file into an object file, a
code generator should always generate the code. The build system should
decide if and when the code generator runs.

Tasks
=====

Tasks are the MSBuild term for operations performed as part of the build. A
colleague of mine once said
> A build system can be thought of as a task scheduler

This quote and MSBuild's use of the term *task* seem to corroborate each
other.

MSbuild itself is pretty generic. I believe most if not all of the build
operations performed by MSBuild are done via pre-packaged tasks in dlls.
These tasks just happen to normally be loaded by the common projects people
use.

Using tasks requires more work, in that one must implement a C# class and
provide either a dll or inline the code into the build files. However, tasks
provide the full capabilities of the .Net framework as well as allowing one
to determine dependencies at build time.

The approach taken in this series will be to utilize a task and go through
the steps of developing, integrating and debugging a code generator
implemented as a task.

Resources
=========

These resources will be used throughout this series.

* [MSBuild Docs][msbuild]. This should be all that you really need. Though the
  other resources may explain things better at times.
* [Inside the Microsoft Build Engine: Using MSBuild and Team Foundation Build][msbuild-book] 
* [MSBuild Trickery: 99 Ways to Bend the Build Engine to Your Will][msbuild-trickery]
  This is more or less a cookbook of techniques, but it has my favorite quote from
  one of the MSBuild authors.
  > We based the syntax on XML, believing that great tools would quickly
  > appear so that nobody would have to type it. They haven't appeared yet.
  > Sorry about that.
* [Implementing and Debugging Custom MSBuild Tasks][debugging-msbuild-tasks]. I
  wish this was written when I initially went down this path.
* [Demystifying Fast Up To Date Check][fast-up-to-date-check]


[msbuild]: https://docs.microsoft.com/en-us/visualstudio/msbuild/msbuild
[msbuild-book]: https://www.amazon.com/Inside-Microsoft-Build-Engine-Foundation-dp-0735645248/dp/0735645248
[msbuild-trickery]: https://www.amazon.com/MSBuild-Trickery-Ways-Build-Engine/dp/061550907X
[debugging-msbuild-tasks]: https://ithrowexceptions.com/2020/08/04/implementing-and-debugging-custom-msbuild-tasks.html
[custom-build-steps]: https://docs.microsoft.com/en-us/cpp/build/understanding-custom-build-steps-and-build-events
[fast-up-to-date-check]: http://zhylich.blogspot.com/2016/03/demystifying-fast-up-to-date-check-in.html