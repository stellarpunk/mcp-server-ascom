# Modern Features

MCP server using 2025-06-18 protocol. Built right.

## Protocol

Latest spec. Structured outputs. Version negotiation.

```json
{
  "success": true,
  "devices": [...],
  "timestamp": "2025-07-30T15:58:33Z"
}
```

Every response: machine-readable JSON, human-readable fallback.

Supports three protocol versions. Negotiates the best. Falls back gracefully.

## Security

Off by default. Easy adoption matters.

One switch enables OAuth 2.0:
```bash
ASCOM_MCP_OAUTH_ENABLED=true
```

When on: JWT validation. Resource indicators. Security headers. CORS control.

Industry standard. Zero friction.

## Architecture

**Extensible**: Base classes for new device types. Plugin ready.

**Async**: Non-blocking operations. Concurrent discovery.

**Testable**: Mock fixtures. Factory patterns. Full coverage.

## Developer Experience

Start simple:
```python
server = create_server()
```

Type safe. Pydantic validates. mypy passes.

Errors tell you what went wrong—and how to fix it:
```json
{
  "error": {
    "type": "device_not_found",
    "message": "Telescope 'MySeestar' not found",
    "suggestion": "Run discovery first"
  }
}
```

Tests everywhere. Mocks included. Contributions welcome.

## Performance

Async everywhere. No blocking. Concurrent discovery.

Large payloads? We detect them. Stream when ready.

## Community

Base classes for new devices. Factory fixtures. Clear docs.

Extend anything. Register custom tools. Override what you need.

## What's Next

**Soon**: structuredContent field support. Elicitation for user input.

**Future**: Multi-agent coordination. Real-time streams. Federation.

## Example

Old way:
```python
return {"text": "Found 3 devices"}
```

Our way:
```python
return create_structured_content(
    data={
        "success": True,
        "devices": [{
            "id": "telescope_0",
            "name": "Seestar S50",
            "status": "ready"
        }],
        "discovery_time_ms": 2043
    },
    text_fallback="Found 1 device: Seestar S50"
)
```

Machine readable. Human friendly. Future proof.

---

Built for astronomers and AI.