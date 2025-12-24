---
layout: post
title:  "Rust's format_args!() lifetime"
date:   2023-03-11 18:00:03 -0800
categories: rust lifetime
---

I recently had a desire to use the
[`format_args!()`](https://doc.rust-lang.org/std/macro.format_args.html) macro
as an intermediate step to build up a formatted
[`Display`](https://doc.rust-lang.org/std/fmt/trait.Display.html)
implementation.

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=use+std%3A%3Afmt%3B%0A%0A%23%5Bderive%28Default%2C+Debug%29%5D%0Apub+struct+Foo%3B%0A%0Aimpl+fmt%3A%3ADisplay+for+Foo+%7B%0A++++fn+fmt%28%26self%2C+f%3A+%26mut+fmt%3A%3AFormatter%3C%27_%3E%29+-%3E+fmt%3A%3AResult+%7B%0A++++++++let+something+%3D+%22hello%22%3B%0A++++++++let+intermediate+%3D+format_args%21%28%22%7Bsomething%7D+World%21%22%29%3B%0A++++++++write%21%28f%2C+%22%7Bintermediate%7D%22%29%0A++++%7D%0A%7D%0A%0Afn+main%28%29+%7B%0A++++let+foo+%3D+Foo%3A%3Adefault%28%29%3B%0A++++println%21%28%22%7Bfoo%7D%22%29%3B%0A%7D"></iframe>

If you run the above example you will get a failure:

```console
--> src/main.rs:9:28
   |
9  |         let intermediate = format_args!("{something} World!");
   |                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^- temporary value is freed at the end of this statement
   |                            |
   |                            creates a temporary value which is freed while still in use
10 |         write!(f, "{intermediate}")
   |                     ------------ borrow later used here
   |
   = note: this error originates in the macro `format_args` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider using a `let` binding to create a longer lived value
   |
9  ~         let binding = format_args!("{something} World!");
10 ~         let intermediate = binding;
   |
```

Unfortunately this suggestion is more or less what I had written:

```rust
let intermediate = format_args!("{something} World!");
```

Adding an extra intermediate variable will not help.

After banging my head for a while I finally ran across this issue
<https://github.com/rust-lang/rust/issues/92698>. The issue explained that
`format_args!()` is meant to be used right away. It is temporary and is more or
less immediately dropped.

This issue also explained that here are ways to work around this limitation by
using match statements or similar:

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=use+std%3A%3Afmt%3B%0A%0A%23%5Bderive%28Default%2C+Debug%29%5D%0Apub+struct+Foo%3B%0A%0Aimpl+fmt%3A%3ADisplay+for+Foo+%7B%0A++++fn+fmt%28%26self%2C+f%3A+%26mut+fmt%3A%3AFormatter%3C%27_%3E%29+-%3E+fmt%3A%3AResult+%7B%0A++++++++let+something+%3D+%22hello%22%3B%0A++++++++match+format_args%21%28%22%7Bsomething%7D+World%21%22%29+%7B%0A++++++++++++intermediate+%3D%3E+write%21%28f%2C+%22%7Bintermediate%7D%22%29%3F%2C%0A++++++++%7D%0A++++++++Ok%28%28%29%29%0A++++%7D%0A%7D%0A%0Afn+main%28%29+%7B%0A++++let+foo+%3D+Foo%3A%3Adefault%28%29%3B%0A++++println%21%28%22%7Bfoo%7D%22%29%3B%0A%7D"></iframe>
