# Contributing to ASCOM MCP Server

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mcp-server-ascom.git
   cd mcp-server-ascom
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

4. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Process

### 1. Create a branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make changes
- Write tests first (TDD)
- Ensure all tests pass
- Add type hints
- Update documentation

### 3. Run quality checks
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest -v
```

### 4. Submit pull request
- Push to your fork
- Create PR against `main`
- Fill out PR template
- Wait for review

## Code Standards

### Style
- Black formatting (88 chars)
- Google-style docstrings
- Type hints required

### Testing
- Minimum 80% coverage
- Unit tests for all components
- Integration tests for workflows

### Commits
- Clear, descriptive messages
- Reference issues: `Fix #123`
- Atomic commits

## Testing

### Test Framework
We use an extensible testing framework with base classes:

```python
from tests.base import BaseToolTest
from tests.fixtures import create_mock_device

class TestYourDevice(BaseToolTest):
    tool_class = YourDeviceTools
    device_type = "YourDevice"
```

See `tests/templates/` for complete examples.

### Without Physical Devices
Use the device factory:
```python
mock_telescope = create_telescope_mock()
mock_focuser = create_focuser_mock(Position=25000)
```

### With Physical Devices
1. **Never** commit device IPs/credentials
2. Use environment variables
3. Mark tests as integration:
   ```python
   @pytest.mark.integration
   def test_real_device():
       pass
   ```

## Adding Device Support

1. Check existing issues first
2. Use device support template
3. Implement in stages:
   - Basic connection
   - Core functions
   - Advanced features

## Documentation

- Update README for user-facing changes
- Add docstrings to all functions
- Include examples for new features

## Questions?

- Check existing issues
- Join discussions
- Ask in pull request

## License

By contributing, you agree that your contributions will be licensed under the MIT License.