# API Examples

Complete, accurate examples of ASCOM MCP Server responses.

## Discovery

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "discover_ascom_devices",
    "arguments": {"timeout": 5.0}
  }
}
```

**Response** (no devices):
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"success\": true,\n  \"devices\": [],\n  \"discovery_time_ms\": 5003\n}"
    },
    {
      "type": "text", 
      "text": "No devices found"
    }
  ]
}
```

**Response** (with devices):
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"success\": true,\n  \"devices\": [\n    {\n      \"id\": \"telescope_0\",\n      \"name\": \"Seestar S50\",\n      \"type\": \"Telescope\",\n      \"host\": \"192.168.1.100\",\n      \"port\": 5555\n    }\n  ],\n  \"discovery_time_ms\": 2156\n}"
    },
    {
      "type": "text",
      "text": "Found 1 device: Seestar S50"
    }
  ]
}
```

## Connect

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "telescope_connect",
    "arguments": {"device_id": "telescope_0"}
  }
}
```

**Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"success\": true,\n  \"device_id\": \"telescope_0\",\n  \"device_name\": \"Seestar S50\",\n  \"connected\": true\n}"
    },
    {
      "type": "text",
      "text": "Connected to Seestar S50"
    }
  ]
}
```

## Goto Object

**Request**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "telescope_goto_object",
    "arguments": {
      "device_id": "telescope_0",
      "object_name": "M31"
    }
  }
}
```

**Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"success\": true,\n  \"object_name\": \"M31\",\n  \"resolved_name\": \"Andromeda Galaxy\",\n  \"ra\": 0.712,\n  \"dec\": 41.269,\n  \"slewing\": true\n}"
    },
    {
      "type": "text",
      "text": "Slewing to M31"
    }
  ]
}
```

## Error Handling

**Request** (device not found):
```json
{
  "method": "tools/call",
  "params": {
    "name": "telescope_connect",
    "arguments": {"device_id": "invalid_id"}
  }
}
```

**Response**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"error\": {\n    \"type\": \"device_not_found\",\n    \"message\": \"Device invalid_id not found. Run discovery first.\"\n  }\n}"
    },
    {
      "type": "text",
      "text": "Error: Device invalid_id not found. Run discovery first."
    }
  ],
  "isError": true
}
```

## Notes

1. All responses include two content blocks:
   - JSON data (machine-readable)
   - Text summary (human-readable)

2. The `type` field is always `"text"` for MCP compatibility

3. Error responses set `isError: true` in CallToolResult

4. Success responses always include `"success": true` in JSON

5. Timestamps use ISO 8601 format when included