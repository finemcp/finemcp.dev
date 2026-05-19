---
title: "Introducing FineMCP: Production-Ready MCP Servers in Go"
description: "Why we built FineMCP, what makes it different from other MCP libraries, and where we're taking it."
date: 2026-05-12
tags: ["announcement", "open-source"]
---

The Model Context Protocol has changed how AI assistants talk to the outside world. Since Anthropic open-sourced the spec in late 2024, the ecosystem has exploded — clients, servers, adapters, wrappers. Most of the early tooling was Python. Some TypeScript. Very little Go.

We needed Go. Not because Go is fashionable, but because the systems we were connecting to — internal APIs, gRPC services, streaming pipelines — were already written in Go. Reaching for a Python subprocess to bridge them felt wrong.

So we looked at what existed. There were thin wrappers: expose a function, get an MCP tool. Simple, quick, and fine for demos. But production is different.

## What production actually needs

When you deploy an MCP server that a hundred AI agents are hitting simultaneously, you start asking questions that thin wrappers don't answer:

- How do I rate-limit per client?
- How do I add auth without rewriting every handler?
- How do I trace a slow tool call end-to-end in Jaeger?
- How do I gracefully degrade when an upstream is down?
- How do I test my tool logic without standing up the full MCP stack?

These aren't exotic requirements. They're the same problems every backend team has solved for HTTP APIs — with middleware. MCP servers should have the same options.

## FineMCP's approach

FineMCP is built around a middleware-first architecture. Every tool call, resource read, and prompt render passes through a configurable chain of handlers. You compose behavior the same way you compose Go functions: layer in what you need, leave out what you don't.

```go
srv := server.New("my-server", "1.0.0",
    server.WithMiddleware(
        middleware.Recover(),
        middleware.Logger(logger),
        middleware.RateLimit(100, time.Minute),
        middleware.Auth(myAuthFn),
    ),
)
```

The rest — tools, resources, prompts, streaming, transports — is built on top of that foundation.

## What's in the box

**16 production middleware** including rate limiting, circuit breaking, retry with backoff, distributed tracing (OpenTelemetry), structured logging, RBAC, request deduplication, and more.

**5 transport protocols** — stdio, HTTP/SSE, HTTP Streaming, WebSocket, and in-process — so you can embed an MCP server inside an existing Go binary, expose it over the web, or pipe it through a CLI.

**Full MCP spec coverage**: tools, resources, resource templates, prompts, sampling, elicitation, roots, progress notifications, cancellation, and completion. If it's in the 2025-11-25 spec, FineMCP implements it.

**A testing package** that lets you call tools and inspect results without touching the network. Write real unit tests for your MCP handlers.

## Where we are

FineMCP is in public beta. The core API is stable enough to build on. We're shipping real improvements weekly based on what we learn from early adopters.

If you're building anything with MCP and Go, we'd love to have you try it and tell us what's broken.

→ [Get started](/docs/getting-started/)  
→ [Browse tutorials](/tutorials/)  
→ [Star us on GitHub](https://github.com/finemcp/finemcp)

