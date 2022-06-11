---
layout: post
title:  "Rust's Move by Default"
date:   2022-06-11 12:29:03 -0700
categories: rust c
---

As a C developer coming to rust, one thing that has taken a while for me to get
used to is rust's move behavior.

Often C developers learn to avoid passing large structures around because
these incur a copy cost.  This practice can often times lead into a general
avoidance of pass by value except when using primitive types (int, char, float,
etc.).

We'll go through a basic example of passing by value versus passing by pointer
(or reference in rust) and see how the differ in both the code written and the
resultant assembly.

Below we have a struct which keeps a hash value and the number of times it's
been hashed. It's a bit of a nonsensical toy idea, but should serve the purpose.
We're going to run three iterations of this hash for pass by value versus pass
by pointer to see how it looks.


```c
typedef struct {
    /// The number of times the data has been hashed 
    int instances;
    /// The current hash
    char hash[64];
} some_hash_type;
```

Pass By Value
===============

For those newer to programing or not from a C (or C++) background, pass by value
may be the most intuitive way to think about things. We take the value in, we
modify it and then we return the modified value. 

```c
some_hash_type hash_by_value(some_hash_type hash_tracker){
    int index;
    hash_tracker.instances++;
    index = hash_tracker.instances % sizeof(hash_tracker.hash);
    hash_tracker.hash[index]++;
    return hash_tracker;
}
```

> Don't try to understand the _hash_ logic too much it's pretty nonsensical and
is really just a fancy counter of its own.  I didn't want to have to pull in a
library with a real hash function.

The operation of three iterations would look like:
```c
some_hash_type hash_tracker;
memset(&hash_tracker, 0, sizeof(hash_tracker));
hash_tracker = hash_by_value(hash_by_value(hash_by_value(hash_tracker)));
```

Using the embed feature of [Compiler Explorer][compiler explorer] we can see
what this looks like and it's assembly.

<iframe width="800px" height="500px" src="https://godbolt.org/e#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAMzwBtMA7AQwFtMQByARg9KtQYEAysib0QXACx8BBAKoBnTAAUAHpwAMvAFYTStJg1AB9U8lJL6yAngGVG6AMKpaAVxYMQAJgCcpBwAyeAyYAHLuAEaYxN5cpAAOqAqEtgzObh7efonJNgJBIeEsUTFecZaY1qlCBEzEBOnunr4WmFZ5DDV1BAVhkdGxFrX1jZktCsM9wX3FA2UAlBaorsTI7BwApF4AzMHIblgA1BvbjhPEwcAAdAgn2BsaAIIPjwQAnvGYWFSH567WxwA7AAhF6HcGHAD00MOABUEJhDgx%2BsRDqgfjY2ApDgQEYd0ExaocEExsVFGMTSQj0McnhDDsECAyGBNDGsFCdQXSIdDIXC8cgVsRGEySQpbtzwcgSaixbcAKzAgBskg28oAIpyXhtAerfqg2MY5cZ3p8tU8XgoDZgjVSTR9EcaIm9jAA3MSuTAQK2G42mx12gjEJjIADW0XmOq5j3pjOZWFU5pjEL9wbD0SuwVZDHZW1BXlB22jsYYCeO2z1qZD4eImZZtRzmGxW3lvzwAC9MOiIFX07W5ZGi2CU4G0zWblS1cDggm1ZqC3mk/ThQQVgxKeKTWPokmdZqLU8fTa/Q7DiwXXLohBIyDLdbbZv/RuEFvqzuh082CwlAQIFslb2NakIcGjAcknbdoBEaDtGUGoiclZ2s6boel6Touu6bhoUhGGoT2o5vsQ8zEUmK5rs%2Br59ruuocIstCcPKvCeBwWikKgnCOPqKxrMcOw8KQBCaLRiyhiA8qgfRHCSExQlsZwvAKCAoGCSxtGkHAsBIGgLDxHQ0TkJQ2m6fQMTIPshjAFIGigTQtAENEikQBEskRMEdRvJw/HaWwggAPIMLQHmqaQWAsBZ4jBfgwpVK6TayZgqiVK49mebwjJtLJtB4BEwbEG8zhYLJQZ4CwqWLFQBjAAoABqeCYAA7r5nzMfx/CCCIYjsFIMiCIoKjqMFuhxAYRggKYxjmFlESKZAiyoPEHSKRwCltJUHT2KWoyeHEgTTEUJR6DkKQCFth1JMdDC9PtAzlKtVQCF0IwuE0egVPdnSTFdKKvZMp3lJ9e3fVwixWtxXUCcK6w8HRDEycF7EcKoAAcSoALQqoc5lGIcUhXBoeOHBAjjAbghAkLx2xxIczg6Xp8F8fMvAqVoxGkKJ4n6Jw0mkMxrEIwpSkCUJrOSV4cN8/JQuqazsXEMkdiSEAA"></iframe>

