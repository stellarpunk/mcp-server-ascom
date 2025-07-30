# Stellarpunk Organization Setup Checklist

## 1. ✅ Create GitHub Organization
- [ ] Go to https://github.com/organizations/new
- [ ] Organization name: `stellarpunk`
- [ ] Add profile README from `stellarpunk-profile-README.md`
- [ ] Set avatar (maybe a gear + star combo?)

## 2. ✅ Transfer Repository
```bash
# In repo settings → General → Transfer ownership
# New owner: stellarpunk
```

## 3. ✅ Update Repository URLs
Files to update:
- [ ] README.md - Change all GitHub URLs
- [ ] pyproject.toml - Update repository URL
- [ ] CONTRIBUTING.md - Update URLs
- [ ] docs/*.md - Any GitHub references

## 4. ✅ Update PyPI Configuration
In `pyproject.toml`:
```toml
[project.urls]
"Homepage" = "https://github.com/stellarpunk/mcp-server-ascom"
"Bug Tracker" = "https://github.com/stellarpunk/mcp-server-ascom/issues"
"Repository" = "https://github.com/stellarpunk/mcp-server-ascom"
```

## 5. ✅ Build and Publish to PyPI
```bash
# From the mcp-server-ascom directory with venv activated
source .venv/bin/activate

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Upload to PyPI (will prompt for credentials)
python -m twine upload dist/*
```

## 6. ✅ Update Claude Desktop Config
Show users this in README:
```json
{
  "mcpServers": {
    "ascom": {
      "command": "uvx",
      "args": ["mcp-server-ascom"]
    }
  }
}
```

## 7. ✅ Domain Registration (Optional)
Consider registering:
- stellarpunk.io ($30-80/year)
- stellarpunk.dev (Google Registry)

## 8. ✅ Future Stellarpunk Projects
Ideas for the movement:
- `stellarpunk/telescope-api` - RESTful API for telescopes
- `stellarpunk/brass-binary-ui` - Steampunk UI components
- `stellarpunk/aethernet-protocol` - Distributed telescope network
- `stellarpunk/clockwork-scheduler` - Observation scheduling

## The Stellarpunk Manifesto
"In the stellarpunk future, every telescope is both a brass instrument and a neural interface, where steam-powered mounts are guided by machine learning, and copper wires carry starlight to quantum processors."