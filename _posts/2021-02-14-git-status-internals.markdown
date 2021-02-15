---
layout: post
title:  "Git Status Internals"
date:   2021-02-14 18:41:03 -0800
categories: git
---

For [win-git-status], I reached the point where I wanted to compare the
working tree files to the git index. I understood that git used [sha1] for
versioning both the file contents as well as other parts of a git repo. So I
decided to try and perform the [sha1] hash on every file in the working
tree. The time to hash quickly became a large bottle neck. I was using
[0f9f0a40] from the [llvm-project] which had 97912 files. I killed the
process after 30 seconds. `git status` only takes 0.340 seconds when run on
the commit [0f9f0a40]. 

I had mentioned in [Efficientlly Walking File Directories in Rust]({% post_url 2021-02-13-walking-file-directories-in-rust %})
how I should look into the actual `git status` implementation, it seemed that
now was the time.

[libgit2]
=========

I already had a clone of [libgit2] available and built. [libgit2] provides an
example [status] command that provides basic `git status` functionality, but
doesn't fully mimic it. With the [libgit2] examples built I was able to debug
how the command worked.

I created a simple repo with one file:

    mkdir simple_repo
    cd simple_repo
    git init
    echo "some text" > foo.txt
    git add foo.txt
    git commit -m "commiting one file"

This simple repo allowed be to minimize the debugging effort. I mean who
want's to walk through 90k file entries?



[git-book]: https://git-scm.com/book/en/v2
[sha1]: https://en.wikipedia.org/wiki/SHA-1
[win-git-status]: https://github.com/speedyleion/win-git-status
[git-status]: https://git-scm.com/docs/git-status
[jwalk]: https://docs.rs/jwalk/0.6.0/jwalk/
[llvm-project]: https://github.com/llvm/llvm-project.git
[0f9f0a40]: https://github.com/llvm/llvm-project/commit/0f9f0a4046e11c2b4c130640f343e3b2b5db08c1
[libgit2]: https://libgit2.org
[status]: https://libgit2.org/libgit2/ex/HEAD/status.html