---
layout: post
title:  "In Source Code Generation"
date:   2021-01-20 20:17:03 -0800
categories: cmake build-systems
---

Code generation is a common task supported by build systems. It is generally
recommended to leave any generated files in the build directory, assuming out
of source builds.

It is generlaly discouraged to generate files in the source directory and
commit these generated files. However, there are times where one may need to
commit the generated files:
- In some development environments, like highly regulated ones, it may be
  easier to review the generated file(s) than to take the steps necessary to
  approve a code generation tool.
- One may want to distrubute these generated files for consumers, without
  forcing the consumers to utilze the code generation tool.
- If you know of other reasons please post them. 

Most build systems will connect any generated code files up to the clean
target. This means that anytime someone runs ``my_build_system clean`` *all*
generated files will be removed. For generated code that is commited, this
will cause extra burden on the developers as they'll have to rebuild before
commiting or check back out the now deleted source files.

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

For C/C++ code there are 2 possibilities when generating source files:
- The file is a header file and is only included by other files.
- The file is an actual code module and will itself be compiled.
Each one of these cases has a slightly different use case for hooking up to
downstream targets.

Header Files
------------

For header files there's usually three steps:
- Create an interface library. This is just a place holder library that allows
  us to propagate the ``generator_target`` dependency as well as populate the
  include directory of the generated file.  
- Make the interface library depend on the ``generator_target``. This ensures
  that the ``generator_target`` and thus the custom command is run prior to
  anything that depends on the interface library.
- Add the include directory to the interface library so downstream targets
  know where to find the generated header.

We created a library ``my_interface_library``
{% highlight cmake %}
add_library(my_interface_library INTERFACE)
add_dependencies(my_interface_library generator_target)
target_include_directories(my_interface_library INTERFACE ${CMAKE_BINARY_DIR})
{% endhighlight %}

Header files will show up as a dependency when the source files that include
them are compiled. Since the custom command will be run prior to any
downstream targets, the downstream targets will only look to see if the
header is out of date after it has been re-generated.

Code Module
-----------

When generating a file that will itself get compiled there are a couple of
things to do to work with CMake's checks.  

CMake will complain if a source file is missing, unless it has the
[GENERATED][generated] property set. However setting the
[GENERATED][generated] property causes CMake to clean the file. This means we
either need to manually create an empty version of the source file to get
things started. Or one can utilize the [FILE(TOUCH <file>)][file_touch]
command at configure time. we'll show the [FILE(TOUCH <file>)][file_touch]
option as it is a littl more automated.

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


[add_custom_command]: https://cmake.org/cmake/help/latest/command/add_custom_command.html
[add_custom_target]: https://cmake.org/cmake/help/latest/command/add_custom_target.html
[generated]: https://cmake.org/cmake/help/latest/prop_sf/GENERATED.html
[file_touch]: https://cmake.org/cmake/help/latest/command/file.html#touch
[ninja]: https://ninja-build.org/
[object_depends]: https://cmake.org/cmake/help/latest/prop_sf/OBJECT_DEPENDS.html