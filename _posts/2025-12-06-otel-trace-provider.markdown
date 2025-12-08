---
layout: post
title:  "Opentelemetry Trace Provider"
date:   2025-12-06 17:00:03 -0800
categories: tracing rust
---

The last part of the initializing OpenTelemetry in a rust application is the
[TraceProvider](https://docs.rs/opentelemetry/latest/opentelemetry/trace/trait.TracerProvider.html).
The rust TraceProvider is a trait which implements the OpenTelemetry definition
of a
[TraceProvider](https://opentelemetry.io/docs/specs/otel/trace/api/#tracerprovider).

The
[SdkTraceProvider](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.SdkTracerProvider.html)
implementation from the
[opentelemetry_sdk](https://docs.rs/opentelemetry_sdk/latest/opentelemetry_sdk/)
crate was used to create the TraceProvider:

```rust
    let provider = SdkTracerProvider::builder()
        .with_resource(resource)
        .with_batch_exporter(exporter)
        .build();
```

The OpenTelemetry documentation says that a TraceProvider is a stateful object
which holds configuration. The documentation also says that a TraceProvider
provides access to a
[Tracer](https://opentelemetry.io/docs/specs/otel/trace/api/#tracer), and a
Tracer creates spans. The previous posts showed Spans being crated from a Tracer:

```rust
    let tracer = opentelemetry::global::tracer("tracer-name");
    let span = tracer.start("step1");
```

The above snippet looks like it's grabbing a global Tracer. However reading the
docs of the
[tracer()](https://docs.rs/opentelemetry/latest/opentelemetry/global/fn.tracer.html)
function.

> This is a more convenient way of expressing
`global::tracer_provider().tracer(name)`.

The code could have been written as:

```rust
    let provider = opentelemetry::global::trace_provider();
    let tracer = provider.tracer("tracer-name");
    let span = tracer.start("step1");
```

Hopefully it is a bit clearer that the code is first getting access to the
global TraceProvider. Then from the global TraceProvider getting access to a
Tracer, in order to create the desired Span.

Piecing together the previous posts and the TraceProvider. The application will
create a TraceProvider, utilizing an application specific Resource and Exporter.
Code that is recording trace data doesn't concern itself with the Resource or
Exporter behavior and only focuses on getting a Tracer from the TraceProvider,
so that it can generate spans. 

# Using the TraceProvider
The previous posts showed two ways that the TraceProvider is accessed in code:

1. By setting a global TraceProvider
2. By passing the trace provider around explicitly

## The Global TraceProvider

Common practice when using the Opentelemtry crates directly, i.e. not using the rust
[tracing](https://docs.rs/tracing/latest/tracing/) crate, is to set the global
trace provider:

```rust
    opentelemetry::global::set_tracer_provider(provider);
```

Then in the functions that are recording trace data, accesses the global
TraceProvider, to get a Tracer:

```rust
    let tracer = opentelemetry::global::tracer("tracer-name");
```

This works fairly well for most applications. There is the common code smell of
using global instances. However, tracing is part of monitoring and monitoring is
considered a 
[cross cutting concern](https://en.wikipedia.org/wiki/Cross-cutting_concern).
Often cross cutting concerns get a bit of a pass on the use of global instances.

Something to be aware of: The global TraceProvider defaults to the
[NoopTraceProvider](https://docs.rs/opentelemetry/latest/opentelemetry/trace/noop/struct.NoopTracerProvider.html).
When asked for a Tracer the NoopTraceProvider will return a
[NoopTracer](https://docs.rs/opentelemetry/latest/opentelemetry/trace/noop/struct.NoopTracer.html).
The NoopTracer will produce
[NoopSpan](https://docs.rs/opentelemetry/latest/opentelemetry/trace/noop/struct.NoopSpan.html)s. 

These Noop versions allow the code that is recording traces to not need specific
logic to work with applications that haven't configured tracing. The Noops are
meant to be very lightweight with almost no runtime overhead. 

## Explicit Trace Provider

It is possible to pass the TraceProvider to a function that will be capturing
span data. This was shown in the
[Opentelemetry Resource]({% post_url 2025-11-28-otel-resource %}) post.
`provider_2` was passed as an argument to the function that was recording trace data. 

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

Then the Tracer and Span were created from the passed in TraceProvider.

```rust
fn step2(trace_provider: &SdkTracerProvider) {
    trace_provider.tracer("tracer-in-step2").in_span("step2", |_| {
        sleep(Duration::from_millis(20));
        println!("Step 2")
    });
}
```