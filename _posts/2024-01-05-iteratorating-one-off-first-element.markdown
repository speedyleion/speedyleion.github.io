---
layout: post
title:  "Iterating: special handling of first element"
date:   2024-01-05 20:00:03 -0800
categories: rust iterators
---

There are times where I need to iterate through some items and the first element
in iterator has some special handling.

A simple example is joining a slice of `str`. One wants to go from:

```rust
["a", "b", "c"]
```

and get:

```rust
"a + b + c"
```

I understand that for this specific example one could use the [join()][join]
method on slice:

```rust
let joined = ["a", "b", "c"].join(" + ");
```

The intent isn't to implement a better join, but to focus on the special
handling around the first element of an iterator. It's also possible that
someone is in a no alloc environment, in these instances they wouldn't have
[join()][join] available to them as it returns a `String`, which requires alloc.

I'll walk through 4 ways this could be implemented (I'm sure there are many more):

1. Using a boolean flag to know if we've seen the first element
2. Keying off of the index
3. Using a zip iterator 
4. Using [once()][once] with default alternative

# Boolean flag

Using the boolean flag method we'll initialize a boolean flag to one state.
We'll condition on the state of the flag to determine if we need to perform
extra logic and then we'll set the flag to the alternate state.

```rust
pub fn boolean_flag_join(slice: &[&str]) -> String {
    let mut add_separator = false;
    let mut output = String::new();
    for item in slice {
        if add_separator {
            output.push_str(" + ");
        }
        add_separator = true;
        output.push_str(item);
    }
    output
}
```

For the above example I chose a positive variable name, so even though the _odd_
state is for the initial item in the iterator of `str` I named it based on what
is being done in the logic, adding the separator between successive elements.

This is a common approach and is often the way one does this type of thing in
C. 

# Keying off of the index

Keying off the index uses the index in the iterator to determine when to do
the special logic. 

```rust
pub fn enumerator_index_join(slice: &[&str]) -> String {
    let mut output = String::new();
    for (i, item) in slice.iter().enumerate() {
        if i != 0 {
            output.push_str(" + ");
        }
        output.push_str(item);
    }
    output
}
```

While the code example is provided a slice and could actually navigate the slice
by index. It's more idiomatic to treat the slice as an iterator. This then
requires using `enumerate()` to get to the index.

# Zip Iterator

To use a zip iterator to solve this, an iterator representing the separator
strings is zipped up with the slice items, *always* pushing a separator onto
the `String`.

```rust
pub fn zip_join(slice: &[&str]) -> String {
    let separators = core::iter::once("").chain(core::iter::repeat(" + "));
    let mut output = String::new();
    separators.zip(slice).for_each(|(separator, item)| {
        output.push_str(separator);
        output.push_str(item);
    });
    output
}
```

For this problem the zipped iterator starts with a [once()][once] iterator which
will provide the specified item once and then be exhausted. The initial item is
an empty string so that the push for the first element results in no change to
the output. The [once()][once] iterator is chained with a [repeat()][repeat]
iterator of the real separator. Using a [repeat()][repeat] ensures we have a
separator for however many items may be in the slice.

This approach removes the condition in the for loop, but it can take a bit of a
mental shift if one is used to the if conditions that's needed in C for loops.

# `once()` with default alternative

Similar to the zip iterator, an iterator could be created from [once()][once].
However instead of chaining this to a [repeat()][repeat] iterator we exhaust the
iterator and fall back to an alternate value.

```rust
pub fn once_join(slice: &[&str]) -> String {
    let mut separator_iter = core::iter::once("");
    let mut output = String::new();
    for item in slice {
        output.push_str(separator_iter.next().unwrap_or_else(|| " + "));
        output.push_str(item);
    }
    output
}
```

This example creates an iterator of one itme being an empty string. The iterator
will be exhausted after the first time it's called and then the `unwrap_or_else`
will provide the value we'll use in all other instances.

