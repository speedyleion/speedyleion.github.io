---
layout: post
title:  "Efficientlly Walking File Directories in Rust"
date:   2021-02-13 09:47:03 -0800
categories: rust git
---

Working on [win-git-status] I have a need to walk all files in a directory
for building up the working tree. The main design goal of [win-git-status] is
a faster implementation of [git status][git-status]. To this end it's not
just about walking all the files in a directory, but trying to find an
efficient method.

Baseline Metrics
================

In order to have a decent baseline to compare different directory walking
methods, I cloned the [llvm-project] and used commit [0f9f0a40]. I then took
a few commands that I felt were efficient at directory walking and compare
the times.

> I'll be shamefully honest here, for any and all times in this post I use
the "eyeball median". This means I run the command a few times, probably 5-8,
and choose what looks to be the median. I really need to start dumping these
timings into a spreadsheet app and just property average them.

| Command | Time (seconds) |
| ------- | ---- |
| `git status` | 0.340 |
| `fd > foo.log` | 1.120 |
| `fd -I > foo.log` | 0.910 |
| `lg2 status` | 1.228 |

The `git` version was `2.29.2.windows.2`. The `fd` version was `8.1.1`. `lg2`
was the example build from version `1.1.0` of [libgit2].  

To give an idea of the repo size `git ls-files | wc -l` resulted in `97912`
file entries.

I was surprised to see that `git status` was so fast on this large of a repo.
I probably need to look into the actual `git status` implementation more. My
understanding is that it's single threaded and that it has to do a SHA1 on
all the files. Maybe there is a caching mechanism going on.

One of the reasons of writing [win-git-status] is for better handling of
submodules. Once submodules are thrown into the mix `git status` will launch
new Windows processes. The Windows process are expensive to launch and happen
to make virus scanners, and other security tools, get a bit upity. Even
knowing that submodules is the main slow point I've seen on Windows, having
an implementation be slower than `git status` on other repos should be
avoided.

Deeper into [fd]
----------------

The speed of [fd] compared to `git status` was another surprise to me. I
thought for sure it would have outperformed `git status`, yet it's almost 3
to 4 times slower. So I took a little detour trying to figure out if it was
something with [fd] or something I was doing (TL;DR it was me). I don't
recall where I ran across it, but I saw someone doing metrics by redirecting
to `/dev/null`. So I gave `/dev/null` a try.

| Command | Time (seconds) |
| ------- | ---- |
| `fd > /dev/null` | 0.614 |

Redirecting to `/dev/null` was almost a 2x speed improvement. Apparently my
timings were greatly skewed by the time to write to a file. Doing further
investigation I was able to see that [fd] supported using threads, and I
decided to throw in skipping over common ignore files.

| Command | Time (seconds) |
| ------- | ---- |
| `fd -I > /dev/null` | 0.400 |
| `fd -j 1 -I > /dev/null` | 0.847 |
| `fd -j 2 -I > /dev/null` | 0.511 |
| `fd -j 3 -I > /dev/null` | 0.396 |
| `fd -j 4 -I > /dev/null` | 0.356 |
| `fd -j 5 -I > /dev/null` | 0.362 |
| `fd -j 6 -I > /dev/null` | 0.390 |

Using values from 6 to 12 for the `-j` flag often hovered between 0.390s and
0.400s. It looks like [fd] uses 12 threads by default on my machine:

    Processor	Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz, 2592 Mhz, 6 Core(s), 12 Logical Processor(s)

Without looking directly at the code, my guess would be that [fd] uses as
many threads as the system has available.

It occurred to me that if searching for everything and redirecting to a
physical file was so time consuming, maybe there was a decent amount of time
spent just building up the list of files. I mean it's probably some kind of
vector that has to keep growing as files are added, thus causing memory
re-allocations.  So I further refined the [fd] timing command:

| Command | Time (seconds) |
| ------- | ---- |
| `fd 'bkl` | 0.534 |
| `fd -I 'bkl` | 0.238 |
| `fd -j 4 -I 'bkl'` | 0.312 |
| `fd --no-ignore-vcs 'bkl'` | 0.324 |

The string `bkl` is just jibberish that didn't match any files in the
[llvm-project]. The `fd -I 'bkl'` command is now faster than `git status`,
however it's doing less than `git status`. I only did a run of `-j 4` since
that was the fastest run when re-directing to `/dev/null`. We can see that
the default 12 threads is now performing better. Just for fun I decided to
time against `--no-ignore-vcs`. The `-I` also omits `.ignore` file entries. I
double checked my machine, I don't have any `.ignore` entries. It's
interesting that it took over 25% of the time, 0.088s, to look for non
existent `.ignore` files when using the `--no-ignore-vcs` flag.

Looking at Rust Crates
======================