The important thing to notice is the `movups` instruction calls.  

```asm
        movups  xmm0, xmmword ptr [rbp - 288]
        movups  xmm1, xmmword ptr [rbp - 272]
        movups  xmm2, xmmword ptr [rbp - 256]
        movups  xmm3, xmmword ptr [rbp - 240]
        movups  xmmword ptr [rax + 48], xmm3
        movups  xmmword ptr [rax + 32], xmm2
        movups  xmmword ptr [rax + 16], xmm1
        movups  xmmword ptr [rax], xmm0
```

It is here that we need to disambiguate the term *move*.  For assembly, things
like `moveups`, it is copying data from one location to another.  For languages
like rust and C++ *move* means that an item _may_ stay in place in storage, but
the original creator of the object no longer needs it and will not try to re-use
the object's storage location.

> I'm not happy with that disambiguation of *move* but the assembly instruction
name deviates from higher level language definition.  Probably why rust prefers
the term *ownership*.


The `movups` are 128 bit copies.  We're doing 8 of these or copying 1024 bytes.
The example structure happens to be just over 512.  So it looks like we're
copying the value into and out of each function invocation.

Pass By Pointer
===============

As mentioned above pass by value results in copying in order to take the value in
and to return it.  When using pass by pointer one only needs to copy the storage
location of the data and that storage location is directly modified.

Often times in C, when using pass by pointer, functions will have a boolean or
integer result in order to communicate failures and return codes. A version of
this hash logic might look like:

```c
void hash_by_pointer(some_hash_type * hash_tracker){
    int index;
    hash_tracker->instances++;
    index = hash_tracker->instances % sizeof(hash_tracker->hash);
    hash_tracker->hash[index]++;
}
```

If one were to use this for 3 iterations it would look like:

```c
some_hash_type hash_tracker;
memset(&hash_tracker, 0, sizeof(hash_tracker));
hash_by_pointer(&hash_tracker);
hash_by_pointer(&hash_tracker);
hash_by_pointer(&hash_tracker);
```

Since this is `void` return we could make it like the pass by pointer and return
the pointer passed in.
> Side note, I was a C developer for over a decade before I realized
[`memcpy()`][memcpy] returns the destination.

```c
some_hash_type * hash_by_pointer(some_hash_type * hash_tracker){
    int index;
    hash_tracker->instances++;
    index = hash_tracker->instances % sizeof(hash_tracker->hash);
    hash_tracker->hash[index]++;
    return hash_tracker;
}
```

Then our operation could look almost like the pass by value version:

```c
some_hash_type hash_tracker;
memset(&hash_tracker, 0, sizeof(hash_tracker));
hash_by_pointer(hash_by_pointer(hash_by_pointer(&hash_tracker)));
```

And the [Compiler Explorer][compiler explorer] version of this:

