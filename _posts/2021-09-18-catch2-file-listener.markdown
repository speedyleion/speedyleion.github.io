---
layout: post
title:  "A Catch2 File Listener"
date:   2021-09-18 13:16:03 -0700
categories: c c++ catch2
---

[Catch2][Catch2] has support for reporting the test results output to a file
using the `-o, --out` flag.  This redirection, redirects all output.  We had a
desire to output *all* testing information in a style like Junit while also
providing the tester the nice failure only output on the command line.

[Catch2][Catch2] does not support multiple reporters, but it can support
multiple [listeners][listener].

Reporters and Listeners
=======================

[Catch2][Catch2] uses the terms _listeners_ and _reporters_.  From a users
perspective a reporter is basically the output style of the test results.  By
default only the failed test information is provided.

A [listener][listener] receives all of the test events, even passing test info.
A listener is a bit more generic in that it is meant do anything an integrator
might find a use for.  This is most likely the reason multiple listeners are
supported and there is no generic output file flag for them.

An interesting example of a listener that I ran across on the googles is
[https://doc.froglogic.com/squish-coco/latest/Catch2Listener.cpp.html](https://doc.froglogic.com/squish-coco/latest/Catch2Listener.cpp.html)
and the accompanying documentation
[https://doc.froglogic.com/squish-coco/latest/integration.html#catch2](https://doc.froglogic.com/squish-coco/latest/integration.html#catch2).

> Doing a quick look, I wasn't sure on the licensing of the code so I chose not
  to include the raw code here.

This listener ends up separating the coverage report for each test case and/or
section.  I haven't read the full documentation, but it seems one could more
easily know which tests target which parts of the code.

The Custom Listener
===================

At the time of this writing [Catch2][Catch2] is transitioning to version 3.
This custom listener example will be based on version 2.  


{% highlight c++ %}
#pragma once

#include <iostream>

#define CATCH_CONFIG_EXTERNAL_INTERFACES
#include "catch2/catch.hpp"

class Listener : public Catch::TestEventListenerBase {
public:
    Listener( Catch::ReporterConfig const& _config ) : Catch::TestEventListenerBase(_config){
        m_stream = std::unique_ptr<Catch::IStream const>(Catch::makeStream(outputFilename));
    }
    void testCaseStarting( Catch::TestCaseInfo const& testInfo ) override {
        m_stream->stream() << "Starting a test case";
    }
    static void SetOutputFilename(const std::string& name){
        outputFilename = name;
    }

protected:
    std::unique_ptr<Catch::IStream const> m_stream;
    static std::string outputFilename;
};
{% endhighlight %}

What we have here is a class derving from Catch2's base listener class
`Catch::TestEventListenerBase`.  Per the documentation on [listeners][listener],
all of the base class methods have default implementations. One only needs to
override the listener events they care about.  To keep the example small we've
only overridden the test case starting method. 

Since Catch2 won't pass any other arguments to the constructor, we utilize a
static method and member to hold the destination filename.  When the listener is
instantiated we provide the filename to Catch2's `makeStream()` function.  This
function isn't publicly documented, but the code is visible in the header.  If
the input stream name is empty then the provided stream will be Catch2's
standard out stream.  See
[CATCH_CONFIG_NOSTDOUT](https://github.com/catchorg/Catch2/blob/2c269eb6332bc1dd29047851ae1efc3cd4c260d2/docs/configuration.md#stdout).
When the input stream name isn't empty it's assumed to be a filename to create a
stream for.

The Test main()
===============

{% highlight c++ %}
#define CATCH_CONFIG_RUNNER
#include "catch2/catch.hpp"
#include "Listener.hpp"

CATCH_REGISTER_LISTENER( Listener )
int main( int argc, char* argv[] ) {
    Listener::SetOutputFilename("my_file.txt");
    int result = Catch::Session().run( argc, argv );
    return result;
}

TEST_CASE("Testing stuff"){
    REQUIRE(3==4);
}
{% endhighlight %}

In order to ensure we can set the output file name up before the listener is
instantiated we create our own main function.  Catch2 can provide a default for
you via the `CATCH_CONFIG_MAIN` macro, but this will prevent setting the output
filename up in time.

`CATCH_REGISTER_LISTENER( Listener )` is how we tell Catch2 to utilize our
listener.  This adds the class to the internal listener registry for Catch2, but
it does not instantiate the instance.  One thing to be aware of is that if the
`CATCH_REGISTER_LISTENER( Listener )` is placed in a separate file and there are
no other symbols in that file that the linker needs for the program, then the
`CATCH_REGISTER_LISTENER()` macro will not get linked in and thus the listener
will not be available.

`Listener::SetOutputFilename("my_file.txt");` sets the filename of the output
file.  One may want better logic here as this example will be relative to the
current working directory when the test executable is ran.

We then kick off the test execution with, 
`int result = Catch::Session().run( argc, argv );`.  It's during the `run()`
method that our custom listener will be instantiated.

If one runs this test there will be a file named `my_file.txt` created in the
current working directory and it's contents will have `Starting a test case`. At
the same time one will get the normal Catch2 output in the terminal.

Summary
=======

Though [Catch2][Catch2] does not natively provide file redirection for
listeners, one can add it to their specific listener class.  Adding a listener,
instead of a reporter, allows one to maintain the default terminal output of
Catch2 while still archiving test result information in a file.

The example was kept short and simply so as to prevent overload.  Hopefully it's
not much more work for one to figure out the other event methods listed for
[listeners][listener].  It may also take some work, but one might imagine how
they could make the listener conditional on the availability of an output file
name.

[Catch2]: https://github.com/catchorg/Catch2
[listener]: https://github.com/catchorg/Catch2/blob/v2.x/docs/event-listeners.md
