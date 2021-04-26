---
layout: post
title:  "Efficientlly Walking File Directories in Rust (Part 2)"
date:   2021-04-25 13:45:03 -0700
categories: rust git
---

This post is meant to follow on from [Efficientlly Walking File Directories
in Rust]({% post_url 2021-02-13-walking-file-directories-in-rust %}) and 
correct some innaccuracies in [Speeding Up File
Modification Time Lookup on Windows]({% post_url
2021-03-03-speeding-up-windows-file-status-lookup %}).

Again the overall goal of the 2 mentioned posts was to find a way to
efficiently get the file modification times for all the files in a directory
tree.

Only Look Once
==============

It took me a bit to realize, but the logic I was using was actually walking
the directory structure twice:

1. [jwalk] was used as a threaded way to get the names and types of each file
   in each directory.
2. [NtQueryDirectoryFile] was used to get the modification times of the files
   that were provided by [jwalk].

File I/O is generally slower than most other CPU processing. So in general
only walking a directory once should show a decent improvement.  

Accessing the files in each directory twice was happening becuase a direct
call to get a file's modified time via [std::fs::modified()][modified] showed
a significant time cost.  I double checked that [jwalk] itself didn't happen
to propagate the modified time.  One can see that the
[jwalk::DirEntry::from_entry()][DirEntry] method copies some fields from the
``std::fs::DirEntry`` struct, but it happens to omit the `metadata`, which
contains the modified time.

With the realization that the use of [jwalk] was causing me to go to the file
system twice I decided to re-visit the topic of [Efficientlly Walking File
Directories in Rust]({% post_url 2021-02-13-walking-file-directories-in-rust
%})

Directory Walking (with examples)
=================================

With a bit more knowledge in rust and with my desire to better back up my
understanding with metrics I created,
https://github.com/speedyleion/rust_directory_walking.  This provides a
simple executable that times the walking of directory using different
approaches.

```
   $ ./target/release/directory_walking.exe /c/git/llvm-project/
   The jwalk time 163.6281ms, and the files 107593
   The ntquery_walk_dir time 185.8282ms, and the files 108404
   The walk_dir_path_is_dir time 638.7077ms, and the files 108450
   The walk_dir time 631.5173ms, and the files 108450
   The walk_dir_threaded time 147.7341ms, and the files 108451
```

This was a run against the [llvm-project] using commit [0f9f0a40].

* `jwalk` is using the [jwalk] crate.
* `ntquery_walk_dir` is my attempt at leveraging [NtQueryDirectoryFile] as I
  documented in [Speeding Up File Modification Time Lookup on Windows]
  ({% post_url 2021-03-03-speeding-up-windows-file-status-lookup %}).  More
  on this later.
* `walk_dir_path_is_dir` is using the basic example provided in the rust docs
  for [std::fs::read_dir()][read_dir]
* `walk_dir` slightly modifies the [std::fs::read_dir()][read_dir]
  example to use `is_dir()` from [std::fs::FileType].  More on this later.
* `walk_dir_threaded` is utilizing [rayon::scope] to provide threading around
  [std::fs::read_dir()][read_dir].

And a nice table form:

| method | Time (ms) | files reported |
| ------- | ---- |------|
| `jwalk` | 163.6281 | 107593 |
| `ntquery_walk_dir` | 185.8282 | 108404 |
| `walk_dir_path_is_dir` | 638.7077 | 108450 |
| `walk_dir` | 631.5173 | 108450 |
| `walk_dir_threaded` | 147.7341 | 108451 |


`ntquery_walk_dir`
------------------

The results of this version contradicts many of my claims made in
[Speeding Up File Modification Time Lookup on Windows] ({% post_url
2021-03-03-speeding-up-windows-file-status-lookup %}).

I double checked the implementation of [std::fs::read_dir()][read_dir] in
the hopes that maybe it was using [NtQueryDirectoryFile] on the backend and
was just more efficient than my attempt.  


Rust Windows `metadata`
-----------------------

As documented on the [fs::DirEntry::metadata()][metadata]:

> On Windows this function is cheap to call (no extra system calls needed),
but on Unix platforms this function is the equivalent of calling
symlink_metadata on the path.

[jwalk]: https://docs.rs/jwalk/0.6.0/jwalk/
[DirEntry]: https://github.com/jessegrosjean/jwalk/blob/master/src/core/dir_entry.rs#L44
[NtQueryDirectoryFile]: https://docs.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntquerydirectoryfile
[modified]: https://doc.rust-lang.org/std/fs/struct.Metadata.html#method.modified
[metadata]: https://doc.rust-lang.org/std/fs/struct.DirEntry.html#method.metadata
[llvm-project]: https://github.com/llvm/llvm-project.git
[0f9f0a40]: https://github.com/llvm/llvm-project/commit/0f9f0a4046e11c2b4c130640f343e3b2b5db08c1
[read_dir]: https://doc.rust-lang.org/std/fs/fn.read_dir.html
[std::fs::FileType]: https://doc.rust-lang.org/std/fs/struct.FileType.html
[rayon::scope]: https://docs.rs/rayon/1.5.0/rayon/fn.scope.html