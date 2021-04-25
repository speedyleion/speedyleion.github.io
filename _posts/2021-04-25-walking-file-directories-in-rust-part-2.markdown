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

The reason for walking the directory twice was, because accessing a file's
modified time via [std::fs::modified()][modified] showed a significant time
cost. I double checked that [jwalk] itself didn't happen to propagate the
modified time. One can see that the [jwalk::DirEntry::from_entry()][DirEntry]
method copies some fields from the ``fs::DirEntry`` struct, but it happens to
omit the `metadata`, which containes the modified time.

With the realization that the use of [jwalk] was causing me to go to the file
system twice I decided to re-visit the topic of [Efficientlly Walking File
Directories in Rust]({% post_url 2021-02-13-walking-file-directories-in-rust
%})

Directory Walking (with examples)
=================================

With a bit more knowledge in rust and with my desire 

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