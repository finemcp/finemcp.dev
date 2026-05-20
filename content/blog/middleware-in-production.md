---
title: "Middleware Is the Difference Between a Demo and a Production MCP Server"
description: "A practical look at how FineMCP's middleware system works, why it matters, and how to compose it for real workloads."
date: 2026-05-20 14:01:00
tags: ["middleware", "production", "deep-dive"]
---

Every MCP framework lets you write a tool. Not every framework helps you run that tool safely under real traffic.

The gap between "works on my machine" and "handles 500 concurrent AI agents" is almost entirely about cross-cutting concerns: auth, rate limiting, timeouts, retries, circuit breaking, tracing. These aren't business logic. They shouldn't live inside your tool handlers. They should be composable infrastructure you bolt on at the server layer.

That's what FineMCP's middleware system is for.

## How the chain works

Every request — tool call, resource read, prompt render — passes through a handler chain before reaching your code. You configure that chain when you create the server:

```go
srv := server.New("my-api", "1.0.0",
    server.WithMiddleware(
        middleware.Recover(),
        middleware.RequestID(),
        middleware.Logger(slog.Default()),
        middleware.Tracing("my-api"),
        middleware.Auth(validateToken),
        middleware.RateLimit(200, time.Minute),
        middleware.Timeout(30 * time.Second),
        middleware.CircuitBreaker(5, 10*time.Second),
    ),
)
```

Middleware executes in order: `Recover` wraps everything, `RequestID` stamps the context, `Logger` records the call, and so on. Each handler calls `next` to pass control to the next layer, or short-circuits with an error.

This is the same pattern as `net/http` middleware — if you've written a Go HTTP server, it feels immediately familiar.

## What ships in the box

### Reliability

**`Recover`** catches panics in your handlers and converts them to structured errors. Essential for long-running servers.

**`Timeout`** gives you per-request deadlines. If a tool takes longer than the configured duration, the context is cancelled and the client gets a clean timeout error instead of a hung connection.

```go
middleware.Timeout(15 * time.Second)
```

**`Retry`** with exponential backoff. Useful for tools that call upstream services which occasionally fail transiently.

```go
middleware.Retry(3, middleware.ExponentialBackoff(100*time.Millisecond))
```

**`CircuitBreaker`** stops hammering a failing upstream. After N consecutive failures, the circuit opens and subsequent calls fail fast for a cooldown period.

### Security

**`Auth`** accepts any function with the signature `func(ctx context.Context, token string) (claims any, err error)`. Plug in your JWT library, your session store, your API key validator — FineMCP doesn't care which.

```go
middleware.Auth(func(ctx context.Context, token string) (any, error) {
    return myJWT.Validate(token, jwtSecret)
})
```

**`RBAC`** layers role-based access control on top of auth claims. Attach required roles to individual tools:

```go
server.AddTool(mcp.Tool{
    Name:        "delete-user",
    Description: "Delete a user account",
    Annotations: mcp.ToolAnnotations{
        Roles: []string{"admin"},
    },
}, deleteUserHandler)
```

**`IPAllowlist`** restricts access to a set of CIDR blocks. Handy for internal tools that should only be reachable from within your network.

### Observability

**`Logger`** emits a structured log line for every request: method, tool name, latency, status. Accepts any `*slog.Logger`.

**`Metrics`** exports Prometheus counters and histograms for request count, latency distribution, and error rate — segmented by tool and transport.

**`Tracing`** instruments every request with OpenTelemetry spans. If your AI agent passes a traceparent header, FineMCP connects the server-side span to the agent's trace automatically.

### Flow control

**`RateLimit`** supports both global and per-client limiting using a token bucket algorithm.

**`Concurrency`** caps the number of simultaneous in-flight requests. Useful when your tools do expensive work.

**`Cache`** memoizes tool results for a TTL. Turn it on for read-heavy tools whose answers don't change frequently.

**`Dedup`** collapses duplicate in-flight requests for the same tool + arguments into a single execution. The second caller waits for the first result.

## Composing for your use case

You don't use all 16 at once. A typical production composition for a public-facing server might look like:

```go
server.WithMiddleware(
    middleware.Recover(),
    middleware.RequestID(),
    middleware.Logger(logger),
    middleware.Tracing(serviceName),
    middleware.Auth(jwtValidator),
    middleware.RateLimit(100, time.Minute),
    middleware.Timeout(20 * time.Second),
    middleware.Metrics(),
)
```

An internal tool with no auth but aggressive reliability requirements:

```go
server.WithMiddleware(
    middleware.Recover(),
    middleware.Timeout(5 * time.Second),
    middleware.Retry(3, middleware.ExponentialBackoff(50*time.Millisecond)),
    middleware.CircuitBreaker(10, 30*time.Second),
    middleware.Cache(5 * time.Minute),
)
```

## Writing your own

If the built-ins don't cover your use case, implementing a custom middleware is straightforward:

```go
func AuditLog(store AuditStore) server.Middleware {
    return func(next server.HandlerFunc) server.HandlerFunc {
        return func(ctx context.Context, req *mcp.Request) (*mcp.Response, error) {
            start := time.Now()
            resp, err := next(ctx, req)
            store.Record(ctx, AuditEntry{
                Tool:     req.Method,
                Duration: time.Since(start),
                Error:    err,
                UserID:   auth.UserIDFromContext(ctx),
            })
            return resp, err
        }
    }
}
```

Wrap `next`, do work before and/or after, pass the context through. The full middleware interface is one function type — nothing to implement, nothing to register.

## The bottom line

The difference between a quick MCP prototype and a server you'd bet production traffic on is almost entirely in this layer. FineMCP gives you that layer ready to use, with sensible defaults, and with enough flexibility to replace any piece with your own implementation.

If you want to see all of this in action, the [Middleware tutorial](/learn/middleware/) walks through a complete example with tracing and rate limiting running together.