Similar to the zip iterator this may seem a bit foreign to those coming from C
or similar where a condition in a for loop is often used. This can also feel a
bit wasteful as it's creating more or less a throw away iterator just to avoid a
condition in the code.

# Comparison

For this simple example one shouldn't worry too much about performance and
should lean toward readability. At the same time I think it's good to know or
understand how the solutions may differ.

I put all of the approaches in one main file using `opt-level 3` on compiler explorer:

<iframe width="800px" height="500px" src="https://godbolt.org/e#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAMzwBtMA7AQwFtMQByARg9KtQYEAysib0QXACx8BBAKoBnTAAUAHpwAMvAFYTStJg1DEArgoKkl9ZATwDKjdAGFUtEywYgATKUcAZPAZMADl3ACNMYhBJAGZSAAdUBUI7Bhc3Dz1E5NsBAKDQlgiorktMa1yGIQImYgJ0908fK0wbVOragnyQ8MjouPNOhszSwbruwuKJAEpLVBNiZHYOeJMwgGoqBnWBJYB9bVRAiAVaPCWQdYBSLwA2K4BWACEb2/NiR4ARafWAWiuYth1tViIFgNcAOwvDQAQXW8PW9AI6xYJmRSnitSYRGIe0IkWuMU%2B6zQxHYIHxURAu0wEBuXnp0wB0LhCKRKLROzRq2RAOJILBIBAQQA7hAmTEWQjNiR1viWHLtqdzphIVLpQj5gQeQA6VYKBB7d4nTCY4jYkh4giRHVBVQEcU6kwMEXm%2BJ7S3lJR0iFOK6%2B65eLyBp6BrzTCXqjVc7VovVmQ3G%2BWRq6w6X%2Bz6p1nwrU8rMZ/Ow1YbLbrABeeHdh2Oyougfuz1e7y%2BP3%2BgOBBFBRjVWel7IxWJxCkJxNJ5MpQppdKDjJ1yAQTGOY6FE5AZPimGx0%2BDN1DjJTabZmGRqORuc5fI7XdAwswYoP2fWA/NQ51FfiJzOS2mOv4uM384%2Bk4JpmhaZBytaLBMgG/pRhq54EPGBpGp2IGDiQD7Rjm3JxvqiaocmzK9giGaYZqOEEPmEKZrCWbFps2yMO4kRgXiDBYKoBxHAwn4qpcryPC8dzNg83x/ACQICt2sHEfC7KnjGPIjlegq3veRGHvCf7rBAeCkBBmBQYqT5fpgOqUo6TFsC%2BtI/DJmkangVByusYBgJeGg9g5WGKbhCYocQ24hmGZHRgW3nkbGiF4QFumQaFkI0Y%2BCFUUldFrAx6xhKgribgwexUAYwBcTWpn8XcglNp2Lbie2UngvZj7yZyTDoOgRqmuhxDKVQYhKBpTXHhyZ4Ucp9VCqK4oDdK2nysZtaqo1PlOesrXtc%2BYFeY%2BPkIUh%2BGBfSwWMtNWHhdtCJrR1oE4spnYmJgJ3RrtMVJvFj2JbJvmUbR1GFjC9Gliwi48XZUKff2pnKZVQZMPS%2Bn0mEcNhsg9JfO98RdgQtAMG527Zblhg9r9Qb6fj9CGAVRUlTxTamRG6OY9juP0lZLE3TJxM%2BOsrMvpagQcdT05vHTCUY4EWM45A9LvkTmYk%2BWlaC7TKr05Kn1i4ITNS0GNKy0jNJK8JIsDRmHCzLQnAPLwngcFopCoJwABKZjovMiyLV4MQ8KQBCaGbswANYgA8Gj6JwkjW379ucLwCggKHvu22bpBwLAMCICgqAsPEdCROQlBoNnudRMQXAQiHfB0NaxBxxAYRR2EgS1AAnpw3uN8wxDNwA8mE2itIn3uF2wgjdwwtCt0npBYGEJjAE4Yi0HH3C8FgQNGOIU/4GSbQAG6YMvduYKorRossdvi%2BUUdnGE5pdy4WBR52eAsG3yeFUwwAKAAangd7dxuG23t%2BCCBEGIdgUgZCCEUCodQU9dClAMEYNcLt9B4DCHHSAsxUDxEqMvX4TgfI7Vwb8eg%2B9aB8hiLwVA%2B9iCgiwJgqAzA2AgEwPgSopBd5iHupwLwGgvA8AjGUCoqQHDsWGJ4LgPh/CBB6EUPokhbgAE4EhJBSAICREgfDZHUQwCYvQoiKJUS0NoAgOh1E0aMcoA92g1HGLIyYfQYgPAhJYOx9RXCND0GMLoDiDEgGcRCWYCg3YXC4ObS2kcp4Ow4OsUw5hkDrC4DqcuOpPIQFwIQWUNwvbTF4InLQQiECbiwFEcUpAg4VwthwCOpBX4VxtnbGJsd44%2Bz9rMVOGcEL5wgIXHO9BiDBFYMseJBBEnJNuAADjSbwNhWT6F6BAcIUQ4hIFLJgWoKOCDSCuiYPEN%2BESOBW1II06hnBu6jVQM5UZ4yUkPDSTpFwRcBmBlyfk9psximtT6OU6ptT6mh1OdHDgLSE4fIqcHUO1SqEnKjs0tpSchHVK8FEppMcEWFNmLQ5I9hJBAA%3D"></iframe>

