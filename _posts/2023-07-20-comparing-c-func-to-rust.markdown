---
layout: post
title:  "Comparing a Simple C Function to Rust"
date:   2023-07-20 16:20:03 -0700
categories: rust c
---

Coming from an embedded C background, I started to notice when reviewing rust
code that I didn't need to focus as much on function input validation. I wanted to
capture my current understanding here.

One often hears the following saying for functional programs, and at times rust:

> It compiles and just works

I think this is an oversimplification, but hopefully the rest of this post
better communicates why some of that feeling may occur.

This isn't meant to be a rust is better than C post, just trying to explain
where one area of rust reduces cognitive load, allowing more mental capacity to
focus on other areas of development.

## C Implementation

Let's jump right into a simple `C` function that one might encounter:

```c
int get_thing(const char * name, thing_type * thing) {
    ...
}
```

This function will use `name` to find and fill out the passed in `thing`. It
returns an `int` to communicate if the function failed or not.

Ignoring _how_ we use `name` to find `thing`, we can dig into some of what this
implementation may need:

1. The function should probably check for a null pointer to `name`
2. Not often practical to check, but `name` should be null terminated.
3. The function should probably check for a null pointer to `thing`
4. We may want to `memset` or have a default for `thing` even if the function
   errors out.

These items are some sharp edges of C, for good and bad.

One could argue against `name` as a `const char *` and that this should use an
enumeration. The example is meant to capture common inputs. Strings are seen in
many C APIs.

## Rust Implementation

Translating more or less one for one into rust we get.

```rust
fn get_thing(name: &str, thing: &mut ThingType) -> u32 {
    ...
}
```

We'll break down some of this signature for those unfamiliar with rust.

`name: &str` is an argument named `name` with a type of `&str`. `&str` is the
common rust type for string references. The compiler will ensure that the `&str`
points to valid memory and has a valid size.

`thing: &mut ThingType` is an argument named `thing`. It is a _mutable_
reference of `ThingType`. By default in rust, all variables and arguments are
immutable, meaning they cannot be modified. When one wants to modify a variable
or argument they must use the `mut` keyword. One can think of it as the opposite
as `const` in C. The compiler will ensure that `thing` is not a null pointer.

`-> u32` is the return type of the function. It is an unsigned 32 bit integer.

Comparing to the C function we can see there are a few less gotchas.

1. `name` can not be a null pointer. The compiler will ensure this. 
2. The compiler will ensure that `name` has a valid length.
3. `thing` can not be a null pointer. The compiler will ensure this.
4. `thing` will have to be initialized prior to the function call. The compiler
   will ensure this. Initializing by the caller could be a bad thing as it puts
   more burden on the caller and it could hurt performance by setting values
   that will be overwritten in the `get_thing` call.

### Using the Result Type

The function could be further updated to follow common rust idioms.

Rust code often uses the [Result<T, E>][Result] type for error handling. This
type is ingrained in the language such that there is a [question mark `?`][question mark] operator
which makes working with `Result`s ergonomic to use.

Coming from C the `Result` type took me a bit to fully appreciate. I'll attempt
to communicate its usage. If we update the rust function to use the `Result`
type we get:

```rust
fn get_thing(name: &str) -> Result<ThingType, u32> {
    ...
}
```

This function will return either a `ThingType` or a `u32`. This means when one
has an error they will only be able to see a `u32` value, the compiler will
enforce this. If the function succeeds it will only return a `ThingType`. The
caller no longer needs to look at the `u32` the presence of the `ThingType`
tells them it succeeded.

An example usage is:

```rust
match get_thing("fish") {
   Ok(thing) => println!("The thing is {thing}"),
   Err(value) => println!("The error code was {value}"),
}
```

The `match` statement is similar to a C `switch` statement, however the compiler
will ensure that you have logic for both the `Ok` and the `Err` branches. 

The `Result` type has two states `Ok()` and `Err()`. In this case the `Ok()`
state contains a `ThingType` and the match statement allows us to get access to
it via the variable that we named `thing`. We could have written 
`Ok(foo) => ...` and referenced it as `foo`. The `Err()` state contains the
`u32` error code, which we reference as `value`.

There are a few other ways to use the `Result` type, but with any of them the
compiler will force you to acknowledge that the two different states.

The returning of the `ThingType` assumes that it's not too large. One could
return the result code and item in C by wrapping them in a struct, but this
isn't often done.

## Summary

While this example function was simple, I think it is a common C API idiom, and
hopefully it communicates how there are a few less concerns to look for when
writing and reviewing the rust version.

I intentionally left out discussion of ownership, borrowing, and the ability to
use `unsafe` in rust. While one can introduce similar gotchas in rust using
`unsafe` code, it isn't the norm.

There are some software practices that can reduce the C gotchas. For example
using static analyzers or organizational coding policies of when and where null
pointers are checked. These require extra work and diligence on top of the
language usage. Often static checkers can be difficult to get working at the
right level of signal to noise.

[question mark]: https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-question-mark-operator
[Result]: https://doc.rust-lang.org/std/result/enum.Result.html