I figured there should already be a rust crate or two that performed
directory walking, especially since [fd] is written in rust. I ended up
finding three posibilites:

- [walkdir]
- [ignore]
- [jwalk]

[walkdir]
---------

[walkdir] provides a nice simple iterator api for navigating the files in a directory: 


{% highlight rust %}
use walkdir::WalkDir;

for entry in WalkDir::new("foo") {
    println!("{}", entry?.path().display());
}
{% endhighlight %}

[walkdir] comes with a `walkdir-list` module that provides some basic CLI
functionality. `walkdir-list` was used to approximage the [walkdir] speed.

[ignore]
--------

[ignore] is the crate used by [fd]. [ignore] also happens to use [walkdir]
under the hood.  [ignore] provides a simple iterator interface:

{% highlight rust %}
use ignore::WalkBuilder;

for result in WalkBuilder::new("foo") {
    println!("{:?}", result);
}
{% endhighlight %}

The [ignore] crate has knowledge of git ignore files and will omit files that are ignored.
[ignore] also provides a parallel threaded interface, [WalkParallel].  

The parallel capabilities and knowledge of git ignore files seems like a good
candidate for using in a tool used for git operations. Due to my limited rust
knowledge fully leveraging the parallel interface may take a while.

[jwalk]
-------

[jwalk] almost flew under my radar. It can provide a nice iterator
interface, while doing the walking in parallel.

{% highlight rust %}
use jwalk::{WalkDir};

for entry in WalkDir::new("foo") {
  println!("{}", entry?.path().display());
}
{% endhighlight %}

[jwalk] does mention that it parallelizes each directory. This means if one
has a flat directory structure the performance may suffer. However, for git
operations where there may be a per directory ignore and attributes file it
seems like this per directory parallelism might actually be beneficial.

Timing of the Crates
--------------------

| Crate | Time (seconds) |
| ------- | ---- |
| [walkdir] `walkdir-list -c` | 0.700 |
| [ignore] `WalkBuilder` | 2.420 |
| [ignore] `WalkBuilder.build_parallel()` | 1.123 |
| [ignore] `WalkBuilder.build_parallel(1)` | 1.921 |
| [ignore] `WalkBuilder.build_parallel(2)` | 1.119 |
| [ignore] `WalkBuilder.build_parallel(3)` | 0.860 |
| [ignore] `WalkBuilder.build_parallel(4)` | 0.715 |
| [ignore] `WalkBuilder.build_parallel(5)` | 0.636 |
| [ignore] `WalkBuilder.build_parallel(6)` | 0.590 |
| [ignore] `WalkBuilder.build_parallel(7)` | 0.562 |
| [ignore] `WalkBuilder.build_parallel(8)` | 0.550 |
| [ignore] `WalkBuilder.build_parallel(9)` | 0.535 |
| [ignore] `WalkBuilder.build_parallel(10)` | 0.520 |
| [ignore] `WalkBuilder.build_parallel(11)` | 0.505 |
| [ignore] `WalkBuilder.build_parallel(12)` | 0.500 |
| [jwalk] | 0.228 |

Conclusion
==========

This was a bigger detour than I probably should have taken. It is probably
walking the line, if not outright, premature optimization. I don't even
have an implementation of building up a git worktree, yet I'm already
profiling it. Most of the crates support a visitor pattern and so it probably
doesn't matter too much which one is initially chosen as long as it isn't
tightly coupled.

Due to the simplicity of the iterator in [jwalk], as well as the significant
speed difference between it and the initial usage of the [ignore] crate's
[WalkParallel], it just seems [jwalk] may be a better way to start. Using
[jwalk] means that I will need to explicitly handle git ignore files, however
it looks like the [ignore] crate's git ignore logic is public so I should
still be able to leverage that work.

I didn't go into detail here, but I want to better understand when and where
to best use async for file I/O. Not fully understanding this stack overflow
suggestion
[https://stackoverflow.com/a/58825638/4866781](https://stackoverflow.com/a/58825638/4866781),
I tested it out resulting in ~4 seconds to complete in the [llvm-project]. So
I quickly shelved the async investigation for now.

[win-git-status]: https://github.com/speedyleion/win-git-status
[git-status]: https://git-scm.com/docs/git-status
[walkdir]: https://docs.rs/walkdir/2.3.1/walkdir/
[ignore]: https://docs.rs/ignore/0.4.17/ignore/
[jwalk]: https://docs.rs/jwalk/0.6.0/jwalk/
[llvm-project]: https://github.com/llvm/llvm-project.git
[0f9f0a40]: https://github.com/llvm/llvm-project/commit/0f9f0a4046e11c2b4c130640f343e3b2b5db08c1
[fd]: https://github.com/sharkdp/fd
[libgit2]: https://libgit2.org
[WalkParallel]: https://docs.rs/ignore/0.4.17/ignore/struct.WalkParallel.html