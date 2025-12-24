---
layout: post
title:  "In Source Code Generation"
date:   2021-01-20 20:17:03 -0800
categories: cmake build-systems
---

Code generation is a common task supported by build systems. 
It is generally discouraged to generate files in the source directory and
commit these generated files. However, there are times where one may need to
go against this guidance:
- In some development environments, like highly regulated ones, it may be
  easier to review the generated file(s) than to take the steps necessary to
  approve a code generation tool.
- One may want to distribute these generated files for consumers, without
  forcing the consumers to utilize the code generation tool.

(If you know of other reasons please post them.)

Most build systems will connect any generated code files up to the clean
target. This means that anytime someone runs ``my_build_system clean`` *all*
generated files will be removed. For generated code that is committed, this
will cause extra burden on the developers as they'll have to rebuild before
committing or check back out the now deleted source files.

The trick to work around the build system is to not tell it about the
generated code.  We'll go over an example using CMake.

Using CMake to Generate in Source Code
======================================

{% include note.html content="This example assumes you understand a bit about 
CMake, in particular [add_custom_command()][add_custom_command] and 
[add_custom_target()][add_custom_target]." %}

First we'll create a [custom command][add_custom_command] that does 2 things:
- generate a source file, the ``copy`` command.
- generate a stamp file, the ``touch`` command.
{% highlight cmake %}
add_custom_command(
    COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/input.in ${CMAKE_CURRENT_SOURCE_DIR}/generated.c
    COMMAND ${CMAKE_COMMAND} -E touch "${CMAKE_BINARY_DIR}/my_generator.stamp"
    OUTPUT  ${CMAKE_BINARY_DIR}/my_generator.stamp
    DEPENDS input.in
    COMMENT "Generating code ..."
)
add_custom_target(generator_target DEPENDS ${CMAKE_BINARY_DIR}/my_generator.stamp)
{% endhighlight %}
One will notice that the ``OUTPUT`` only lists the stamp file. The generated
file is not marked as an output. This means that CMake doesn't know the file
will be created via this custom command. The input file is listed as a
``DEPENDS`` to ensure anytime a downstream target is built and the stamp
file either doesn't exist or is older than the input file this command will
run. It is important to note that if the generated source file is deleted and
the stamp file exists and is newer than the input file the custom command
will not be run.

We've also created a [custom target][add_custom_target]. For those unfamiliar
with CMake the two commands often go together for code generation. The custom
target allows for easier referencing from other targets, as well as providing
some other benefits.

CMake will complain if a source file is missing, unless it has the
[GENERATED][generated] property set. However setting the
[GENERATED][generated] property causes CMake to clean the file. This means we
either need to manually create an empty version of the source file to get
things started. Or one can utilize the [FILE(TOUCH <file>)][file_touch]
command at configure time. we'll show the [FILE(TOUCH <file>)][file_touch]
option as it is a little more automated.

One issue with generating a compiled source file is that the backend build
system, like [Ninja][ninja], will do an initial pass to see what's out of
date. Since the generated file is not listed as generated, the build system
will think it's up to date and not realize that by invoking the custom
command the generated file will be modified. We use the
[OBJECT_DEPENDS][object_depends] property to let CMake know that if the stamp
file changes, it affects the resultant output of the generated source file,
and thus the source file will need to be re-compiled.

{% highlight cmake %}
FILE(TOUCH ${CMAKE_CURRENT_SOURCE_DIR}/generated.c)
add_library(some_lib ${CMAKE_CURRENT_SOURCE_DIR}/generated.c)
add_dependencies(some_lib generator_target)
set_source_files_properties(${CMAKE_CURRENT_SOURCE_DIR}/generated.c 
    PROPERTIES OBJECT_DEPENDS ${CMAKE_BINARY_DIR}/my_generator.stamp
)
{% endhighlight %}

Caveats
=======

- For headers I haven't yet found a reliable incremental path for all build
  backends. In particular [Ninja][ninja], and guessing make, will do an
  initial inspection of the build tree to see what is out of date, and then
  run the build commands. Since the header isn't advertising itself as
  generated to CMake, there is no way for Ninja to know to mark users of the
  header as out of date during the initial inspection of the build tree. One
  can invoke the build twice to work around this, but this is error prone.


[add_custom_command]: https://cmake.org/cmake/help/latest/command/add_custom_command.html
[add_custom_target]: https://cmake.org/cmake/help/latest/command/add_custom_target.html
[generated]: https://cmake.org/cmake/help/latest/prop_sf/GENERATED.html
[file_touch]: https://cmake.org/cmake/help/latest/command/file.html#touch
[ninja]: https://ninja-build.org/
[object_depends]: https://cmake.org/cmake/help/latest/prop_sf/OBJECT_DEPENDS.html