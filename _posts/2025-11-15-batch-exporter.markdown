---
layout: post
title:  "Using a Batch Exporter"
date:   2025-11-15 18:00:03 -0800
categories: tracing rust
---

In the previous [post]({% post_url 2025-11-10-spans-in-rust %}) we discovered
that using the
[SimpleSpanProcessor](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.SimpleSpanProcessor.html)
resulted in 4-10ms that happens after `inside_step_1` completes.
![Jaeger Step 1](/assets/jaeger-step-1.png)

The simple exporter was used in the example, as it was _simple_ to setup and
didn't require any extra steps to get spans published. However, moving forward I
don't want the extra time to be interpreted as a downside to using tracing in
rust. So we're going to move over to the
[BatchSpanProcessor](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.BatchSpanProcessor.html)

Per the documentation:

> [BatchSpanProcessor] uses a dedicated background thread to manage and export
spans asynchronously

This means that the running task will pass the spans onto this other thread and
the other thread will handle the overhead of sending the spans to Jaeger. 

In order to use a `BatchSpanProcessor` one needs to change how the provider is
built and be sure to call
[shutdown()](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.SdkTracerProvider.html#method.shutdown)
on the provider. 

The documentation for the
[SDKTraceProvider](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.SdkTracerProvider.html)
says
> When the last reference is dropped, the shutdown process will be automatically
triggered to ensure proper cleanup.

I have not found this auto cleanup to be true. If one doesn't explicitly call
`shutdown()`, then no traces seem to get to Jaeger for this simple example. 

Below is the updated `main` using
[with_batch_exporter()](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.TracerProviderBuilder.html#method.with_batch_exporter)
instead of
[with_simple_exporter()](https://docs.rs/opentelemetry_sdk/0.31.0/opentelemetry_sdk/trace/struct.TracerProviderBuilder.html#method.with_simple_exporter). Notice that the `provider` now needs to be `cloned()` into the
`set_trace_provider()`. This is so we can keep it around to `shutdown()` at the
end.

```rust
fn main() -> Result<(), Box<dyn std::error::Error>> {
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
    opentelemetry::global::set_tracer_provider(provider.clone());

    step1();
    step2();
    Ok(provider.shutdown()?)
}
```

Running this updated version should result in a trace similar to:
![No trailing span export time](/assets/batch-export-time.png)

We now see almost no time in `step1` after `inside_step1` finishes.  This is
because the span is sent to the batch processing thread, which is significantly
faster than sending directly to Jaeger on span completion.

Using the batch processor should now provide the minimal overhead for tracing
one would hope to get in a real world application.
