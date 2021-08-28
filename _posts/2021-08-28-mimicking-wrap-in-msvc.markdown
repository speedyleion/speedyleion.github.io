---
layout: post
title:  "Mimicking `--wrap` for C code in MSVC"
date:   2021-08-28 14:16:03 -0700
categories: c windows msvc
---

`--wrap`
========

GCC and Clang have a linker flag called `--wrap`.  This flag allows one to
intercept a function at link time.

Let us say you have a funciton `foo()`.  If you use the linker flag
`--wrap=foo`, then the linker will re-direct all calls to `foo()` with calls
to `__wrap_foo()`.  The linker will also rename the implementation of
`foo()` as `__real_foo()`.  This means that one will need to implement a
function `__wrap_foo()` or else there will be a linker error.

Often times one does something like:

{% highlight c %}
int __wrap__foo(int some_arg){
    if(some_condition){
        return 0;
    }
    return __real_foo(some_arg);
}
{% endhighlight %}

This means that any calls to `foo()` will go to `__wrap_foo()`.  If the
condition is met then callers will get `0`.  If the condition is not met then
callers will be directed back to the original implementation of `foo()`.

The main problem with `--wrap` is that it only works with GCC and compilers
mimicking GCC, like Clang.  

[llvm-objcopy][llvm-objcopy]
============================

[objcopy][objcopy] is a gnu utility for copying object files.  LLVM has their
own version called [llvm-objcopy][llvm-objcopy].  Since Clang, the C language
compiler from LLVM, knows how to build and link windows libraries, I thought it
was worth a shot to see if [llvm-objcopy][llvm-objcopy] could work with windows
libraries.

I created a library, `foo.lib`, which is made up of one file, `foo.c`, with
the following contents:

{% highlight c %}
#include "foo.h"
const char *foo(int option) {
    return "This is the real foo";
}
{% endhighlight %}

> The header `foo.h` just has the declartion for the function `foo()`.

When I dump this library file using [llvm-objdump][llvm-objdump] the function
`foo` shows up in the output:

    $ llvm-objdump.exe --syms foo.lib

    foo.lib(CMakeFiles\foo.dir\foo.cpp.obj):        file format coff-x86-64

    SYMBOL TABLE:
    ...
    [13](sec  5)(fl 0x00)(ty  20)(scl   2) (nx 0) 0x00000000 foo
    ...

Running [llvm-objcopy][llvm-objcopy] to redefine the symbol and then dumping the new library
results in `__real_foo` showing up in the copied library.

    $ llvm-objcopy.exe --redefine-sym=foo=__real_foo foo.lib objcopy_foo.lib
    $ llvm-objdump.exe --syms objcopy_foo.lib

    objcopy_foo.lib(CMakeFiles\foo.dir\foo.cpp.obj):        file format coff-x86-64

    SYMBOL TABLE:
    ...
    [13](sec  5)(fl 0x00)(ty  20)(scl   2) (nx 0) 0x00000000 __real_foo
    ...

This looks promising, however trying to link against the copied library results in:

    objcopy_foo.lib : warning LNK4003: invalid library format; library ignored

Time to punt on [llvm-objcopy][llvm-objcopy].

MSVC Tools
==========

To be honest I should have looked at the MSVC tools first, since I'm trying to
figure out how to do something with MSVC outputs.  I happen to have a bias
towards clang and its tools.

There are a few tools provided with most MSVC installs for working with library
files:

- [DUMPBIN][DUMPBIN] similar to [llvm-objdump][llvm-objdump], it provides
  information on library and object files.
- [LIB][LIB] handles assembling and exracting library files.
- [EDITBIN][EDITBIN] handles editing object files.

These tools must be accessed through a Visual Studio command prompt.

Extracting the original object file
-----------------------------------

It may be that I couldn't figure it out, but it doesn't appear that you can
extract a function with the `/EXTRACT` flag it appears to only extract object
files.  One must know the exact name of the object file, and since I used CMake
to build, it had an intersting name.  This name also showed up in the
[llvm-objdump][llvm-objdump] operation:

    LIB /EXTRACT:CMakeFiles\foo.dir\foo.cpp.obj foo.lib

This created a file `foo.cpp.obj` in the current working directory. I copied
this file over to `editbin_foo.cpp.obj` so I could investigate the usage of
[EDITBIN][EDITBIN].  First, however, I wanted to see what the object file had in
it with [DUMPBIN][DUMPBIN]:

    dumpbin /symbols editbin_foo.cpp.obj
    Microsoft (R) COFF/PE Dumper Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.


    Dump of file editbin_foo.cpp.obj

    File Type: COFF OBJECT

    COFF SYMBOL TABLE
    ...
    00D 00000000 SECT5  notype ()    External     | foo
    ...

