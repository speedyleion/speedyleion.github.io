---
layout: post
title:  "Rust: Reusing Variable In Loop"
date:   2021-01-21 19:42:03 -0800
categories: rust git nom
---

The following chunk of code tries to parse a [git index][git-index] file. The
``Index::read_entry()`` function is meant to be reading out each file name
and it's respective SHA form the git index. The code was actually reading out
the first file entry over and over, for the number of files in the index. The
first file happened to be the ``.gitignore`` file.

{% highlight rust %}
pub fn new(path: &Path) -> Result<Index, GitStatusError> {
    let oid: [u8; 20] = [0; 20];
    let mut buffer: Vec<u8> = Vec::new();
    File::open(&path).and_then(|mut f| f.read_to_end(&mut buffer))?;
    let (contents, header) = Index::read_header(&buffer)?;
    let mut entries = vec![];
    for _ in 0..header.entries {
        let (contents, entry) = Index::read_entry(&contents)?;
        entries.push(entry);
    }
    let index = Index {
        path: String::from(path.to_str().unwrap()),
        oid,
        header,
        entries,
    };
    Ok(index)
}
{% endhighlight %}

The following line is meant to return the slice after the next entry and the
next entry. However each time it was processed in the loop it did not appear
to be updating ``contents`` to the location after the next entry.

{% highlight rust %}
let (contents, entry) = Index::read_entry(&contents)?; 
{% endhighlight %}

I had a couple of tests around ``Index::read_entry()``, but was missing a
test that ensured the returned value was after the next entry, so I added it.
I haven't had a chance to clean up the tests, there is a bit too much setup
repeated in each one. The important thing to look at is the ``suffix``
variable. It is placed after the file name in the ``u8`` vector, and the
assert assures that the function returns the slice for the ``suffix``, as
well as the file entry.

{% highlight rust %}
#[test]
fn test_read_of_file_entry_leaves_remainder() {
    let name= b"a/file";
    let sha = b"ab7ca9aba237a18e3f8a";
    let mut stream: Vec<u8> = vec![0; 40];
    stream.extend(sha);
    let name_length: u16 = name.len() as u16;
    stream.extend(&name_length.to_be_bytes());
    stream.extend(name);
    let suffix = b"what";
    stream.extend(suffix);
    let read = Index::read_entry(&stream);
    assert_eq!(
        read,
        Ok((&suffix[..], Entry {sha: *sha, name: String::from_utf8(name.to_vec()).unwrap()}))
    );
}
{% endhighlight %}

This test passed, so clearly the function was returning the ``&[u8]`` slice
after the next entry. I decided to focus on how I had written my attempt at
updating the value of ``contents``.

{% highlight rust %}
let (contents, header) = Index::read_header(&buffer)?;
let mut entries = vec![];
for _ in 0..header.entries {
    let (contents, entry) = Index::read_entry(&contents)?;
    entries.push(entry);
}
{% endhighlight %}

With a bit of investigation I finally realized the issue is the [let]
keyword. [let] declares new variables. Since the contents of the for loop is
in a new block there is a new ``contents`` variable declared which shadows
the original one. However each iteration the for loop's ``contents`` variable
hasn't been created yet so it re-uses the outer scope's ``contents`` variable
in the ``Index::read_entry``.

I tried to resolve this issue by declaring ``entry`` and then assigning:

{% highlight rust %}
for _ in 0..header.entries {
    let entry;
    (contents, entry) = Index::read_entry(&contents)?;
    entries.push(entry);
}
{% endhighlight %}

However this resulted in the following compilation error:

{% highlight rust %}
   |
88 |             (contents, entry) = Index::read_entry(&contents)?;
   |             ----------------- ^
   |             |
   |             cannot assign to this expression
   |
   = note: destructuring assignments are not currently supported
   = note: for more information, see https://github.com/rust-lang/rfcs/issues/372
{% endhighlight %}

It's nice that the compilation error directly links to the issue tracking
the implementation of destructuring assignments.

The final solution, create a local variable in the assignment and then assign
that to the ``contents`` variable.

{% highlight rust %}
for _ in 0..header.entries {
    let (local_contents, entry) = Index::read_entry(&contents)?;
    entries.push(entry);
    contents = local_contents;
}
{% endhighlight %}

[git-index]: https://git-scm.com/docs/index-format
[nom]: https://docs.rs/nom/6.0.1/nom/
[let]: https://doc.rust-lang.org/std/keyword.let.html
