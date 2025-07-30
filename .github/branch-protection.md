# Branch Protection Settings

Configure these settings in GitHub repository settings → Branches → Add rule for `main`:

## Required Settings

### Branch name pattern
- `main`

### Protect matching branches

#### ✅ Require a pull request before merging
- ✅ Require approvals: 1
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from CODEOWNERS (if configured)

#### ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- Required status checks:
  - `critical-tests`
  - `test (ubuntu-latest, 3.12)`
  - `build`

#### ✅ Require conversation resolution before merging

#### ✅ Require signed commits (optional but recommended)

#### ✅ Include administrators
- Even admins must follow the rules

#### ✅ Restrict who can push to matching branches
- Add specific users or teams who can push

## Recommended Additional Settings

### Auto-merge
Enable auto-merge for Dependabot PRs after tests pass

### CODEOWNERS file
Create `.github/CODEOWNERS`:
```
# Default owners for everything
* @stellarpunk

# MCP protocol changes need extra review
src/ascom_mcp/server.py @stellarpunk/mcp-experts
tests/integration/test_claude_desktop_integration.py @stellarpunk/mcp-experts
```

## Release Process

With these protections:
1. All changes go through PR
2. Tests must pass
3. Can't accidentally break main
4. Tags trigger automatic release pipeline