<iframe width="800px" height="500px" src="https://godbolt.org/e#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAMzwBtMA7AQwFtMQByARg9KtQYEAysib0QXACx8BBAKoBnTAAUAHpwAMvAFYTStJg1AB9U8lJL6yAngGVG6AMKpaAVxYMQAJlIOAMngMmABy7gBGmMTeAMykAA6oCoS2DM5uHt7xickCAUGhLBFRXrGWmNYpQgRMxARp7p4%2BZRUCVTUEeSHhkTEW1bX1GU39HYFdhT0lAJQWqK7EyOwcAKQlgchuWADUy9GOCgTEgcAAdAi72MsaAIJX1wQAnnGYWFRbB8Su1jsA7ABCdy2QK2AHowVsACoITBbBjdYhbVBvGxsBRbAjQrboJjVLYIJhoiKMPEE6HoHY3YFbQIEakMA6GRYKXYAynAsEgyGY5DzYiMWn4hTnNlA5D4hGC84AVj%2BADZJMspQARFl3ZY/JXvVBsYyS4yPZ6qm53BTazC60n6p4wgBUJKFxjCD2MCRpkQgpp1eoNtvtCH1xCYyAA1pEpurWdcqTS6VhVEao8DvYGQ5EALQXQIMhhM1YArwA6KR6MMOM7aKa5NB0PEDPRbBZ6o5zBo1ZS954ABemCRECrqdrF0l4aLgKTlsO1fTQ9Jir%2BgTjipVBbzCapfII8wYfoDU%2BICfVKuNN095u91q2LGdkvd4f%2BJrNFodPp3k4HCbYLCUBAgq1l/ZrUgtg0ICkm7XsALDEdIz1J0XVQN1iD7S04NdQR3Vg500IId0/0g4gpkIhMNy3V8UxrA8NQ4GZaE4KVeE8DgtFIVBOEcLV5kWHYSh4UgCE0aiZmDEApRA2iOEkBiBJYzheAUEAQP4pjqNIOBYCQNAWDiOhInIShNO0%2BgomQDZDGAKQNBAmhaBw4h5IgMJpLCQIageTheM0thBAAeQYWg3OU0gsBYMzxEC/A%2BQqAA3FtpMwVRylcHD3N4N1xOY2g8DCQNiAeZwsGkw48BYFKZioAxgAUAA1PBMAAd2855GN4/hBBEMR2CkGRBEUFR1EC3QuH0MyQFMYxzEysJ5MgGZUDiGwBHkjg5MwKwFs8CAHEGTwhv8MYCiKPQEiSdbtqO7J1s6A6eiG5p1raAYXAaPQ7sqEYrvhF6RjO273v2z6uBmU1OM6vi%2BSWHgaLoqTAtYjhVAADllNN5S2UyjC2KQTg0bGtggRwgNwQgSG46Ihq2ZwtJ0hFVjJqZeCUrRCNIYTRP0ThJNIRjmLhuSFL4gTmfErwYZ52SBeU5mYrslIQEkIA"></iframe>

Comparing
=========

If you look at the assembly of the two versions there are a couple of differences.

Looking at just the function definitions we can see that the pass by value seems
to be manipulating the stack a bit more to make room for the struct.

```asm
hash_by_value:                          # @hash_by_value
        push    rbp
        mov     rbp, rsp
        sub     rsp, 16
        mov     rax, rdi
        mov     qword ptr [rbp - 16], rax       # 8-byte Spill
        lea     rsi, [rbp + 16]
```


Where things really start to show up is when one looks at the usage of the
functions in `my_hasher()` in the [Compiler Explorer][compiler explorer] samples.
The pass by pointer version has none of the `movups` instructions that were so
prevelant in the pass by value.

Rust Pass by Value (Move)
=========================

Lets look at how rust does this.  When rust does a pass by value it's normally
considered a move of the value. Again move here does not imply an assembly `mov` instruction.

Passing by value in rust would look something like
```rust
pub struct SomeHashType {
    instances: u32,
    hash: [u8; 64],
}

pub fn hash_by_value(mut hash_tracker: SomeHashType) -> SomeHashType {
    hash_tracker.instances += 1;
    let index = hash_tracker.instances as usize % hash_tracker.hash.len();
    hash_tracker.hash[index] += 1;
    hash_tracker
}

pub fn my_hasher() -> SomeHashType {
    let mut hash_tracker = SomeHashType{ instances: 0, hash: [0; 64]};
    hash_by_value(hash_by_value(hash_by_value(hash_tracker)))
}
```

