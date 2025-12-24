---
layout: post
title:  "Custom Test Framework in Rust"
date:   2022-05-24 19:10:03 -0700
categories: rust test
---

Rust and Cargo come out of the box with [unit test][unit_tests] support.  This
is a nice feature for one to get started quickly with testing in Rust.  The
skeleton project created by `cargo init` even provides an example test for one
to use.

```rust
#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        let result = 2 + 2;
        assert_eq!(result, 4);
    }
}
```

# Limitations

Unfortunately the default test framework is lacking features that are available
in other languages:

* It doesn't support test fixtures, setup and teardown operations
* It's not available with `no_std`
* It doesn't support custom reporters or listeners.  

At times these limitation can be worked around, but they can be clunky.  There
are also times where it just isn't practical to work around the issues.  For
example not supporting tests in `no_std` quickly limits non host test runs.

# Custom Frameworks

There is an unstable feature which supports 
[custom test frameworks][custom_test_frameworks].  Copying from the provided
example.

```rust
#![feature(custom_test_frameworks)]
#![test_runner(my_runner)]

fn my_runner(tests: &[&i32]) {
    for t in tests {
        if **t == 0 {
            println!("PASSED");
        } else {
            println!("FAILED");
        }
    }
}

#[test_case]
const WILL_PASS: i32 = 0;

#[test_case]
const WILL_FAIL: i32 = 4;
```

Being new to rust this example left me wondering how this helps.  My initial
thought was when would I want to test a constant.

> To get this to run one will need to use the nightly channel.  This can be done
by running `rustup override set nightly` in the workspace directory.

Running this example with `cargo test`, results in:
```
➜  custom_test_framework git:(master) ✗ cargo test
warning: function is never used: `my_runner`
 --> src/lib.rs:4:4
  |
4 | fn my_runner(tests: &[&i32]) {
  |    ^^^^^^^^^
  |
  = note: `#[warn(dead_code)]` on by default

warning: `custom_test_framework` (lib) generated 1 warning
    Finished test [unoptimized + debuginfo] target(s) in 1.04s
     Running unittests src/lib.rs (target/debug/deps/custom_test_framework-dbf8bd94e11d2c90)
PASSED
FAILED
   Doc-tests custom_test_framework

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

There are a some things to notice with this output:
* The summary result lists `0 passed` and `0 failed`
* There is no listing of each test by name like standard rust tests
* There is a warning to the user for an unused function.  I'll admit this one
  seems petty, but having a warning from the only example in the _official_
  docs, even if it's an unstable feature, is not welcoming.

## Converting to Functions

As mentioned above the example was not using functions. I'm new to rust so
it took me a little bit to figure out how to update the example to work with
functions.  Eventually I was able to re-write as:

```rust
#![feature(custom_test_frameworks)]
#![test_runner(my_runner)]

fn my_runner(tests: &[&dyn Fn()]) {
    for t in tests {
        t();
    }
}

#[test_case]
fn test_1() {
    assert_eq!(1, 1);
}

#[test_case]
fn test_2() {
    assert_eq!(3, 1);
}
```

Notice that `test_2()` will fail.  Running this with `cargo test` will result in:

```
➜  custom_test_framework git:(master) ✗ cargo test
warning: function is never used: `my_runner`
 --> src/lib.rs:4:4
  |
4 | fn my_runner(tests: &[&dyn Fn()]) {
  |    ^^^^^^^^^
  |
  = note: `#[warn(dead_code)]` on by default

warning: `custom_test_framework` (lib) generated 1 warning
    Finished test [unoptimized + debuginfo] target(s) in 0.00s
     Running unittests src/lib.rs (target/debug/deps/custom_test_framework-dbf8bd94e11d2c90)
thread 'main' panicked at 'assertion failed: `(left == right)`
  left: `3`,
 right: `1`', src/lib.rs:17:5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
error: test failed, to rerun pass '--lib'
```

This suffers from the same output problems as the initial run.  One may notice
the summary is missing that's because the `assert_eq!()` caused a panic and
nothing prevented it from stopping the entire application.

## Test Names

One thing any good test framework should have is the ability to run a subset of
tests.  Debugging `my_runner()` I noticed that `tests` is a slice containing all
the `test_case` functions.  Trying to run one test with cargo, 
`cargo test test_1`, all of the tests are still provided to `my_runner()`.
Since rust doesn't provide reflection there isn't an easy way to filter these
functions based on their name.

Doing some investigation I eventually came across
[`test_main_static()`][test_main_static] in the rust source. It gets a slice
of some kind and it grabs the program arguments *after* the slice of tests.

```rust
pub fn test_main_static(tests: &[&TestDescAndFn]) {
    let args = env::args().collect::<Vec<_>>();
    let owned_tests: Vec<_> = tests.iter().map(make_owned_test).collect();
    test_main(&args, owned_tests, None)
}
```

Looking up the `TestDescAndFn` gets one to:
```rust
pub struct TestDescAndFn {
    pub desc: TestDesc,
    pub testfn: TestFn,
}
```

While I dug down further into what these sub structs were, there is no need for
the rest of this post.  This gave me an idea that maybe I could also pass in a
slice of something other than a function.  

After much pondering, it finally donned on me what the benefit of `#[test_case]`
is for non functions:

