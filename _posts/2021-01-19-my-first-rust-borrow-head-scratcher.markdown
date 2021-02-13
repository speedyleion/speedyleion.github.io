---
layout: post
title:  "My first rust borrow head scratcher"
date:   2021-01-19 18:47:03 -0800
categories: rust git
---

The Problem
===========

I'm fairly new to rust, having only read through the [rust book][rust-book]
and a bit of the [nom docs][nom].

I spent more time than I care to admit trying to debug the following
borrow issue:
{% highlight rust %}
90 |         let (contents, header) = Index::read_header(&buffer)?;
   |                                                     ------- ^ returns a value referencing data owned by the current function
   |                                                     |
   |                                                     `buffer` is borrowed here
{% endhighlight %}

This error appeared when I tried to connect reading from a file to functions
that could parse some parts of a [git index file][git-index]. The unit tests
for the ``read_header`` function worked fine with no compilation or run time
errors. It was only when I started to connect to a file that the compilation
error reared it's head.

The new function I was writing, and the ``read_header`` function: 
(Did I mention I'm new to rust, I'm sure this is pretty rough for most
rustaceans)
{% highlight rust %}
pub fn new(path: &Path) -> Result<Index, GitStatusError> {
    let mut file = File::open(path)?;
    let metadata = file.metadata()?;
    let mut buffer:Vec<u8> = vec![0; metadata.len() as usize];
    file.read(&mut buffer)?;
    let (contents, header) = Index::read_header(&buffer)?;
    let mut entries = vec![];
    for _ in 0..header.entries {
        let (contents, entry) = Index::read_entry(contents)?;
        entries.push(entry);
    }
    let index = Index {
        header,
        entries,
    };
    Ok(index)
}

fn read_header(stream: &[u8]) -> IResult<&[u8], Header> {
    let signature = tag("DIRC");

    let (input, (_, version, entries)) = tuple((signature, be_u32, be_u32))(stream)?;

    Ok((input, Header { version, entries }))
}

{% endhighlight %}

How I Debugged
==============

After a bit of head scratching I decided I needed to try and come up with a
minimal example that reproduced the issue. I've had experience with the 
[bmp file format][bmp-format], so I decided to parse a few bytes from a
bmp file.  I created a new cargo package with only a ``main.rs``.

Here is the bmp file parsing in all it's glory:
{% highlight rust %}
use std::fs::File;
use std::io::Read;

use nom::bytes::complete::tag;
use nom::number::complete::le_u32;
use nom::sequence::tuple;
use nom::IResult;

fn read_size(stream: &[u8]) -> IResult<&[u8], u32> {
    let signature = tag(b"BM");
    let (input, (_, size)) = tuple((signature, le_u32))(stream)?;
    Ok((input, size))
}

fn read_offset(stream: &[u8]) -> IResult<&[u8], u32> {
    let (input, (_, offset)) = tuple((le_u32, le_u32))(stream)?;
    Ok((input, offset))
}

fn read_bmp_info(file: &str) -> (u32, u32) {
    let mut buffer: Vec<u8> = Vec::new();
    File::open(&file).and_then(|mut f| f.read_to_end(&mut buffer)).unwrap();
    let (contents, size) = read_size(&buffer).unwrap();
    let (_, offset) = read_offset(&contents).unwrap();
    (size, offset)
}
fn main() {
    for file in std::env::args().skip(1) {
        let (size, offset) = read_bmp_info(&file);
        println!("{} and {}", size, offset);
    }
}
{% endhighlight %}

This code compiles and runs just fine.  Now it's time to start comparing...

It still took me awhile to see it, but if you look at the simple bmp file
parsing I used ``unwrap()``. I didn't care about propagating errors, I just
wanted to quickly get something working.  

So I updated ``read_header`` to also use ``unwrap()`` instead of the
[question mark operator][question-mark]:
{% highlight rust %}
    let (contents, header) = Index::read_header(&buffer)?;
{% endhighlight %}
to
{% highlight rust %}
    let (contents, header) = Index::read_header(&buffer).unwrap();
{% endhighlight %}
this got past the borrow compiler error???

I didn't show it earlier as it would have stood out a bit with the rest of
the code, but you can see that the ``new`` function ritten returns a result
with an error type:
{% highlight rust %}
pub fn new(path: &Path) -> Result<Index, GitStatusError>
{% endhighlight %}
And if we look at how that error type was defined as:
{% highlight rust %}
pub enum GitStatusError<'a> {
    IO(io::Error),
    Nom(nom::Err<nom::error::Error<&'a[u8]>>),
}
{% endhighlight %}
There is a [lifetime][lifetimes] specified for the u8 slice in the [nom][nom]
error wrapper. The lifetime came about due to me blindly obeying the
following compiler error:
{% highlight rust %}
   |
27 |     Nom(nom::Err<nom::error::Error<&[u8]>>),
   |                                    ^ expected named lifetime parameter
   |
help: consider introducing a named lifetime parameter
   |
25 | pub enum GitStatusError<'a> {
26 |     IO(io::Error),
27 |     Nom(nom::Err<nom::error::Error<&'a [u8]>>),
   |
{% endhighlight %}
This is mainly a lack of my rust experience. I had a general idea of what
[lifetimes][lifetimes] were, but didn't really understand the implications
in this instance.

The Reason for the Compiler Error
=================================

As I now understand the problem:
- ``new`` could return a ``nom`` variant of ``GitStatusError``
- the ``nom`` variant of ``GitStatusError`` used the u8 slice
- The u8 slice was local to ``new``

This means that the code was trying to send the local slice outside of
``new``, when there was an error. When I changed to ``unwrap()`` this
prevented the possibility of an error that referenced the u8 slice and thus
avoided the borrow error.

Update (2021-01-20)
===================

The same night, after I wrote this post, my google fu uncovers a stack
overflow question someone had almost two years prior. The SO question is the
same underlying issue,
[https://stackoverflow.com/questions/55184864/nom-parser-borrow-checker-issue].
The author of the post has a much more consise example of the issue and I'm
assuming the answer is from a more experienced rust person.

[rust-book]: https://doc.rust-lang.org/book/ 
[nom]: https://docs.rs/nom/6.0.1/nom/
[git-index]: https://git-scm.com/docs/index-format
[bmp-format]: https://en.wikipedia.org/wiki/BMP_file_format
[lifetimes]: https://doc.rust-lang.org/1.9.0/book/lifetimes.html
[question-mark]: https://doc.rust-lang.org/edition-guide/rust-2018/error-handling-and-panics/the-question-mark-operator-for-easier-error-handling.html
[https://stackoverflow.com/questions/55184864/nom-parser-borrow-checker-issue]: https://stackoverflow.com/questions/55184864/nom-parser-borrow-checker-issue