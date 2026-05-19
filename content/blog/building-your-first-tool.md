---
title: "FineMCP Public Beta is Open"
description: "We're opening FineMCP to the public for beta testing. Here's what's ready, what's rough, and how you can help shape it."
date: 2026-05-16
tags: ["beta", "announcement", "release"]
---

Today we're opening FineMCP to public beta.

If you're building Go services that need to expose AI-friendly interfaces — or if you're integrating MCP into an existing backend — this is the right time to kick the tires and give us feedback.

## What beta means

The API is stable for the core primitives: `server.New`, `server.AddTool`, `server.AddResource`, `server.AddPrompt`, and the middleware chain. We will not break these without a deprecation cycle.

Everything marked `Experimental` in the docs may change. If you use it, pin your version and watch the changelog.

## What's ready today

### Tools
Define typed tool handlers with struct-based input validation. FineMCP derives JSON Schema from Go struct tags automatically — no manual schema writing.

```go
type SearchInput struct {
    Query  string `json:"query"  jsonschema:"required,description=Search query"`
    Limit  int    `json:"limit"  jsonschema:"default=10,minimum=1,maximum=100"`
}

server.AddTool(mcp.Tool{
    Name:        "search",
    Description: "Search documents by keyword",
}, func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
    var in SearchInput
    req.BindArguments(&in)
    results := db.Search(ctx, in.Query, in.Limit)
    return mcp.NewToolResultText(results.Format()), nil
})
```

### Resources & Templates
Expose dynamic data as MCP resources. Use URI templates to let clients browse parameterised resource spaces — think `/users/{id}/profile` or `/repos/{owner}/{repo}/issues`.

### Streaming
Long-running tools can stream partial results back as they become available. No polling, no custom protocols — just send tokens as you produce them.

### 16 middleware, out of the box

| Category | Middleware |
|---|---|
| Reliability | `Recover`, `Timeout`, `Retry`, `CircuitBreaker` |
| Security | `Auth`, `RBAC`, `IPAllowlist` |
| Observability | `Logger`, `Metrics`, `Tracing` (OpenTelemetry) |
| Control | `RateLimit`, `Concurrency`, `Cache`, `Dedup` |
| DX | `Validator`, `RequestID`, `Audit` |

### 5 transports

- **stdio** — pipe-based, perfect for Claude Desktop and local agents  
- **HTTP/SSE** — standard for cloud deployments  
- **HTTP Streaming** — chunked streaming over plain HTTP  
- **WebSocket** — bidirectional, real-time  
- **In-process** — embed a server inside your binary, no network hop

### Testing

```go
func TestMyTool(t *testing.T) {
    client := testutil.NewInProcessClient(srv)
    result, err := client.CallTool(ctx, "search", map[string]any{
        "query": "golang middleware",
        "limit": 5,
    })
    require.NoError(t, err)
    assert.Contains(t, result.Text(), "middleware")
}
```

No ports, no subprocess, no mocks. Just call the tool.

## What's rough

We're honest about this:

- **Docs coverage is uneven.** The middleware reference is complete. Some advanced topics (gateway mode, plugin system) have stubs.
- **Error messages** could be better in a few middleware edge cases — we're working through them.
- **Windows CI** is passing but less battle-tested than Linux/macOS.

## How to help

The most valuable thing you can do right now is **build something real with it** and tell us where you hit friction.

Open a GitHub issue for bugs. Start a discussion for API questions. If something feels unnecessarily complicated, that's signal worth sharing — we want the happy path to feel obvious.

→ [Read the docs](/docs/)  
→ [Browse the tutorials](/tutorials/)  
→ [Open an issue](https://github.com/finemcp/finemcp/issues)  
→ [Join Slack](https://finemcp.slack.com)

We'll be shipping weekly updates throughout the beta. Thank you for being early.