```rust
#![feature(custom_test_frameworks)]
#![test_runner(my_runner)]

pub struct TestCase <'a> {
    name: &'a str,
    function: &'a dyn Fn(),
}
unsafe impl Sync for TestCase <'_>{}

fn my_runner(tests: &[&TestCase]) {
    for t in tests {
        (t.function)();
    }
}

#[test_case]
static _test_1: TestCase = TestCase{name:"test_1", function:&test_1};
fn test_1() {
    assert_eq!(1, 1);
}

#[test_case]
static _test_2: TestCase = TestCase{name:"test_2", function:&test_2};
fn test_2() {
    assert_eq!(3, 1);
}
```

This creates a new struct that holds the name of the test, as well as the actual
function of the test itself.  We decorate static instances of these structs with
`#[test_case]` in order build up a list of those to be passed into
`my_runner()`.

### Macro Magic

Manually creating a static `TestCase` for each test function is not ideal.  So I
decided to dig into macro magic.  This post is already getting a bit long so
I'll just drop the macro code here, to show that it can be done.  Due to macros
needing to be in a `proc-macro` crate this requires a separate crate to be its
home.

```rust
extern crate proc_macro;

use syn::{ItemFn, parse};
use proc_macro2::{TokenStream, Span};
use quote::{quote, format_ident};

#[proc_macro_attribute]
pub fn mytest(attr: proc_macro::TokenStream, input: proc_macro::TokenStream) -> proc_macro::TokenStream {
    let attr = proc_macro2::TokenStream::from(attr);
    let input = proc_macro2::TokenStream::from(input);
    let output =
        match mytest_impl(attr, input) {
            Ok(ts) => ts,
            Err(e) => e.to_compile_error().into(),
        };

    proc_macro::TokenStream::from(output)
}

/// Generate the necessary wrapper for a test function
fn mytest_impl(attr: TokenStream, input: TokenStream) -> parse::Result<TokenStream> {
    if !attr.is_empty() {
        return Err(parse::Error::new(
            Span::call_site(),
            "`#[mytest]` attribute takes no arguments",
        ));
    }
    let function: ItemFn = syn::parse2(input)?;
    let function_name = function.sig.ident.clone();
    let function_string = format!("{}", function_name);
    let test_case_name = format_ident!("_{}", function_name);

    Ok(quote!(
    #[test_case]
    static #test_case_name: TestCase = TestCase{name: #function_string, function: &#function_name};
    #function
    ))
}
```

This creates a new macro `#[mytest]` which one can decorate test functions with
to get them to be seen by the test runner function.

```rust
fn my_runner(tests: &[&TestCase]) {
    for t in tests {
        (t.function)();
    }
}

#[mytest]
fn test_1() {
    assert_eq!(1, 1);
}
```

# Summary

Unstable rust does support custom test frameworks, however it only provides the
test discovery. One is left building up the rest of the framework:
* Output format
* Proper summary
* Capturing panics
* CLI parsing and logic
* Test filtering

The custom test framework attributes also have to be in the root `lib.rs` or
`main.rs` of the crate.  These can't be hidden down in a test framework crate.
It does seem that one can add a test framework as a dev dependency and the crate
will only be looked up when running tests. So one can reference the test runner
function from a framework crate without polluting the non test builds.

For example the below could be placed at the top of a crate's `lib.rs`, where
`my_test_framework` is a crate that has `my_runner` in it.  `my_test_framework`
would only need to be a dev dependency in the crates toml file.

```rust
#![feature(custom_test_frameworks)]
#![test_runner(my_test_framework::my_runner)]
```

[unit_tests]: https://doc.rust-lang.org/rust-by-example/testing/unit_testing.html
[custom_test_framework]: https://doc.rust-lang.org/beta/unstable-book/language-features/custom-test-frameworks.html
[test_main_static]: https://github.com/rust-lang/rust/blob/master/library/test/src/lib.rs#L125