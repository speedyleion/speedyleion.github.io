---
layout: post
title:  "Comparing rust's Option to C's null pointer"
date:   2023-07-27 20:05:03 -0700
categories: rust c
---

Coming from C development, I heard people say there are no null pointers in
rust, and I thought that sounds good, but I wonder how they could get by with
always passing a valid value. Then I would hear people say there's `Option<T>`
which can have `None` to indicate no value. This made me think:

"what advantage does this have over a null pointer?"

# Null Pointer

Let's dig into C and it's use of null pointers. Here we have a function that
returns a pointer to a `cool_thing`. 

```c
int * foo();
```

Often in C API's, one will return a null pointer when `foo()` failed to derive
the `int *`.  This means a user of this API will generally need to have a
guard clause similar to:

```c
int * my_value = foo();
if(my_value == 0) {
    return SOME_ERROR;
}

return do_stuff(my_value);
```

A problem that crops up is in the implementation of `do_stuff()`. It is most
likely getting a pointer to an `int`. Should it have a guard clause as
well? We could document that `do_stuff()` assumes it's `int *` is not null,
but that requires diligence from all the users. There may also be cases where we
want to pass a null pointer to `do_stuff()` or an equivalent function.

```c
error_type do_stuff(int * value) {
    if(value == 0) {
        return SOME_ERROR;
    }

    // actual logic
}
```

# Rust's `Option<T>`

The `Option<T>` type can be thought of as a wrapper around the desired type.
This wrapper contains either `Some(T)` or `None`. Coming from C it's use seems
similar handling to a null pointer, in that one often checks for `None`. 

There are some differences that we'll get into with code examples.
In the following snippet we have a function `foo()` that returns an
`Option<&u32>`. This means it returns either `None` or `Some(&u32)`. The `&u32`
is a reference to a 32 bit unsigned integer. 

```rust
fn foo() -> Option<&u32>;
```

The caller of `foo()` needs to have logic to handle the two cases of `None` or
`Some(&u32)`.

```rust
let thing = foo();
let result = match thing {
    None => FAIL,
    Some(item) => do_stuff(item),
};
result
```

In this instance the caller `match`es on the value returned from `foo()`. If
`thing` happens to be `None` then it sets `result` to the `FAIL` error code. The
other match statement of `Some(item)` may be foreign to those coming from C.
This matches the pattern `Some(item)` where `item` is the value inside of
`Some`. The `item` can be thought of as a local variable. One could have
`Some(my_name)` and then the other side of the `=>` would be `do_stuff(my_name)`.

There are 2 important things to note over a null pointer in C:
1. The compiler will require both of these branches to be handled, or at least
   acknowledged.
2. `do_stuff()` takes a `&u32`. It does not need to worry about unwrapping the
   `Option<>`. Rust will *not* allow a null pointer to be present in a `&u32`.

# Summary

Coming from a C background it's easy to conflate rust's `Option<>` type and the
common use of C's null pointers to indicate the presence of a value. It helps to
understand that the rust compiler will require code to handle the `None` version
of an `Option<>` and that once the value is unwrapped from an option the need to
check for `None` does not continue to propagate down through the API.