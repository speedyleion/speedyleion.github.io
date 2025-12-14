---
layout: post
title:  "Opentelemetry Tracer"
date:   2025-12-13 16:50:03 -0800
categories: tracing rust
---

The previous post,
[Opentelemetry Trace Provider]({% post_url 2025-12-06-otel-trace-provider %}),
finished up the initialization of the Opentelemetry crates in rust. The post
discussed the creation of a 
[TraceProvider](https://docs.rs/opentelemetry/latest/opentelemetry/trace/trait.TracerProvider.html)
and how the `TraceProvider` provides 
[`Tracer`](https://docs.rs/opentelemetry_sdk/latest/opentelemetry_sdk/trace/struct.Tracer.html)s.
This post is going to cover what a `Tracer` is and how it's used.

The Opentelemetry description of a
[Tracer](https://opentelemetry.io/docs/specs/otel/trace/api/#tracer) only
requires that a Tracer provides a function to create a Span. That's more or less
all the rust version of a Tracer does. There are different ways of creating a
Span, but in the end it's still just creating a span.

# Getting a Tracer

Getting a tracer from a TraceProvider can be done using the 
[tacer()](https://docs.rs/opentelemetry/latest/opentelemetry/trace/trait.TracerProvider.html#method.tracer)
method.

```rust
    let tracer = provider.tracer("tracer-name");
```

This method takes a `name`. As the documentation says:

> The name should be the application name or the name of the library providing instrumentation.

This means that the top level application could be getting a Tracer called
`my_app`. While a sub crate could be getting a tracer called `crate-b`.

We can see this if we modify the script from the
[Opentelemetry Resource]({% post_url 2025-11-28-otel-resource %}) post and have
each Tracer use a different name.

```
Step 1
Inside Step 1
Step 2
Spans
Resource
	 ->  service.name=String(Static("tracing-example"))
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
Span #0
	Instrumentation Scope
		Name         : "tracer-inside-step1"

	Name         : inside_step1
	TraceId      : bd6c365ceaea01519209b92e81ce5b36
	SpanId       : cc3d0d7884d48c8a
	TraceFlags   : TraceFlags(1)
	ParentSpanId : ecf345390eea5a5e
	Kind         : Internal
	Start time   : 2025-12-14 01:15:19.584019
	End time     : 2025-12-14 01:15:19.619095
	Status       : Unset
Span #1
	Instrumentation Scope
		Name         : "tracer-in-step1"

	Name         : step1
	TraceId      : bd6c365ceaea01519209b92e81ce5b36
	SpanId       : ecf345390eea5a5e
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-12-14 01:15:19.571476
	End time     : 2025-12-14 01:15:19.619110
	Status       : Unset
Spans
Resource
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
	 ->  service.name=String(Static("step2_resource"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
Span #0
	Instrumentation Scope
		Name         : "tracer-in-step2"

	Name         : step2
	TraceId      : f9b9d6ffbad9ed107d32a6d3536b020c
	SpanId       : 2ac13fd290522524
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-12-14 01:15:19.619793
	End time     : 2025-12-14 01:15:19.644842
	Status       : Unset
```

<details>

  <summary>The script that provided the above output</summary>
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
    trace::{TraceContextExt, Tracer, TracerProvider},
};
use opentelemetry_stdout::SpanExporter;
use opentelemetry_sdk::{Resource, trace::SdkTracerProvider};
use std::{thread::sleep, time::Duration};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let exporter = SpanExporter::default();
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .build();
    let provider = SdkTracerProvider::builder()
        .with_resource(resource)
        .with_batch_exporter(exporter)
        .build();
    opentelemetry::global::set_tracer_provider(provider.clone());

    step1();

    let resource_2 = Resource::builder()
        .with_service_name("step2_resource")
        .build();
    let provider_2 = SdkTracerProvider::builder()
        .with_resource(resource_2.clone())
        .with_batch_exporter(SpanExporter::default())
        .build();
    step2(&provider_2);
    provider.shutdown()?;
    provider_2.shutdown()?;
    Ok(())
}

fn step1() {
    let tracer = opentelemetry::global::tracer("tracer-in-step1");
    let span = tracer.start("step1");
    let context = Context::current_with_span(span);
    let _guard = context.attach();
    sleep(Duration::from_millis(10));
    println!("Step 1");
    inside_step1();
}

fn inside_step1() {
    opentelemetry::global::tracer("tracer-inside-step1").in_span("inside_step1", |_| {
        sleep(Duration::from_millis(30));
        println!("Inside Step 1");
    });
}

fn step2(trace_provider: &SdkTracerProvider) {
    trace_provider.tracer("tracer-in-step2").in_span("step2", |_| {
        sleep(Duration::from_millis(20));
        println!("Step 2")
    });
}
```
{% endraw %}
</div>
</details>

With the Stdout SpanExporter the Tracer names are listed as:

```
    Instrumentation Scope
		Name         : "tracer-in-step2"
```

We can bring back the 
[opentelemetry_otlp](https://docs.rs/opentelemetry-otlp/latest/opentelemetry_otlp/index.html)
SpanExporter to see how the Tracer name is populated in Jaeger.

![Jaeger showing Tracer name in Process section](/assets/tracer-name.png)

Jaeger lists the Tracer name in each Span's Process section as `otel.library.name`.

# Using a Tracer with the Tracing Crate

The [initial post on tracing]({% post_url 2025-11-09-jaeger-tracing %}) used the
[`tracing`](https://docs.rs/tracing/latest/tracing) crate.

The tracing crate was initialized by passing a Tracer into the
[tracing_opentelemetry](https://docs.rs/tracing-opentelemetry/latest/tracing_opentelemetry/)
crate to create an 
[OpenTelemetryLayer](https://docs.rs/tracing-opentelemetry/latest/tracing_opentelemetry/struct.OpenTelemetryLayer.html).
Then the OpenTelemetryLayer was passed into the 
[tracing_subscriber](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/index.html)'s 
[Registry](https://docs.rs/tracing-subscriber/latest/tracing_subscriber/registry/struct.Registry.html).

> To minimize the scope of this post, the OpenTelemetryLayer and Registry are
going to be glossed over for now.


```rust
    let tracer = provider.tracer("tracer-name");
    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);
    tracing_subscriber::registry().with(telemetry).init();
```

It could be deduced by looking at the initialization that:
- The rust tracing crates uses a Tracer and stores this in some kind of global Registry.
- The Tracer comes from an Opentelemetry TraceProvider

With this relation between the crates understood, it implies that it is possible
to mix and match tracing via the 
[`instrument`](https://docs.rs/tracing/latest/tracing/attr.instrument.html)
macro and explicitly creating Spans from a global TraceProvider. This can be
done by initializing the tracing crates with a Tracer from the same
TraceProvider that is set as the global TraceProvider.

```rust
    let tracer = provider.tracer("tracer-name");
    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);
    tracing_subscriber::registry().with(telemetry).init();
    opentelemetry::global::set_tracer_provider(provider.clone());
