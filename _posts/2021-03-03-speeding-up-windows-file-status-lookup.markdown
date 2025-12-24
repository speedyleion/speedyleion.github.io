---
layout: post
title:  "Speeding Up File Modification Time Lookup on Windows"
date:   2021-03-03 20:23:03 -0800
categories: rust git
---

> Some of this information has been revised. Be sure to read updated finding
  in [Efficientlly Walking File Directories in Rust (Part 2)]({% post_url
  2021-04-25-walking-file-directories-in-rust-part-2 %}).

File modification time, or `mtime` is a common value used to efficiently tell
if a file has changed. 

Build systems will look at the `mtime`s of the inputs and outputs of a build
target. If any of the input's `mtime`s are newer than the output(s) `mtime`
the build system knows to invoke the build step for the target.

Another use case is version control systems (VCS). In order to efficiently
determine which files may be out of date the version control system will look
at the `mtime` of the on disk files, any that are newer than it had
previously stored are likely changed compared to what's stored in the version
control system.

In particular I'm focusing on an attempt to implement a more efficient `git
status` for Windows, [win-git-status].

Baseline Performance
====================

The purpose of [win-git-status] is to be a more efficient version of 
`git status` on Windows. In particular when submodules are involved. To that
end it should match the performance of `git status` for repos without submodules.

For a large repo without submodules I chose to use [llvm-project] at commit
[0f9f0a40]. The repo and specific are more or less arbitrary, but the more
than 90k files provides a nice stress test.

On my machine with 6 cores (12 threads) and an SSD, I've taken timings using
`git status` as well as [libgit2].

| Command | Time (seconds) |
| ------- | ---- |
| `git status` | 0.340 |
| `lg2 status` | 1.228 |

The `git` version was `2.29.2.windows.2`. `lg2` was the example build from
version `1.1.0` of [libgit2].

[libgit2] performs ok, but I don't think it does threadying on it's own.
While the `git status` from git for Windows does use multi-threading.

Performance of [win-git-status]
-------------------------------

Using [std::fs::modified()][modified] resulted in 1.6 seconds to get the
`mtime` from the 90k files in commit [0f9f0a40]. Though this isn't too
far from the [libgit2] run it was more than 5 times worse than normal `git
status`.

I decided that it was worth investigating how to speed this up. Looking at
the profiling of running [win-git-status] every file was being opened.  See 
[Profiling Rust On Windows]({% post_url 2021-02-28-profiling-rust %}). It
seemed unnecessary to be opening every file just for the file modification
time.  

> I'll admit I don't know the underlying meaning of "opening" on Windows. So
> it may just be a generic way to access a resource and might not do extra
> work.

In an attempt to speed up the `mtime` retrieval. I attempted to write a C
wrapper that directly called [_stat] and friends. This resulted in more or
less the same performance. I next tried to call [GetFileAttributesExA]
directly in rust. This too resulted in about the same performance of 1.6
seconds.

I decided it was time to investigate what git, and in particular what git for
Windows might be doing. In doing some googling I ran across [fscache].

[fscache]
---------

I'm pretty sure [fscache] stands for "File Status Cache". 

When I initially ran across [fscache]. I thought it was an on disk cache of
the file `mtime`s. After looking into it more, it's actually an in memory
cache that is populated when an associated `git` operation is ran.

For example `git status` will look up the `mtime` of file `foo.c`. It will
request this value from the cache. The cache will not have this file yet, so
it will then get the `mtime` from the file system directly, storing it in the
cache as well as returning it to the caller.

[fscache] is enabled by default on newer versions of git for Windows. One can
see for themselves the performance. Simply time `git status`
normally. Then call `git config core.fscache false` and retime the `git
status` command.

Below is doing timings with and without [fscache] enabled on [0f9f0a40].

| fscache state | Time (seconds) |
| ------- | ---- |
| `core.fscache true` | 0.340 |
| `core.fscache false` | 2.231 |

> Be sure to turn the cache back on if you want to maintain performance 
> `git config core.fscache true`.

If one thinks about it some, there should be little to no reason that 
`git status` needs to get the `mtime` more than once per file. In fact my
timings of [win-git-status] were the result of getting the `mtime`s once.

I decided to look further into how [fscache] worked.

### [NtQueryDirectoryFile]

[fscache] utilizes [NtQueryDirectoryFile] to get the file `mtime`s. [fscache]
"open"s a directory to cache and then it makes successive calls to
[NtQueryDirectoryFile] to populate all the `mtime`s of the files in that
directory. 

The [ntapi] crate happens to provide this function. After some wrangling, I
was able to implement getting file `mtime`s utilizing [NtQueryDirectoryFile].
With the use of [NtQueryDirectoryFile], [win-git-status] can now get the
`mtime`s from commit [0f9f0a40] in 0.772 seconds. This is still a bit more
than 2x slower than `git status`, but I think this path has the potential to
close the gap.

My naive implementation using [NtQueryDirectoryFile] retrieved one directory
entry at a time. Looking more closely at the interface, it's possible to pass
a buffer and [NtQueryDirectoryFile] will provide an offset to subsequent
entries in the buffer. This means right now the prototype implementation is
calling back 90k times to get each file entry in the directory. While using a
buffer it's possible to minimize these calls and possible user to kernel
context switches.

If one looks closely at the implementation of [fscache], it is passing a
buffer and walking entries in the buffer when possible. I'm hopeful changing
[win-git-status] to utilize that approach of multiple entries per call to
[NtQueryDirectoryFile] will bring the time closer to the 0.340 seconds that
`git status` achieves.

Side Note
=========

I had mentioned in 
[Profiling Rust On Windows]({% post_url 2021-02-28-profiling-rust %}) 
how it was taking ~6 seconds to get the `mtime`s from commit [0f9f0a40]. This
is not the 1.6 seconds I mention above.

I had something similar to the following:

{% highlight rust %}
let walk_dir = WalkDirGeneric::<((usize),(bool))>::new("foo")
    .process_read_dir(|depth, path, read_dir_state, children| {
        // per directory processing
    });

for entry in walk_dir {
    // look up mtime
}
{% endhighlight %}

For those unfamiliar with [jwalk] it may not be apparent what's happening,
so we'll update some comments

{% highlight rust %}
let walk_dir = WalkDirGeneric::<((usize),(bool))>::new("foo")
    .process_read_dir(|depth, path, read_dir_state, children| {
        // per directory processing
        // happens on a separate thread per directory.
    });

for entry in walk_dir {
    // look up mtime
    // happens on the main thread
}
{% endhighlight %}

Basically the code I had written lost the benefit of the multithreaded
directory traversal provided by [jwalk] and was doing a lot of work on the
main thread.

Summary
=======

If performance is a concern when getting `mtime`s on windows, consider using
[NtQueryDirectoryFile]. It takes a little more work to implement, but the
performance is 5x or more (based on `git status`).

At least for `git status` [fscache] isn't so much about caching as it is
about how it gets the `mtime`s of files.

I'm not fond that my first decent attempt at rust has me needing to delve
into unsafe code, but I think the performance in this case justifies it.

[win-git-status]: https://github.com/speedyleion/win-git-status
[git-status]: https://git-scm.com/docs/git-status
[walkdir]: https://docs.rs/walkdir/2.3.1/walkdir/
[jwalk]: https://docs.rs/jwalk/0.6.0/jwalk/
[llvm-project]: https://github.com/llvm/llvm-project.git
[0f9f0a40]: https://github.com/llvm/llvm-project/commit/0f9f0a4046e11c2b4c130640f343e3b2b5db08c1
[libgit2]: https://libgit2.org
[WalkParallel]: https://docs.rs/ignore/0.4.17/ignore/struct.WalkParallel.html
[modified]: https://doc.rust-lang.org/std/fs/struct.Metadata.html#method.modified
[_stat]: https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/stat-functions?view=msvc-160
[GetFileAttributesExA]: https://docs.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileattributesexa
[fscache]: https://github.com/git-for-windows/git/blob/main/compat/win32/fscache.c
[NtQueryDirectoryFile]: https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntquerydirectoryfile
[ntapi]: https://docs.rs/ntapi/0.3.6/ntapi/