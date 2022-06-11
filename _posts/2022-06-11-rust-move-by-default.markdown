---
layout: post
title:  "Rust's Move by Default"
date:   2022-06-11 12:29:03 -0700
categories: rust c
---

As a c developer, one thing that has taken a while for me to get used to is
rust's move by default behavior.

As a c developer one learns to avoid passing large structures around because
these incur a copy cost.  This avoidance can often times lead into a general
avoidance of pass by value except when using primitive types (int, char, float,
etc.).

A disadvantage of avoiding pass by value is that one often isn't able to chain
or nest function calls.  Let's show this with an example.

```c
typedef struct {
    /// The number of times the data has been hashed 
    int instances;
    /// The current hash
    char hash[64];
} some_hash_type;
```

Here we have a struct which keeps a hash value and the number of times it's been
hashed. It's a bit of a nonsensical toy idea, but should serve the purpose.
We're going to run three iterations of this hash for pass by value versus pass
by pointer to see how it looks.


```c
void hash_by_pointer(some_hash_type * hash_tracker){
    int index;
    hash_tracker.instances++;
    index = hash_tracker.instances % sizeof(hash_tracker.hash);
    hash_tracker.hash[index]++;
}
```

If one were to use this for 3 iteration it would look like

```c
some_hash_type hash_tracker;
memset(&hash_tracker, 0, sizeof(hash_tracker));
hash_by_pointer(&hash_tracker);
hash_by_pointer(&hash_tracker);
hash_by_pointer(&hash_tracker);
```

Since this is `void` and there is nothing else to return we could make this a
little nicer to use by returning the pointer passed in.
> Side note, I was a C developer for over a decade before I realized
[`memcpy()`](memcpy) returns the destination.

```c
some_hash_type * hash_by_pointer(some_hash_type * hash_tracker){
    int index;
    hash_tracker.instances++;
    index = hash_tracker.instances % sizeof(hash_tracker.hash);
    hash_tracker.hash[index]++;
    return hash_tracker
}
```
Then our operation could look like
```c
some_hash_type hash_tracker;
memset(&hash_tracker, 0, sizeof(hash_tracker));
hash_by_pointer(hash_by_pointer(hash_by_pointer(&hash_tracker)));
```

[memcpy]: https://cplusplus.com/reference/cstring/memcpy/