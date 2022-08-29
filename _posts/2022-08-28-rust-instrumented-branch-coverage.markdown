---
layout: post
title:  "Instrumented branch coverage in rust"
date:   2022-08-28 16:11:03 -0700
categories: rust coverage testing
---

Rust has [instrumented coverage][instrument coverage] available.  This form of
coverage uses LLVM's built in coverage instrumentation.  It is intended to be
performant and accurate.

I was interested to see how coverage for the `?` operator was handled.

> This is available in `one.rs` at, https://github.com/speedyleion/rust-coverage

```rust
#[derive(Debug, PartialEq)]
pub enum Error {
    Bar,
    Baz
}

fn bar(flag: bool) -> Result<(), Error> {
    if flag {
        Err(Error::Bar)
    } else {
        Ok(())
    }
}

fn baz(flag: bool) -> Result<(), Error> {
    if flag {
        Err(Error::Bar)
    } else {
        Ok(())
    }
}

pub fn foo(flag: bool) -> Result<(), Error> {
    bar(flag)?;
    baz(flag)?;
    baz(flag)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn no_flag_is_ok() {
        assert_eq!(foo(false), Ok(()));
    }
    #[test]
    fn flag_is_error() {
        assert_eq!(foo(true), Err(Error::Bar));
    }
}
```

I used a modified version of the instructions available at
<https://doc.rust-lang.org/rustc/instrument-coverage.html> to test out.

```
RUSTFLAGS="-C instrument-coverage" cargo test
llvm-profdata.exe merge -sparse default.profraw -o default.profdata
llvm-cov show -Xdemangler=rustfilt target/debug/deps/coverage-e9b7e916b6f3c18b -instr-profile=default.profdata -show-line-counts-or-regions
```

> Note the name of your executable may differ

This resulted in a nice console output:
```
   28|       |pub fn foo(flag: bool) -> Result<(), Error> {
   29|      2|    bar(flag)?;
                           ^1
   30|      1|    baz(flag)?;
                           ^0
   31|      1|    baz(flag)
```
Importantly the `?` operator after the first `baz()` call showed that it was hit
0 times (it was also highlighted red in the terminal).  This seems to indicate
that the coverage information knows about branches with respect to the `?`
operator.

Coverage Viewing
----------------

Using `llvm-cov show` is nice for the local command line.  Once a project has
more than one file having a navigable coverage report is more or less required.

There are:

- [codecov][codecov]: provides free hosting for opensource github repos
  With supported formats listed at <https://docs.codecov.com/docs/supported-report-formats>
- [coveralls][coveralls]: provides free hosting for opensource github repos. (Doesn't natively support rust)
  Proprietary format specified under "Source File" at <https://docs.coveralls.io/api-reference>
- [grcov][grcov]: Generates an html coverage report


### grcov

Both [codecov][codecov] and [coveralls][coveralls] require hosting, so I first
looked at [grcov][grcov] to see what it looked like.

Generating the html files can be done with the following command.  Notice the
`--branch` argument.
```
grcov . --binary-path ./target/debug/ -s . -t html --branch --ignore-not-existing -o ./coverage/
```

The generated coverage report is available at `./coverage/index.html`.
Navigating to `one.rs` I saw that it reported 100% branch coverage and that the
`baz(flag)?;` was green..  This seemed to contradict the CLI output of `llvm-cov
show` command.  Also the `if/else` condition in `baz()` was not marked, the
statement was.

grcov seemed like a non starter for showing branch coverage.

### codecov

[codecov][codecov] was the next tool to try out for branch coverage.  

I located [cargo-llvm-cov][cargo-llvm-cov] published by
[taiki-e][https://github.com/taiki-e].  Using the action settings provided in
the repo's `README.md`.

```yaml
name: Coverage

on: [pull_request, push]

jobs:
  coverage:
    runs-on: ubuntu-latest
    env:
      CARGO_TERM_COLOR: always
    steps:
      - uses: actions/checkout@v3
      - name: Install Rust
        run: rustup toolchain install stable --component llvm-tools-preview
      - name: Install cargo-llvm-cov
        uses: taiki-e/install-action@cargo-llvm-cov
      - name: Generate code coverage
        run: cargo llvm-cov --all-features --workspace --lcov --output-path lcov.info
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }} # not required for public repos
          files: lcov.info
          fail_ci_if_error: true
```

Similar to [grcov][grcov], the resultant coverage run didn't show the missing
branch at `?`.  It did show the missing line for the `if` in `baz()`, but it did
not show the partial for only hitting the `if` condition false.


Regions
-------

At this point I decided to do some googling.  I ran across
<https://github.com/rust-lang/rust/issues/79649>.  In particular this comment,
<https://github.com/rust-lang/rust/issues/79649#issuecomment-1120040546>.

It seems that branch coverage is not currently supported for rust's source based
code coverage.  Region based coverage *is* available and that's what was
actually being seen by `llvm-cov show`.

Summary
=======

It seems that branch based source code coverage is not currently supported by
rust's [instrumentation coverage][instrument coverage].  

Per the comment <https://github.com/rust-lang/rust/issues/79649#issuecomment-1121561058> 
> Implementation (MIR) wise, all the counters are there.
https://rustc-dev-guide.rust-lang.org/llvm-coverage-instrumentation.html is very
detailed about how this all works. And in theory, implementing branch coverage
would consist of introducing new counters that just "reference" existing
counters for the true/false branch.

I want to look through
<https://www.llvm.org/docs/CoverageMappingFormat.html> and see if there is a way
to derive or convert the region information into `lcov`s branch format. It may
be that the information is lost by the time we get to the llvm output format.

[instrument coverage]: https://doc.rust-lang.org/rustc/instrument-coverage.html 
[codecov]: https://codecove.io
[coveralls]: https://coveralls.io
[grcov]: https://github.com/mozilla/grcov
[cargo-llvm-cov]: https://github.com/taiki-e/cargo-llvm-cov