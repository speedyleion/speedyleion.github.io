---
layout: post
title:  "Borrowing in Async Rust"
date:   2022-12-17 10:31:03 -0700
categories: rust async borrow
---

While learning to use async in rust I tripped up a little bit on the behavior of
borrowing and lifetimes. This is meant to summarize how borrows behave when used
in async functions and methods.

This is written with some assumption that the reader is familiar with borrows
and has some cursory knowledge of async/await.

Normal Borrowing
================

Normally a borrow persists until the completion of a function. This can often be
read fairly linearly through the code.

The comments in `main()` specify when the borrows start and stop.

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=fn%20main()%20%7B%0A%20%20%20%20let%20mut%20foo%20%3D%20Foo%3A%3Anew(3)%3B%0A%20%20%20%20%0A%20%20%20%20%2F%2F%20Start%20of%20immutable%20borrow%0A%20%20%20%20foo.a_borrow_of_self()%3B%0A%20%20%20%20%2F%2F%20End%20of%20immutable%20borrow%0A%20%20%20%20%0A%20%20%20%20%2F%2F%20Start%20of%20mutable%20borrow%0A%20%20%20%20foo.a_mutable_borrow_of_self()%3B%0A%20%20%20%20%2F%2F%20End%20of%20mutable%20borrow%0A%20%20%20%20%0A%20%20%20%20foo.a_borrow_of_self()%3B%0A%7D%0A%0A%23%5Bderive(Default%2C%20Debug)%5D%0Apub%20struct%20Foo%20%7B%0A%20%20%20%20value%3A%20usize%2C%0A%7D%0A%0Aimpl%20Foo%20%7B%0A%20%20%20%20pub%20fn%20new(value%3A%20usize)%20-%3E%20Self%20%7B%0A%20%20%20%20%20%20%20%20Foo%7B%20value%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_borrow_of_self(%26self)%20%7B%0A%20%20%20%20%20%20%20%20println!(%22%7Bself%3A%3F%7D%22)%3B%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_mutable_borrow_of_self(%26mut%20self)%20%7B%0A%20%20%20%20%20%20%20%20self.value%20%2B%3D%201%3B%0A%20%20%20%20%20%20%20%20println!(%22Incremented%20self%20by%20one%3A%20%7Bself%3A%3F%7D%22)%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%7D%0A%20%20%20%20%0A%7D"></iframe>

Since no new structs or similar are being derived from the borrow of `Foo` the
borrows end after each method. This means that the mutable borrow can start
after the immutable borrow because the immutable borrow has ended.

Async Borrowing
================

In async code a function or method returns a future. This future encapsulates
everything that is part of the function.

Compiling the following code will fail.

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=%23%5Btokio%3A%3Amain%5D%0Aasync%20fn%20main()%20%7B%0A%20%20%20%20let%20mut%20foo%20%3D%20Foo%3A%3Anew(3)%3B%0A%20%20%20%20%0A%20%20%20%20println!(%22Calling%20an%20async%20immutable%20borrow%22)%3B%0A%20%20%20%20let%20future%20%3D%20foo.an_async_borrow_of_self()%3B%0A%20%20%20%20println!(%22After%20calling%20an%20async%20immutable%20borrow%22)%3B%0A%0A%20%20%20%20%2F%2F%20Start%20of%20mutable%20borrow%0A%20%20%20%20foo.a_mutable_borrow_of_self()%3B%0A%20%20%20%20%2F%2F%20End%20of%20mutable%20borrow%0A%20%20%20%20%0A%20%20%20%20println!(%22awaiting%20on%20the%20future%22)%3B%0A%20%20%20%20future.await%3B%0A%20%20%20%20println!(%22done%20with%20the%20future%22)%3B%0A%7D%0A%0A%23%5Bderive(Default%2C%20Debug)%5D%0Apub%20struct%20Foo%20%7B%0A%20%20%20%20value%3A%20usize%2C%0A%7D%0A%0Aimpl%20Foo%20%7B%0A%20%20%20%20pub%20fn%20new(value%3A%20usize)%20-%3E%20Self%20%7B%0A%20%20%20%20%20%20%20%20Foo%7B%20value%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_borrow_of_self(%26self)%20%7B%0A%20%20%20%20%20%20%20%20println!(%22%7Bself%3A%3F%7D%22)%3B%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_mutable_borrow_of_self(%26mut%20self)%20%7B%0A%20%20%20%20%20%20%20%20self.value%20%2B%3D%201%3B%0A%20%20%20%20%20%20%20%20println!(%22Incremented%20self%20by%20one%3A%20%7Bself%3A%3F%7D%22)%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%7D%0A%20%20%20%20pub%20async%20fn%20an_async_borrow_of_self(%26self)%20%7B%0A%20%20%20%20%20%20%20%20println!(%22%7Bself%3A%3F%7D%22)%3B%0A%20%20%20%20%7D%0A%20%20%20%20pub%20async%20fn%20an_async_mutable_borrow_of_self(%26mut%20self)%20%7B%0A%20%20%20%20%20%20%20%20self.value%20%2B%3D%201%3B%0A%20%20%20%20%20%20%20%20println!(%22Incremented%20self%20by%20one%3A%20%7Bself%3A%3F%7D%22)%0A%20%20%20%20%7D%0A%7D"></iframe>

