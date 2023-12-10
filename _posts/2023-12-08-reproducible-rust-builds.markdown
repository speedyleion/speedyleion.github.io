---
layout: post
title:  "Debugging reproducible rust builds"
date:   2023-12-09 19:05:03 -0800
categories: rust build
---

This is a bit long as it's a summary of my one and half day debugging adventure.
I wanted to throw as much info out there to communicate that debugging isn't
often a 5 minute find it and fix it process.

# The background

We provide clients with signed versions of our rust binaries. The builds must be
reproducible so that anyone can verify the binary contents are from the
specified version of the source. A reproducible binary is one that results in
the exact same bytes. This requires using a consistent build environment and
tools.

# The Failure

I was making some optimizations to our build and I wanted to make sure that my
changes didn't affect the resultant binaries. When testing my optimizations I
could not reproduce the same binary.

The steps were more or less:

```console
> cargo clean
...
> cargo build --release
...
> md5sum target/release/my_binary
<SOME_MD5_VALUE>
> cargo clean
...
> cargo build --release
...
> md5sum target/release/my_binary
<A_DIFFERENT_MD5_VALUE>
```

Fortunately I was quick to think of checking out the tip of our mainline to
ensure I had the correct steps. To my surprise our mainline could not provide a
reproducible binary. 

I wanted to see if I could tell what was different between the binaries. I ran
across [elf_diff][elf_diff]. As the name implies it allows one to diff elf
binaries. Using it I could see that some [serde][serde] implementations appeared
to be different. For many the main change was around function address values. I
assumed this was due to surrounding functions increasing or decreasing in size
changing the function addresses. A couple of functions I found had some
different assembly instructions, but I'm not that fluent in assembly to quickly
understand what it might mean. I decided to shelve that for now.

I thought for a bit, and was pretty sure our latest release had reproducible
binaries. Running the above steps on the latest released version did indeed
provide a reproducible binary. 

So somewhere between our latest release and our current mainline we lost
reproducible rust builds.

I was familiar with many of changes that happened since the latest release. I
recalled we had bumped rust versions, so I decided to look there first. I
tried to revert the rust version bump at the tip of mainline. I spent
probably 30 minutes to an hour trying to revert the rust version. Then I
realized I should just check out the commit prior to the rust version bump and
test build reproducibility there.

The commit at the old rust version also failed to provide reproducible builds. I
tried to think of what other changes could be the likely culprit. As I was
thinking this over a thought finally came into my head. 

> I should use git bisect!

[git bisect][bisect] does a binary search through your commit history to find
the point when the breaking change happened. For this to be effective the commit
history has to be one that most, if not all, commits are building commits. I've
seen some code bases where people push non working changes into the mainline and
every week or month someone comes along and gets it building again. These types
of code bases probably aren't a good candidate for `git bisect`. 

It took eight iterations of `git bisect` to locate the commit that first broke
reproducible builds. This commit was pulling in functionality from a new crate
we had developed elsewhere. This new crate provided a rust wrapper around a
third party C library. Fortunately this commit was only integrating a small
piece of the new crate. Subsequent commits hooked up the rest of this new crate.

Working on the broken commit, I tried to remove small pieces of the integration
and rebuild looking for reproducibility. For instance pulling in the new crate
resulted in cargo updating serde, and since I saw those implementations in
`elf_diff` I tried to pin the serde version back to see what the outcome might
be.  Much like my attempt to revert the rust versions, this wasn't a good
approach. I realized it would be better to start from the commit prior, which
worked, and then slowly add small pieces of the change until I lose reproducible
builds. The reason for this is that if you start from a broken version and try
to undo things, it's possible that when you go to test, you test incorrectly and
it's your testing method that is the cause of a failure instead of the actual
change.

As mentioned this new crate was a wrapper around a C library. We followed the
[sys-packages][sys] recommendation. Which means we actually have two crates; a
`foo` crate which provides the idiomatic rust interface and a `foo-sys` crate
which does some very basic mapping of C to rust. In the `foo-sys` crate we use
[bindgen][bindgen] to generate the rust interface from the C headers. We also
derived `Serialize` and `Deserialize` from serde on some of the `foo-sys` types.

Again latching on to the `serde` functions in the `elf_diff` output, I decided
to use [cargo-expand][cargo-expand] on `foo-sys`. `cargo-expand` will take rust
files and expand all of the macros in those files.  This is similar to looking
at C's pre-processed output. I was hoping to see a giant on/off switch in the
wrong position in the output, but nothing stood out to me. I ran it twice and
compared the output, it was the same each time. 

