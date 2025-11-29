---
layout: post
title:  "Opentelemetry Resource"
date:   2025-11-28 18:00:03 -0800
categories: tracing rust
---

The previous post,
[Opentelemetry SpanExporter]({% post_url 2025-11-23-otel-span-exporter %}),
started digging into some of the initialization of OpenTelemetry in rust. This
post is going to cover the `resource` portion of the initialization.

```rust
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .build();
```

A
[Resource](https://docs.rs/opentelemetry_sdk/latest/opentelemetry_sdk/struct.Resource.html)
is created using a
[ResourceBuilder](https://docs.rs/opentelemetry_sdk/latest/opentelemetry_sdk/resource/struct.ResourceBuilder.html).
The only thing done with this builder is add a service name, `tracing-example`.

Looking at the stdout exporter output from the previous post, this service name
is showing up under the `Resource` portion of the output as `service.name`.

```
Resource
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  service.name=String(Static("tracing-example"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
	 ->  telemetry.sdk.language=String(Static("rust"))
```

From the earlier post, [Using Jaeger to Capture Traces]({% post_url
2025-11-09-jaeger-tracing %}), the `tracing-example` name also appeared in the
Jaeger UI under the `Services` section.

![Jaeger Example Service](/assets/jaeger-capture.png)

# Resource Attributes

This post has been throwing around `Resource`, but not really defining what it
is. The OpenTelemetry documentation on
[Resources](https://opentelemetry.io/docs/concepts/resources/) starts out with:

> A resource represents the entity producing telemetry as resource attributes. 

This throws out another term that hasn't been defined in these posts yet,
`attribute`. Up above I mentioned how the `tracing-example` was showing up under
`service.name`. `service.name` is an attribute, as are:

- telemetry.sdk.version
- telemetry.sdk.name
- telemetry.sdk.language

These are resource attributes. Attributes are extra pieces of metadata that can
be provided with the trace data.  Often times trace data will be sent from
multiple applications or services to a common trace collector like Jaeger. The
attributes enable filtering down trace information based on `service.name` or
perhaps the programming language, `telemetry.sdk.language`.

Other attributes can be added to the resource:

```rust
    use opentelemetry::KeyValue;
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .with_attribute(KeyValue::new("something", "happy"))
        .with_attribute(KeyValue::new("else", "joy"))
        .build();
```

Running the script with the above modifications will result in the new
attributes present in the the `Resource` section of the output.

```
Resource
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
	 ->  service.name=String(Static("tracing-example"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  else=String(Static("joy"))
	 ->  something=String(Static("happy"))
```

Omitting the `with_service_name()` call will result in the implementation
providing a default of `unknown_service`.

```rust
    let resource = Resource::builder()
        .with_service_name("tracing-example")
        .with_attribute(KeyValue::new("something", "happy"))
        .with_attribute(KeyValue::new("else", "joy"))
        .build();
```
```
Resource
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  service.name=String(Static("unknown_service"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
```

# Resource

The Opentelementry documentation on
[Resources](https://opentelemetry.io/docs/concepts/resources/) says

> A resource is added to the TracerProvider or MetricProvider when they are
created during initialization. This association cannot be changed later. After a
resource is added, all spans and metrics produced from a Tracer or Meter from
the provider will have the resource associated with them.

This means there can only be one resource per TraceProvider. It is possible to
create multiple TraceProviders, each one will need its own resource.

<details>
  <summary>Full script using multiple TraceProviders</summary>

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
<br/>

Running the full script above the result will be similar to:
```
Step 1
Inside Step 1
Step 2
Spans
Resource
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  service.name=String(Static("tracing-example"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
Span #0
	Instrumentation Scope
		Name         : "tracer-name"

	Name         : inside_step1
	TraceId      : 94722b3303dac0ac71ea281c397c189d
	SpanId       : 7cef86805b2f7ee1
	TraceFlags   : TraceFlags(1)
	ParentSpanId : f5c413a87dcc61db
	Kind         : Internal
	Start time   : 2025-11-29 03:45:46.829062
	End time     : 2025-11-29 03:45:46.864145
	Status       : Unset
Span #1
	Instrumentation Scope
		Name         : "tracer-name"

	Name         : step1
	TraceId      : 94722b3303dac0ac71ea281c397c189d
	SpanId       : f5c413a87dcc61db
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-11-29 03:45:46.816518
	End time     : 2025-11-29 03:45:46.864161
	Status       : Unset
Spans
Resource
	 ->  service.name=String(Static("step2_resource"))
	 ->  telemetry.sdk.version=String(Static("0.31.0"))
	 ->  telemetry.sdk.language=String(Static("rust"))
	 ->  telemetry.sdk.name=String(Static("opentelemetry"))
Span #0
	Instrumentation Scope
		Name         : "tracer-in-step2"

	Name         : step2
	TraceId      : 8828513740e2356b714ed0c5ed871451
	SpanId       : c1c30d2f2842a055
	TraceFlags   : TraceFlags(1)
	ParentSpanId : None (root span)
	Kind         : Internal
	Start time   : 2025-11-29 03:45:46.864707
	End time     : 2025-11-29 03:45:46.889755
	Status       : Unset

```

Now there are two `Resource` sections. One with service name `tracing-example`
and a second with `step2_resource`. This is because the modified script above is
creating and passing a different TraceProvider to `step2()`

```rust
    let resource_2 = Resource::builder()
        .with_service_name("step2_resource")
        .build();
    let provider_2 = SdkTracerProvider::builder()
        .with_resource(resource_2.clone())
        .with_batch_exporter(SpanExporter::default())
        .build();
    step2(&provider_2);
```

# Summary

Resources hold the service or application specific attributes. The
`service.name` attribute is a common attribute most tracing tools understand.
It's good to specify this to differentiate between the different services that
are being collected. There isn't anything restricting an application from having
multiple resources, via multiple trace providers, but it's probably not done too
often.