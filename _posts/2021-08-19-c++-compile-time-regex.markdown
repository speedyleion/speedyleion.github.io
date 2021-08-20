---
layout: post
title:  "C++ Compile Time Regex"
date:   2021-08-19 19:17:03 -0800
categories: c++ regex
---

In our C++ code we have a macro that is used to report an identifier that
someone can use to look things up.

For example, let us say it's a [Nato Stock Number (NSN)][NSN].  We might have
a function or macro like:

{% highlight c++ %}
NSN("3139-00-121-6210");
{% endhighlight %}

We want the NSN to be legibale in the code and we don't want to allow something
like:

{% highlight c++ %}
NSN("nonsense string");
{% endhighlight %}

While this could be caught run time, it would be nicer to let a user know when
at compile time that it's not correct.

Compile Time Regular Expressions
================================

Having listened to [CppCast Episode 171: Compile Time Regular Expressions with
Hana Dusíková][CPPCAST171], I was aware that there was as compile time regular
expression library.  However I didn't pay as much attention to the episode as I
thought...  

What better way to make up for my lack of attention by attempting to use the
library myself to try and enforce valid NSNs.

The Library
-----------

Like most code these days Hana has graciously shared the code on gitub,
[https://github.com/hanickadot/compile-time-regular-expressions](https://github.com/hanickadot/compile-time-regular-expressions).

I decided to try out the ``ctre.hpp`` single header option mentioned in the
readme.

The readme also has a nice example snippet to get started (I'm stuck at C++17):

{% highlight c++ %}
static constexpr auto pattern = ctll::fixed_string{ "h.*" };

constexpr auto match(std::string_view sv) noexcept {
    return ctre::match<pattern>(sv);
}
{% endhighlight %}

The Code Implementation
=======================

Modifying the example provided by the libary's readme I came up with:

{% highlight c++ %}
#include "ctre.hpp"

static constexpr auto nsn = ctll::fixed_string{ "\\d{4}-\\d{2}-\\d{3}-\\d{4}" };

constexpr auto match(std::string_view sv) noexcept {
    // For those unfamiliar with "!!", it will negate twice.  This will convert
    // a value/object to bool if it supports the bool() operator or similar.
    return !!ctre::match<nsn>(sv);
}

int main(){
    printf("Fake nsn doesn't match: %d\n", match("wrong_string"));
    printf("Real nsn matches: %d\n", match("3139-00-121-6210"));
    return 0;
}
{% endhighlight %}

And this printed out:

```
Fake nsn doesn't match: 0
Real nsn matches: 1
```

This is a run time example though, so now it's time to try a compile time.

First Failed Compile Time Implementation
----------------------------------------

My first attempt at trying to convert this to compile time was to use an ``if constexpr``.  

{% highlight c++ %}
constexpr auto match(std::string_view sv) noexcept {
    if constexpr(ctre::match<nsn>(sv)){
        return true;
    } else {
        return false;
    }
}
{% endhighlight %}

Admitedly I don't fully understand ``constexper`` other than it can result in
compile time evaluation. 

This failed to compile on MSVC with compiler error [C2131][C2131].

Successful Compile Time Implementation
--------------------------------------

After a few different failures, I was able to come upon this stackoverflow
answer,
[https://stackoverflow.com/a/66815881/4866781](https://stackoverflow.com/a/66815881/4866781).

So I reverted the ``match`` function and converted the ``printf()`` statements
to ``static_asserts()``.

{% highlight c++ %}
#include "ctre.hpp"

static constexpr auto nsn = ctll::fixed_string{ "\\d{4}-\\d{2}-\\d{3}-\\d{4}" };

constexpr auto match(std::string_view sv) noexcept {
    return !!ctre::match<nsn>(sv);
}

int main(){
    static_assert(match("wrong_string"));
    static_assert(match("3139-00-121-6210"));
    return 0;
}
{% endhighlight %}

Though the ``"wrong_string"`` will cause a compiler failure, you can comment it
out to see that the ``"3139-00-121-6210"`` succesfully compiles.


[NSN]: https://en.wikipedia.org/wiki/NATO_Stock_Number
[CPPCAST171]: https://cppcast.com/hana-dusikova/
[C2131]:  https://docs.microsoft.com/en-us/cpp/error-messages/compiler-errors-1/compiler-error-c2131?view=msvc-160