And the [Compiler Explorer][compiler explorer] is
<iframe width="800px" height="500px" src="https://godbolt.org/e#g:!((g:!((g:!((h:codeEditor,i:(filename:'1',fontScale:14,fontUsePx:'0',j:1,lang:rust,selection:(endColumn:2,endLineNumber:16,positionColumn:1,positionLineNumber:1,selectionStartColumn:2,selectionStartLineNumber:16,startColumn:1,startLineNumber:1),source:'pub+struct+SomeHashType+%7B%0A++++instances:+u32,%0A++++hash:+%5Bu8%3B+64%5D,%0A%7D%0A%0Apub+fn+hash_by_value(mut+hash_tracker:+SomeHashType)+-%3E+SomeHashType+%7B%0A++++hash_tracker.instances+%2B%3D+1%3B%0A++++let+index+%3D+hash_tracker.instances+as+usize+%25+hash_tracker.hash.len()%3B%0A++++hash_tracker.hash%5Bindex%5D+%2B%3D+1%3B%0A++++hash_tracker%0A%7D%0A%0Apub+fn+my_hasher()+-%3E+SomeHashType+%7B%0A++++let+mut+hash_tracker+%3D+SomeHashType%7B+instances:+0,+hash:+%5B0%3B+64%5D%7D%3B%0A++++hash_by_value(hash_by_value(hash_by_value(hash_tracker)))%0A%7D'),l:'5',n:'0',o:'Rust+source+%231',t:'0')),k:50,l:'4',n:'0',o:'',s:0,t:'0'),(g:!((h:compiler,i:(compiler:r1610,filters:(b:'0',binary:'1',commentOnly:'0',demangle:'0',directives:'0',execute:'1',intel:'0',libraryCode:'0',trim:'1'),flagsViewOpen:'1',fontScale:14,fontUsePx:'0',j:1,lang:rust,libs:!(),options:'',selection:(endColumn:25,endLineNumber:65,positionColumn:25,positionLineNumber:65,selectionStartColumn:25,selectionStartLineNumber:65,startColumn:25,startLineNumber:65),source:1,tree:'1'),l:'5',n:'0',o:'rustc+1.61.0+(Rust,+Editor+%231,+Compiler+%231)',t:'0')),k:50,l:'4',n:'0',o:'',s:0,t:'0')),l:'2',n:'0',o:'',t:'0')),version:4"></iframe>


Looking at the assembly it is overall a bit more.  There are some reasons rust
is both a memory safe language and not quite as fast as C by default.
For example this chunk here is panicking if we exceeded the bounds of the hash
array:
```asm
.LBB0_5:
        mov     rdi, qword ptr [rsp + 8]
        lea     rdx, [rip + .L__unnamed_2]
        mov     rax, qword ptr [rip + core::panicking::panic_bounds_check@GOTPCREL]
        mov     esi, 64
        call    rax
        ud2
```

The important bit is here:
```asm
        call    qword ptr [rip + example::hash_by_value@GOTPCREL]
        lea     rdi, [rsp + 160]
        lea     rsi, [rsp + 232]
        call    qword ptr [rip + example::hash_by_value@GOTPCREL]
        mov     rdi, qword ptr [rsp + 8]
        lea     rsi, [rsp + 160]
        call    qword ptr [rip + example::hash_by_value@GOTPCREL]
```
You'll notice there are no `memcpy` or `movups` between the function calls.

Rust Pass by Reference
======================

Rust allows one to pass by reference.  This is very similar to C's pass by
pointer.

Pass by reference would look like:

```rust
pub struct SomeHashType {
    instances: u32,
    hash: [u8; 64],
}

pub fn hash_by_reference(hash_tracker: &mut SomeHashType) -> &mut SomeHashType {
    hash_tracker.instances += 1;
    let index = hash_tracker.instances as usize % hash_tracker.hash.len();
    hash_tracker.hash[index] += 1;
    hash_tracker
}

pub fn my_hasher() -> SomeHashType {
    let mut hash_tracker = SomeHashType{ instances: 0, hash: [0; 64]};
    hash_by_reference(hash_by_reference(hash_by_reference(&mut hash_tracker)));
    hash_tracker
}
```