We can see that `foo` is visible in this object file.  My first try at renaming
`foo` in the object file:

    editbin /SECTION:foo=__real_foo editbin_foo.cpp.obj
    Microsoft (R) COFF/PE Editor Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.

    editbin_foo.cpp.obj : warning LNK4039: section 'foo' specified with /SECTION option does not exist

That seems like it didn't succeed to rename `foo`, :(.  However, I thought why
not dump again to double check I spelled `foo` right:

    dumpbin /symbols editbin_foo.cpp.obj
    Microsoft (R) COFF/PE Dumper Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.


    Dump of file editbin_foo.cpp.obj

    File Type: COFF OBJECT

    COFF SYMBOL TABLE
    ...
    00D 00000000 SECT5  notype ()    External     |
    ...

`foo` disappeared!?!  Maybe there is something funky about the leading double
underscore `__` so why not recopy the object file and try again:

    editbin /SECTION:foo=real_foo editbin_foo.cpp.obj
    Microsoft (R) COFF/PE Editor Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.

    editbin_foo.cpp.obj : warning LNK4039: section 'foo' specified with /SECTION option does not exist

    dumpbin /symbols editbin_foo.cpp.obj
    Microsoft (R) COFF/PE Dumper Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.


    Dump of file editbin_foo.cpp.obj

    File Type: COFF OBJECT

    COFF SYMBOL TABLE
    ...
    00D 00000000 SECT5  notype ()    External     | real_foo
    ...

That looks promising. Time to assemble into a library and try to link against
it:

    LIB editbin_foo.cpp.obj /OUT:editbin_foo.lib
    Microsoft (R) Library Manager Version 14.28.29336.0
    Copyright (C) Microsoft Corporation.  All rights reserved.

Building and linking an executable to `edtibin_foo.lib` when calling `real_foo`
worked.  Trying to call `foo` from the same set up resulted in an unresolved
symbol.

That renames the function at its entry point, but it doesn't change what the
callers are looking for.

[/ALTERNATENAME][ALTERNATENAME]
===============================

The [/ALTERNATENAME][ALTERNATENAME] flag can be used to tell the linker to
search for a different symbol name if the original can't be found.  

Since we've renamed the implementation of `foo` to `real_foo` we'll use the 
[/ALTERNATENAME][ALTERNATENAME] linker flag to link all the call sites of `foo`
to `__wrap_foo`.

Providing the following linker argument:

    /ALTERNATENAME:foo=__wrap_foo

The following `main.c` which links against the `edtibin_foo.lib`:

{% highlight c %}
#include <stdio.h>
#include "foo.h"

/// when option is other than 0, the fake implementation will be used.
const char *real_foo(int option);

const char *__wrap_foo(int option) {
    if(option == 0){
        return real_foo(option);
    }
    return "The fake version of foo";
}

int main(){
    printf("The return of foo(0) is: %s\n", foo(0));
    printf("The return of foo(1) is: %s\n", foo(1));
    return 0;
}
{% endhighlight %}

resulted in this output:

    The return of foo(0) is: This is the real foo
    The return of foo(1) is: The fake version of foo

Summary
=======

It looks like it's possible to mimic the `--wrap` flag using the MSVC toolchain.
It is a bit more work that can probably be pushed off onto the build system. 
This example is fairly simple, so it more testing would need to be done to flush
out any problems that got overlooked.  I have a feeling it may require a bit
more diligence versus being able to leverage the linker for wrapping functions.

[LIB]: https://docs.microsoft.com/en-us/cpp/build/reference/lib-reference?view=msvc-160
[objcopy]: https://web.mit.edu/gnu/doc/html/binutils_4.html
[llvm-objcopy]: https://llvm.org/docs/CommandGuide/llvm-objcopy.html
[llvm-objdump]: https://llvm.org/docs/CommandGuide/llvm-objdump.html
[EDITBIN]: https://docs.microsoft.com/en-us/cpp/build/reference/editbin-reference?view=msvc-160
[DUMPBIN]: https://docs.microsoft.com/en-us/cpp/build/reference/dumpbin-reference?view=msvc-160
[ALTERNATENAME]: https://devblogs.microsoft.com/oldnewthing/20200731-00/?p=104024