---
layout: post
title:  "Timing rust derive macros"
date:   2023-07-21 21:10:03 -0700
categories: rust
---

I was working on updating a rust code base to utilize some newer types. The
newer types I had written derived the minimum they needed, `Debug` and `Clone`.
The using types were deriving a few more traits. 

```rust
#[derive(Debug, Clone, Ord, PartialOrd, Eq, PartialEq, Serialize, Deserialize)]
pub struct ContainingType {
    field: NewType
}

#[derive(Debug, Clone)]
pub struct NewType {
    field: usize
}

```

I had a choice to make, derive the missing ones on `NewType` or remove
unnecessary ones from `ContainingType`. I chose to remove what I could from the
`ContainingType`.  The only justification for this decision was leaning on
[YAGNI][YAGNI]. My thought was less is better.

In this endeavor I realized that part of me was thinking removing unused derives
might speed up compile time. The compiler has to do some work deriving these
implementations, as well as compiling these derivations.

I decided that this should really be timed and considered instead of assuming it
will be fast enough to matter.

## The Test Cases

While I could have tested and timed in the code base I was changing. I was also
changing the underlying types, which means it wasn't easy to focus on the effect
of just the derives. I also think the code base is large enough that there is
likely to be a decent amount of overall noise that could hide or mask the derive
times.

I created an application that would generate a rust crate made up of nested
structs. The application had the ability to set how many struct nestings there
would be and which derives would be placed on the structs.

<details>
  <summary>The Application Code</summary>

<div markdown="1">
{% raw %}
```rust
use std::path::PathBuf;
use clap::Parser;

const MOD_PREFIX: &str = "my_struct_";
const STRUCT_PREFIX: &str = "MyStruct";

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    /// Optional directory to create the project in
    #[arg(short, long)]
    out_dir: Option<PathBuf>,

    /// Derives to use for the structs
    #[arg(long, value_delimiter = ',')]
    derives: Vec<String>,

    /// Imports to use for the structs
    #[arg(short, long, default_value = "")]
    imports: String,

    /// Number of nested structures to create
    #[arg(short, long, default_value = "10")]
    depth: usize,

    /// Package name to use in Cargo.toml
    #[arg(short, long, default_value = "my_structs")]
    package_name: String,
}

fn main() {
    let cli = Cli::parse();
    if let Some(out_dir) = cli.out_dir {
        std::fs::create_dir_all(&out_dir).unwrap();
        std::env::set_current_dir(&out_dir).unwrap();
    }

    std::fs::create_dir_all("src").unwrap();
    std::fs::write("Cargo.toml", cargo_toml_contents(cli.package_name)).unwrap();
    std::fs::write("src/lib.rs", lib_contents(cli.depth)).unwrap();
    for depth in 0..cli.depth {
        let struct_file = format!("src/{}.rs", module_name(depth));
        std::fs::write(&struct_file, struct_file_contents(depth, &cli.derives, &cli.imports)).unwrap();
    }

}

fn module_name(depth: usize) -> String {
    format!("{MOD_PREFIX}{depth}")
}

fn cargo_toml_contents(package_name: impl AsRef<str>) -> String {
    let package_name = package_name.as_ref();
    format!("[package]\nname = \"{package_name}\"\nversion = \"0.1.0\"\nedition = \"2021\"\n")
}

fn struct_file_contents<'a, I, S>(depth: usize, derives: I, imports: impl AsRef<str>) -> String
    where
        I: IntoIterator<Item = &'a S>,
        S: ToString + 'a + ?Sized,
{
    let derives = derives.into_iter().map(|d| d.to_string()).collect::<Vec<_>>().join(", ");
    let member_type = match depth {
        0 => "usize".to_string(),
        _ => format!("crate::{}::{STRUCT_PREFIX}{}", module_name(depth -1), depth - 1),
    };
    let imports = imports.as_ref();
    format!("{imports}\n\n#[derive(Debug, {derives})]\npub struct {STRUCT_PREFIX}{depth} {{\n    pub field: {member_type},\n}}\n")
}

fn lib_contents(depth: usize) -> String
{
    let modules = (0..depth).map(|d| format!("mod {};", module_name(d))).collect::<Vec<_>>();
    let last_struct = depth - 1;
    let mod_usage = modules.join("\n");
    let last_mod = module_name(depth - 1);
    format!("{mod_usage}\npub use {last_mod}::{STRUCT_PREFIX}{last_struct};\n")
}
```
{% endraw %}
</div>
</details>

