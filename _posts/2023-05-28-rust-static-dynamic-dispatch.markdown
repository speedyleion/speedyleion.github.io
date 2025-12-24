---
layout: post
title:  "Rust's Static and Dynamic Dispatch"
date:   2023-05-28 19:30:03 -0700
categories: rust traits
---

When invoking an object's method in rust there are two dispatch mechanisms,
static and dynamic.

```rust
pub trait Trait {
    fn do_something(&self);
}

fn static_dispatch<T: Trait>(foo: &T) {
    foo.do_something();
}

fn dynamic_dispatch(foo: &dyn Trait) {
    foo.do_something();
}
```

Here we have a trait named `Trait`. It expects implementations to provide a
`do_something()` method. The `do_something()` method takes `&self`, a reference
to the concrete type which is implementing the `Trait`. This means that
implementations of `do_something()` will have full access to whatever type
implements the trait.

The `static_dispatch()` function is a generic function that takes a reference to
a type that implements `Trait`. This is resolved at compilation time, meaning
that wherever `static_dispatch()` is called the compiler has to know what the
underlying type of `foo` is.

The `dynamic_dispatch()` function is *not* generic. It is a function that takes
a reference to an object that implements `Trait`, a trait object. At run time
this will do a lookup on `foo` to find the address of the `do_something()`
method and then call it.

## Passing Trait Objects to Functions

We'll define a simple type that implements `Trait` and then try to use it with
the `static_dispatch()` and the `dynamic_dispatch()` functions:

```rust
pub struct Stuff {
    pub value: u64,
}

impl Trait for Stuff {
    fn do_something(&self) {
        println!("Stuff: {}", self.value);
    }
}
```

If we create a concrete instance of `Stuff` we can pass it to either function
and it will compile and run fine:
```rust
fn main() {
    let stuff = Stuff { value: 1 };
    static_dispatch(&stuff);
    dynamic_dispatch(&stuff);
}
```

We can create a `Box` containing a `Stuff` instance and pass it to either
function:
```rust
fn main() {
    let stuff = Box::new(Stuff { value: 1 });
    static_dispatch(&*stuff);
    dynamic_dispatch(&*stuff);
}
```

We had to first dereference the contents of the `Box` with the
[dereference][dereference operator] operator, `*`, to get access to the
contained item, before we passed the reference.

It's important to note that this a `Box<Stuff>`. If we instead create a `Box` of
the trait it will fail to compile.
```rust
fn main() {
    let stuff: Box<dyn Trait> = Box::new(Stuff { value: 1 });
    static_dispatch(&*stuff);
    dynamic_dispatch(&*stuff);
}
```

We will be provided with an error similar to:

```
error[E0277]: the size for values of type `dyn Trait` cannot be known at compilation time
  --> src/main.rs:25:21
   |
25 |     static_dispatch(&*stuff);
   |     --------------- ^^^^^^^ doesn't have a size known at compile-time
   |     |
   |     required by a bound introduced by this call
   |
   = help: the trait `Sized` is not implemented for `dyn Trait`
note: required by a bound in `static_dispatch`
  --> src/main.rs:5:20
   |
5  | fn static_dispatch<T: Trait>(foo: &T) {
   |                    ^ required by this bound in `static_dispatch`
help: consider relaxing the implicit `Sized` restriction
   |
5  | fn static_dispatch<T: Trait + ?Sized>(foo: &T) {
   |                             ++++++++

For more information about this error, try `rustc --explain E0277`.
```

Like many rust error messages, this one provides you with a potential fix,
adding `+ ?Sized` to the trait bounds.

## Implicitly Sized

Per the [`Sized`][Sized] documentation. `Sized` is an implicit trait on all type
parameters. It means that the size of the type is known at compile time. In
order to _relax_ this bound one uses the `?Sized` syntax.

If we follow the error suggestion and modify `static_dispatch()` to relax this
bounds, then the example will again compile and run.

```rust
fn static_dispatch<T: Trait + ?Sized>(foo: &T) {
    foo.do_something();
}
```

I've got a feeling that `+ ?Sized` turns the `static_dispatch()` function into a
dynamic dispatch implementation. I did some quick searching online and came up
empty 

## Resources

- [Rust Playground for code examples](https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&gist=633d37bcc6348b499d5e940aa89cfec2)
- [The rust book trait objects chapter](https://doc.rust-lang.org/book/ch17-02-trait-objects.html)
- [Crust of Rust: Dispatch and Fat Pointers](https://www.youtube.com/watch?v=xcygqF5LVmM&list=PLqbS7AVVErFiWDOAVrPt7aYmnuuOLYvOa&index=10&pp=iAQB)

[Sized]: https://doc.rust-lang.org/std/marker/trait.Sized.html
[dereference operator]: https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-dereference-operator