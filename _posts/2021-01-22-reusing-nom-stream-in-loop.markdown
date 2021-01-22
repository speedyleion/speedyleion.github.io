---
layout: post
title:  "Reusing Nom Stream In Loop"
date:   2021-01-21 10:42:03 -0800
categories: rust git nom
---

The [nom] crate is used in this post. The important thing to know about it
is that the functions being created for parsing with [nom] take an input
``&[u8]`` and return an ``IResult<&[u8], thing_parsed>``, where
``thing_parsed`` depends on the function.

The following chunk of code tries to parse a [git index][git-index] file. The
``Index::read_entry()`` function is meant to be reading out each file name
and it's respective SHA form the git index. As written the code was actually
reading out the first file entry over and over, fro the number of files in
the index. The first file happend to be the ``.gitignore`` file.

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

I had a couple of tests around ``Index::read_entry()``, but was missing one
that ensured the returned stream from the parser function was after the
parsed data, so I added it.

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
after the file entry. I decided to focus on my attempt at re-using the
variable name of ``contents``.
{% highlight rust %}
    let (contents, header) = Index::read_header(&buffer)?;
    let mut entries = vec![];
    for _ in 0..header.entries {
        let (contents, entry) = Index::read_entry(&contents)?;
        entries.push(entry);
    }
{% endhighlight %}


[git-index]: https://git-scm.com/docs/index-format
[nom]: https://docs.rs/nom/6.0.1/nom/