```

Below is a script mixing the usages. Running the script will provide similar
stdout Spans that have been shown in this and previous posts on tracing.
The mixing of the two initializations allows one to consume a crate with either
Span style. It also makes it possible to opportunistically migrate a code base
from one Span creation style to another. 

<details>
  <summary>Script using rust tracing and plain Opentelemetry tracing</summary>

<div markdown="1">
{% raw %}
```rust
#!/usr/bin/env -S cargo +nightly -Zscript
---cargo
[dependencies]
opentelemetry = "0.31"
opentelemetry_sdk = "0.31"
opentelemetry-stdout = "0.31"
tracing = "0.1"
tracing-subscriber = "0.3"
tracing-opentelemetry = "0.32"
---

use opentelemetry::{
    Context,
    trace::{TraceContextExt, Tracer, TracerProvider},
};
use opentelemetry_sdk::{Resource, trace::SdkTracerProvider};
use opentelemetry_stdout::SpanExporter;
use std::{thread::sleep, time::Duration};
use tracing::instrument;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let exporter = SpanExporter::default();
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .build();

    let provider = SdkTracerProvider::builder()
        .with_resource(resource)
        .with_batch_exporter(exporter)
        .build();

    let tracer = provider.tracer("tracer-name");
    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);
    tracing_subscriber::registry().with(telemetry).init();
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

#[instrument]
fn inside_step1() {
    sleep(Duration::from_millis(30));
    println!("Inside Step 1");
}

#[instrument]
fn step2() {
        sleep(Duration::from_millis(20));
        println!("Step 2");
}
```

{% endraw %}
</div>
</details>