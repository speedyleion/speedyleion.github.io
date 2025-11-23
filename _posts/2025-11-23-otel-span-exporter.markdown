---
layout: post
title:  "Opentelemetry SpanExporter"
date:   2025-11-23 14:00:03 -0800
categories: tracing rust
---

The previous posts about tracing in rust glossed over the initialization.
In particular there is an `exporter`, `resource`, and a `provider`.

```rust
    let exporter = opentelemetry_otlp::SpanExporter::builder()
        .with_http()
        .with_protocol(Protocol::HttpJson)
        .build()?;
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .build();
    let provider = opentelemetry_sdk::trace::SdkTracerProvider::builder()
        .with_resource(resource)
        .with_batch_exporter(exporter)
        .build();
```

A large part of it was I didn't really understand them. The names weren't
intuitive to me and their documentation seemed to assume you were already
familiar with the Opentelemetry terminology.

This post is meant to dig a bit deeper into the `exporter`.

# SpanExporter

The first statement we see is the creation of a
[SpanExporter](https://docs.rs/opentelemetry_sdk/latest/opentelemetry_sdk/trace/trait.SpanExporter.html).
```rust
    let exporter = opentelemetry_otlp::SpanExporter::builder()
        .with_http()
        .with_protocol(Protocol::HttpJson)
        .build()?;
```

A `SpanExporter` handles formatting and sending the span data outside of the application.

This particular `SpanExporter` is coming from the
[opentelemetry_otlp](https://docs.rs/opentelemetry-otlp/latest/opentelemetry_otlp/index.html)
crate. It exports span data using the Opentelemetry Protocol (OTLP). The
OTLP exporter was chosen for this example as the protocol is commonly supported
by most trace visualization tools like Jaeger. There are multiple supported
formats for OTLP. This example used
[HttpJson](https://docs.rs/opentelemetry-otlp/latest/opentelemetry_otlp/enum.Protocol.html#variant.HttpJson),
the reasoning being I could set up an Http server and echo the
human readable Json. For production use I would suggest choosing one of the binary protocols:

- [HttpBinary](https://docs.rs/opentelemetry-otlp/latest/opentelemetry_otlp/enum.Protocol.html#variant.HttpBinary)
- [GRPC](https://docs.rs/opentelemetry-otlp/latest/opentelemetry_otlp/enum.Protocol.html#variant.Grpc)

Some other exporter crates are:

- [opentelemetry-jaeger](https://docs.rs/opentelemetry-jaeger/latest/opentelemetry_jaeger/),
as the docs say, this is deprecated since Jaeger can accept OTLP data.
- [opentelemetry-zipkin](https://docs.rs/opentelemetry-zipkin/latest/opentelemetry_zipkin/)
exports in the [zipkin](https://zipkin.io/) format.
- [opentelemetry-stdout](https://docs.rs/opentelemetry-stdout/latest/opentelemetry_stdout/)
this is an exporter that will dump trace data to stdout.

## StdOut SpanExporter

Let's use the `stdout` exporter and see what we get. One will need to add
`opentelemetry-stdout` as a dependency and replace the original `exporter`
statement with the following:
```rust
    let exporter = opentelemetry_stdout::SpanExporter::default();
```

<details>
  <summary>Full script using stdout exporter</summary>

<div markdown="1">
{% raw %}
```rust
#!/usr/bin/env -S cargo +nightly -Zscript
---cargo
[dependencies]
opentelemetry = "0.31"
opentelemetry_sdk = "0.31"
opentelemetry-stdout = "0.31"
---

use opentelemetry::{
    Context,
    trace::{TraceContextExt, Tracer},
};
use opentelemetry_sdk::Resource;
use std::{thread::sleep, time::Duration};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let exporter = opentelemetry_stdout::SpanExporter::default();
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .build();
    let provider = opentelemetry_sdk::trace::SdkTracerProvider::builder()
        .with_resource(resource)
        .with_batch_exporter(exporter)
        .build();
    opentelemetry::global::set_tracer_provider(provider.clone());

    step1();
    step2();
    Ok(provider.shutdown()?)
}

fn step1() {
    let tracer = opentelemetry::global::tracer("tracer-name");
    let span = tracer.start("step1");
    let context = Context::current_with_span(span);
    let _guard = context.attach();
    sleep(Duration::from_millis(10));
    println!("Step 1");
    inside_step1();
}

fn inside_step1() {
    opentelemetry::global::tracer("tracer-name").in_span("inside_step1", |_| {
        sleep(Duration::from_millis(30));
        println!("Inside Step 1");
    });
}

fn step2() {
    opentelemetry::global::tracer("tracer-name").in_span("step2", |_| {
        sleep(Duration::from_millis(20));
        println!("Step 2")
    });
}
```

{% endraw %}
</div>
</details>
<br/>

Running the script should result in output similar to the following:
```bash
Step 1
Inside Step 1
Step 2
Spans
Resource
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
	 ->  service.name=String(Static("tracing-example"))
Span #0
	Instrumentation Scope
		Name         : "tracer-name"

	Name         : inside_step1
	TraceId      : 3f9d606a211974eb3b91ba092d5afecb
	SpanId       : a45ce26c2b675d70
	TraceFlags   : TraceFlags(1)
	ParentSpanId : 4247b2fdbb3b5778
	Kind         : Internal
	Start time   : 2025-11-23 22:43:21.208442
	End time     : 2025-11-23 22:43:21.243523
	Status       : Unset
Span #1
	Instrumentation Scope
		Name         : "tracer-name"

	Name         : step1
	TraceId      : 3f9d606a211974eb3b91ba092d5afecb
	SpanId       : 4247b2fdbb3b5778
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-11-23 22:43:21.195887
	End time     : 2025-11-23 22:43:21.243541
	Status       : Unset
Span #2
	Instrumentation Scope
		Name         : "tracer-name"

	Name         : step2
	TraceId      : 93ea5003fb39bce01d0da5829c44fcb0
	SpanId       : dea37efc6eea724a
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-11-23 22:43:21.243592
	End time     : 2025-11-23 22:43:21.267158
	Status       : Unset
```

We can see that `Span #0` has the `Name` "inside_step1". It has a `ParentSpanId`
of `4247b2fdbb3b5778` which matches the `SpanId` of `Span #1`. We have to take
the difference of the `End time` and the `Start time` in order to compute the
duration of the span.

This isn't as easy to visualize as the Jaeger UI, but there are no extra
services needed to run.


# Summary

The `SpanExporter` determines both the format and the protocol used for sending
the span data to a service. Without an exporter the trace data would not leave
the application and thus would not be very useful.