I decided to focus on three cases:

1. `Debug` only. `Debug` often comes in handy for development. We have a setting
   that requires `Debug` on all the structs.
2. `Debug, Eq, PartialOrd, Ord, PartialOrd`. Some of the code I was cleaning up
   had `Ord` and `PartialOrd`. Looking at the types themselves, it didn't seem
   useful to compare the types to each other. There are some uses for `Ord`
   outside of `<`, `>`, etc. For example [BTreeMap][BTreeMap] uses `Ord` to
   store the keys.
3. `Debug, Serialize, Deserialize`. There were some types we wanted to
   serialize. However, at times it appeared that `Serialize` and `Deserialize`
   might have gotten sprinkled around a bit more than needed. We already have a
   dependency on [serde][serde] so it doesn't hurt too much using it in more
   places, but [YAGNI][YAGNI] makes me want to omit the derives unless there is
   a need.


### The Timings

| Derives    | time |
| -------- | ------- |
| `Debug` | 200ms |
| `Debug, Eq, PartialEq, Ord, PartialOrd` | 280ms |
| `Debug, Serialize, Deserialize`  | 860ms |

These are the timings for nesting 100 structs. I.e. `Struct<n>` contains one
field with `Struct<n-1>`. `Struct<n-1>` contains one field with `Struct<n-2>`.
`Struct0` contains one field of `usize`.

Assuming we can extrapolate the cost evenly, it looks like it's 0.8ms per struct
for the combined usage of `Eq, PartialEq, Ord, PartialOrd`. We might be able to
say that each one of these derives is ~0.2ms, but that would require further
testing. These derives are built into the compiler and as such are able to be
well optimized. The derivations are usually fairly simple logic.

For `serde` we can see that there is 8x more time spent. Again assuming we can
extrapolate cost evenly, it's 6.6ms per struct. `serde` is not built into the
compiler, it has many options that can be applied to the derivation and the
derived implementation is a bit more complex. With that in mind it's not
surprising it takes more time to compile. One thing to note is that the
implementations of `Deserialize` are about two times the size of the
implementation of `Serialize`. Deriving only `Serialize` I was getting ~1.3ms
per struct.

To get timings of just the package. I first built the package with `cargo build`
then I cleaned *only* the package and invoked `cargo build` again.

```console
cargo build
cargo clean -p my_structs && cargo build
```

I looked at the timing coming from the output of `cargo build`

```console
Finished dev [unoptimized + debuginfo] target(s) in 0.20s
```

For the `serde` test case I had to first add the serde dependency 
`cargo add serde --features derive`

This was done on a Mac m2 max. The `serde` version from the lock file
was 1.0.174. The rust version was 1.68.2.

The commands to generate the crates using the application:

```
cargo run -- -o ../derives/vanilla_100 --depth 100
cargo run -- -o ../derives/ord_100 --derives=Ord,PartialOrd,Eq,PartialEq --depth 100
cargo run -- -o ../derives/serde_100 --derives=Serialize,Deserialize --imports="use serde::{Serialize, Deserialize};" --depth 100
```

## Summary

Macro derives do have a cost. For some of the built in traits this cost is
fairly negligible. For more complex derives the cost may start to be noticeable.
While the 6.6ms per type isn't noticeable on a per type basis. A user can see
the 660ms time delay of 100 such types. This time may be insignificant compared
to a project that takes minutes to build. 

For me I don't think I'll worry too much about excessive `PartialOrd` and `Ord`,
but I'll probably push back a bit more on unnecessary usages of `Serialize` and
`Deserialize`.

[YAGNI]: https://en.wikipedia.org/wiki/You_aren't_gonna_need_it
[BTreeMap]: https://doc.rust-lang.org/std/collections/struct.BTreeMap.html
[serde]: https://serde.rs/
