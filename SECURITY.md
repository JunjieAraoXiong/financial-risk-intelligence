# Security Guidelines for FE-EKG

## Secret Management

### Environment Variables

All sensitive credentials are stored in `.env` file:

```bash
AG_URL=https://qa-agraph.nelumbium.ai/
AG_USER=sadmin
AG_PASS=279H-Dt<>,YU
AG_REPO=feekg_dev
```

### Rules

1. **NEVER commit `.env` to Git**
   - Already included in `.gitignore`
   - Double-check before any commit

2. **NEVER print credentials to console**
   - Use `get_masked_config()` for logging
   - Passwords are masked as `***`

3. **NEVER include credentials in error messages**
   - The `secrets.py` module automatically masks passwords in exceptions

4. **Rotate credentials if leaked**
   - If `.env` is accidentally committed or shared
   - Contact AllegroGraph admin to reset password
   - Update `.env` with new credentials

## Safe Usage Examples

### ✅ CORRECT - Masked logging

```python
from config.secrets import get_masked_config

config = get_masked_config()
print(f"Config: {config}")
# Output: {'ag_user': 'sa***', 'ag_pass': '***', ...}
```

### ❌ INCORRECT - Exposing credentials

```python
import os
print(f"Password: {os.getenv('AG_PASS')}")  # DON'T DO THIS!
```

### ✅ CORRECT - Safe connection

```python
from config.secrets import get_ag_connection

conn = get_ag_connection()  # Credentials handled internally
size = conn.size()
conn.close()
```

## Files to NEVER Commit

The following are automatically excluded by `.gitignore`:

- `.env` - Main credentials file
- `.env.*` - Any environment variants
- `**/secrets/**` - Any secrets directory
- `**/*.pem` - Certificate files
- `logs/*.log` - May contain sensitive data

## Audit Trail

When working with credentials:

1. Check `.gitignore` is present
2. Verify `.env` is NOT tracked by Git:
   ```bash
   git status --ignored
   ```
3. Use `get_masked_config()` in all logs
4. Review code for hardcoded credentials before commits

## Incident Response

If credentials are leaked:

1. **Immediately** rotate AllegroGraph password
2. Update `.env` with new credentials
3. If committed to Git:
   - Remove from Git history: `git filter-branch` or BFG Repo-Cleaner
   - Force push: `git push --force`
   - Notify team to re-clone repository

## Contact

For security concerns, contact the AllegroGraph administrator.