Looking at the assembly, the `boolean_flag_join()` and the
`enumerator_index_join()` were compiled into the same function. 
The `zip_join()` and the `once_join()` remain separate functions. The assembly
for `once_join()` and `boolean_flag_join()` are very similar. The `zip_join()`
deviates quite a bit and looks to have more assembly instructions.

I decided to use [criterion][criterion] to see how these compare performance
wise:

```
once_join               time:   [34.016 ns 34.068 ns 34.134 ns]

zip_join                time:   [45.314 ns 45.369 ns 45.442 ns]

enumerator_join         time:   [34.014 ns 34.152 ns 34.309 ns]

boolean_flag_join       time:   [33.965 ns 34.047 ns 34.154 ns]
```

As the extra assembly implied, `zip_join()` is slower. These benchmarks were
using the example slice of `["a", "b", "c"]`. To get a better idea of how much
the `zip_join()` deviates I ran the benches again with 
`["a", "b", "c", "d", "e", "f", "g", "h"]`:

```
once_join               time:   [73.588 ns 73.787 ns 73.992 ns]

zip_join                time:   [102.24 ns 102.55 ns 102.87 ns]

enumerator_join         time:   [74.523 ns 75.011 ns 75.541 ns]

boolean_flag_join       time:   [77.397 ns 77.928 ns 78.417 ns]
```

Since the `zip_join()` delta increased it seems to be a per iteration cost. As
opposed to a one time setup cost.

# Summary

For some reason seeing if statements inside of for loops feels like a code
smell. I understand at times it may be the only way to do things, especially for
more complex cases than the example. It may be that having a condition makes one
pause and think:

> Under what circumstances does this for loop behave differently?

Coming from C I've had a bit harder time becoming fluent in iterators and what
they're doing at times, but I've been trying to lean on them more.

I was a bit surprised and disappointed that the `zip_join()` was ~33% slower in
these simple tests. I wouldn't avoid it as a solution unless there is a
performance concern.

[join]: https://doc.rust-lang.org/std/primitive.slice.html#method.join
[once]: https://doc.rust-lang.org/stable/core/iter/fn.once.html
[repeat]: https://doc.rust-lang.org/stable/core/iter/fn.repeat.html
[criterion]: https://bheisler.github.io/criterion.rs/criterion/index.html