The compilation error should look like:

```shell
error[E0502]: cannot borrow `foo` as mutable because it is also borrowed as immutable
  --> src/main.rs:10:5
   |
6  |     let future = foo.an_async_borrow_of_self();
   |                  ----------------------------- immutable borrow occurs here
...
10 |     foo.a_mutable_borrow_of_self();
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ mutable borrow occurs here
...
14 |     future.await;
   |     ------ immutable borrow later used here

For more information about this error, try `rustc --explain E0502`.
```

The compiler is saying that the `&self` parameter of `Foo::an_async_borrow_of_self()`
is still being borrowed. This is because it's borrowed as part of `future_1`.

If we `await` the future prior to the mutable borrow the program will compile
and run. This is because the borrow propagates to the future. Once we `await` on
the future we fully consume it and are done. This means the compiler is free to
drop it there, ending the borrow of `foo`.

<iframe width="800px" height="500px" src="https://play.rust-lang.org/?version=stable&mode=debug&edition=2021&code=%23%5Btokio%3A%3Amain%5D%0Aasync%20fn%20main()%20%7B%0A%20%20%20%20let%20mut%20foo%20%3D%20Foo%3A%3Anew(3)%3B%0A%20%20%20%20%0A%20%20%20%20println!(%22Calling%20an%20async%20immutable%20borrow%22)%3B%0A%20%20%20%20let%20future%20%3D%20foo.an_async_borrow_of_self()%3B%0A%20%20%20%20println!(%22After%20calling%20an%20async%20immutable%20borrow%22)%3B%0A%20%20%20%20%0A%20%20%20%20println!(%22awaiting%20on%20the%20future%22)%3B%0A%20%20%20%20future.await%3B%0A%20%20%20%20println!(%22done%20with%20the%20future%22)%3B%0A%0A%20%20%20%20%2F%2F%20Start%20of%20mutable%20borrow%0A%20%20%20%20foo.a_mutable_borrow_of_self()%3B%0A%20%20%20%20%2F%2F%20End%20of%20mutable%20borrow%0A%20%20%20%20%0A%7D%0A%0A%23%5Bderive(Default%2C%20Debug)%5D%0Apub%20struct%20Foo%20%7B%0A%20%20%20%20value%3A%20usize%2C%0A%7D%0A%0Aimpl%20Foo%20%7B%0A%20%20%20%20pub%20fn%20new(value%3A%20usize)%20-%3E%20Self%20%7B%0A%20%20%20%20%20%20%20%20Foo%7B%20value%20%7D%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_borrow_of_self(%26self)%20%7B%0A%20%20%20%20%20%20%20%20println!(%22%7Bself%3A%3F%7D%22)%3B%0A%20%20%20%20%7D%0A%20%20%20%20pub%20fn%20a_mutable_borrow_of_self(%26mut%20self)%20%7B%0A%20%20%20%20%20%20%20%20self.value%20%2B%3D%201%3B%0A%20%20%20%20%20%20%20%20println!(%22Incremented%20self%20by%20one%3A%20%7Bself%3A%3F%7D%22)%0A%20%20%20%20%20%20%20%20%0A%20%20%20%20%7D%0A%20%20%20%20pub%20async%20fn%20an_async_borrow_of_self(%26self)%20%7B%0A%20%20%20%20%20%20%20%20println!(%22%7Bself%3A%3F%7D%22)%3B%0A%20%20%20%20%7D%0A%20%20%20%20pub%20async%20fn%20an_async_mutable_borrow_of_self(%26mut%20self)%20%7B%0A%20%20%20%20%20%20%20%20self.value%20%2B%3D%201%3B%0A%20%20%20%20%20%20%20%20println!(%22Incremented%20self%20by%20one%3A%20%7Bself%3A%3F%7D%22)%0A%20%20%20%20%7D%0A%7D%0A"></iframe>

> The code snippets provide print statements around the method invocation and
> the awaiting of the future. This is done to emphasize that async functions do
> *nothing* until they are awaited on. 
> 
> When learning async I kept having to reaffirm this to myself.

Summary
========

The function signatures don't show it, but the future that is returned has the
same borrow usage as the function arguments. A function that mutably borrows an
argument will return a future that mutably borrows that argument. The mutable
borrow will last until the future is fully consumed.
