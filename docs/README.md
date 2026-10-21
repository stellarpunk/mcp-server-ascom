# Documentation

## Quick Links

### Getting Started
- **[Installation & Setup](GETTING_STARTED.md)** - Get up and running
- **[API Reference](API.md)** - All available tools
- **[SDK Guide](SDK_GUIDE.md)** - Type-safe Python SDK (v0.5.0+)
- **[Troubleshooting](troubleshooting.md)** - Fix common issues

### Integration Guides  
- **[Seestar S50](seestar_integration.md)** - Seestar-specific guide
- **[MCP Setup](MCP_INTEGRATION.md)** - Claude Code configuration
- **[Simulator](simulator_setup.md)** - Test without hardware

### Technical Docs
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Development](development.md)** - Contributing
- **[Testing](E2E_TESTING_GUIDE.md)** - Test framework

## Directory Structure

```
docs/
├── User Guides
│   ├── GETTING_STARTED.md
│   ├── API.md
│   └── troubleshooting.md
├── Integration
│   ├── seestar_integration.md
│   ├── MCP_INTEGRATION.md
│   └── simulator_setup.md
├── Technical
│   ├── ARCHITECTURE.md
│   ├── development.md
│   └── E2E_TESTING_GUIDE.md
└── Reference
    ├── EXECUTIVE_SUMMARY.md
    └── MIGRATION_v0.3.0.md
```

## Key Concepts

**ASCOM** - Astronomy Common Object Model, standard for device control  
**MCP** - Model Context Protocol, enables AI control  
**Alpaca** - HTTP/REST API for ASCOM devices  
**FastMCP** - Framework for building MCP servers

## Contributing

See [development.md](development.md) for guidelines.