I realized that the `foo` crate is really the one used by the clients and it
hides the `foo-sys` crate from them. So I also ran `cargo-expand` on it. Again 
nothing grabbed my attention. Running it twice however resulted in different
output. Some of the derived functions moved around. I don't know how well
`cargo-expand` integrates with cargo and rustc so figured it might be expanding
in parallel and piecing together itself.

At this point I decided to use the last known good commit and start manually
pulling over the pieces of `foo` into the problem binary. The idea was to leave
all of `foo` out as a dependency copying over small pieces of code directly into
the problem crate. In doing this, I was skipping `bindgen` and manually
implementing the C interfaces. Working this way for a bit, I was unable to get
the non reproducible build to occur.

After a bit of this, my battery decided it had enough, and I decided it was time
for a walk.

# The Cause

As often happens, I only had to start getting ready for a walk when the pieces
started to come together in my head. Sort of like the ending of "The Usual
Suspects".

<iframe width="1038" height="441" src="https://www.youtube.com/embed/LtSldnuKBEs" title="The Usual Suspects (1995) - &quot;The Greatest Trick&quot;/ending scene [1080]" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

As I had mentioned in `foo-sys` we derived `Serialize` and `Deserialize` on some
of the C types. To do this we used `bindgen`'s [add_derives()][add_derives]
method. The implementation looked something like.

```rust
    fn add_derives(&self, info: &DeriveInfo<'_>) -> Vec<String> {
        let mut derives = HashSet::new();
        if self.some_case(info) {
            derives.insert("Clone");
        }
        if self.other_case(info) {
            derives.insert("Serialize");
        }
        ...
        derives.into_iter().map(String::from).collect::<Vec<_>>()
    }
```

We used a set to make it easier to have two cases that might want `Clone`.
If you tried to use a vector directly and you passed two `Clone`s then the
compilation would bark at the `bindgen` produced:

```rust
#[derive(Clone, Clone)]
pub MyStruct {
    a: u32,
    b: float
}
```

I had mentioned how `elf_diff` had shown diffs on `serde` implementations and
that we happened to derive `Serialize` and `Deserialize` on some types. I also
mentioned how the derives were reordered in one of the runs of `cargo-expand`.

Unfortunately one has to look at the docs for [`HashMap`][hash_map] to
find the clue, but rust's [`HashSet`][hash_set] uses the same default hasher.

> By default, HashMap uses a hashing algorithm selected to provide resistance
> against HashDoS attacks. The algorithm is randomly seeded, and a reasonable
> best-effort is made to generate this seed from a high quality, secure source
> of randomness provided by the host without blocking the program. 

This means that the hashing algorithm is randomly seeded on each run and thus
the hash values are not consistent between runs. The result was that the order
of the derives on the generated output of `bindgen` would vary between builds.

For example one can run the following code and half the time the assert will
cause a panic. Unscientific, but I can usually get a pass or panic within four
runs.

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=use+std%3A%3Acollections%3A%3AHashSet%3B%0Afn+main%28%29+%7B%0A++++let+mut+derives+%3D+HashSet%3A%3Anew%28%29%3B%0A++++derives.insert%28%22Debug%22%29%3B%0A++++derives.insert%28%22Clone%22%29%3B%0A++++assert_eq%21%28derives.into_iter%28%29.collect%3A%3A%3CVec%3C_%3E%3E%28%29%2C+vec%21%5B%22Debug%22%2C+%22Clone%22%5D%29%3B%0A%7D"></iframe>

To fix this inconsistent order one can:
- [`sort`][sort] the vector before returning it.
- use [`BTreeSet`][btree_set] which will provide a consistent order across runs.
- use a stable hasher instead of the default one.

# Summary

To ensure reproducible builds avoid direct use of the default hasher in
generated code.

When debugging try to start from a good known state and then slowly bring it
into the error state.

[btree_set]: https://doc.rust-lang.org/stable/std/collections/struct.BTreeSet.html
[sort]: https://doc.rust-lang.org/std/vec/struct.Vec.html#method.sort
[hash_map]: https://doc.rust-lang.org/std/collections/struct.HashMap.html
[hash_set]: https://doc.rust-lang.org/std/collections/struct.HashSet.html
[add_derives]: https://docs.rs/bindgen/0.69.1/bindgen/callbacks/trait.ParseCallbacks.html#method.add_derives
[cargo-expand]: https://github.com/dtolnay/cargo-expand
[bindgen]: https://docs.rs/bindgen/0.69.1/bindgen/
[sys]: https://doc.rust-lang.org/cargo/reference/build-scripts.html#-sys-packages
[elf_diff]: https://github.com/noseglasses/elf_diff
[bisect]: https://git-scm.com/docs/git-bisect
[serde]: https://github.com/serde-rs/serde