The [Compiler Explorer][compiler explorer] output is:

<iframe width="800px" height="500px" src="https://godbolt.org/e#g:!((g:!((g:!((h:codeEditor,i:(filename:'1',fontScale:14,fontUsePx:'0',j:1,lang:rust,selection:(endColumn:58,endLineNumber:15,positionColumn:58,positionLineNumber:15,selectionStartColumn:58,selectionStartLineNumber:15,startColumn:58,startLineNumber:15),source:'pub+struct+SomeHashType+%7B%0A++++instances:+u32,%0A++++hash:+%5Bu8%3B+64%5D,%0A%7D%0A%0Apub+fn+hash_by_reference(hash_tracker:+%26mut+SomeHashType)+-%3E+%26mut+SomeHashType+%7B%0A++++hash_tracker.instances+%2B%3D+1%3B%0A++++let+index+%3D+hash_tracker.instances+as+usize+%25+hash_tracker.hash.len()%3B%0A++++hash_tracker.hash%5Bindex%5D+%2B%3D+1%3B%0A++++hash_tracker%0A%7D%0A%0Apub+fn+my_hasher()+-%3E+SomeHashType+%7B%0A++++let+mut+hash_tracker+%3D+SomeHashType%7B+instances:+0,+hash:+%5B0%3B+64%5D%7D%3B%0A++++hash_by_reference(hash_by_reference(hash_by_reference(%26mut+hash_tracker)))%3B%0A++++hash_tracker%0A%7D'),l:'5',n:'0',o:'Rust+source+%231',t:'0')),k:50,l:'4',n:'0',o:'',s:0,t:'0'),(g:!((h:compiler,i:(compiler:r1610,filters:(b:'0',binary:'1',commentOnly:'0',demangle:'0',directives:'0',execute:'1',intel:'0',libraryCode:'0',trim:'1'),flagsViewOpen:'1',fontScale:14,fontUsePx:'0',j:1,lang:rust,libs:!(),options:'',selection:(endColumn:1,endLineNumber:1,positionColumn:1,positionLineNumber:1,selectionStartColumn:1,selectionStartLineNumber:1,startColumn:1,startLineNumber:1),source:1,tree:'1'),l:'5',n:'0',o:'rustc+1.61.0+(Rust,+Editor+%231,+Compiler+%231)',t:'0')),k:50,l:'4',n:'0',o:'',s:0,t:'0')),l:'2',n:'0',o:'',t:'0')),version:4"></iframe>

There are a few differences with the rust pass by value and the rust pass by
reference but for the most par they are fairly close .  

One may notice the ommision of a `memcpy` in the pass by reference
version.  This is because these examples are without optimizations.  One can
compile with optimizations or change the pass by value example to be the
following to get rid of the `memcpy` that isn't present in the pass by
reference.

```rust
pub fn my_hasher() -> SomeHashType {
    hash_by_value(hash_by_value(hash_by_value(SomeHashType{ instances: 0, hash: [0; 64]})))
}
```

The pass by reference uses `mov` instructions for the argument memory location,
while the pass by value uses the `lea` instruction using a bit more indirection,
and a bit more loading cost.  But this extra cost generally won't come close to
the cost of copying values around.

Summary
=======

Passing by value in rust does not have the same negative impacts as pass by
value in C.  As such the stigma for pass by value in C should be avoided in rust.

It does appear at the micro level pass by reference in rust may
have less assembly instructions than pass by value.  However the two outputs are
probably close enough to require one to profile with timings before trying to
argue one way or another in the general case.

While it wasn't discussed here, pass by value in rust can provide
some API benefits due to rusts ownership rules.

One may notice that all of these examples were done without compiler
optimizations turned on.  When turning on optimizations for the rust examples
the function calls get inlined resulting in more assembly bloat.  While LTO(link
time optimizations) may inline functions from other modules I wanted to focus on
the common case for non local functions.


[memcpy]: https://cplusplus.com/reference/cstring/memcpy/
[compiler explorer]: https://godbolt.org/