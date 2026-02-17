# Contributing a New App

Want to add a new app to the patching platform? Here's how.

## Prerequisites

- Python 3.10+
- Basic understanding of smali/APK structure
- The app's Android package name (e.g., `com.example.myapp`)

## Step-by-Step Guide

### 1. Fork & Clone

```bash
git clone https://github.com/cfopuser/app-store.git
cd app-store
pip install -r requirements.txt
```

### 2. Create the App Directory

```bash
mkdir -p apps/your-app
```

### 3. Create `app.json`

Create `apps/your-app/app.json` with your app's metadata:

```json
{
  "id": "your-app",
  "name": "Your App Name",
  "package_name": "com.example.yourapp",
  "description": "Short description of the app and what the patch does",
  "icon_url": "https://example.com/icon.png",
  "source": "apkmirror",
  "maintainer": "your-github-username",
  "version_file": "apps/your-app/version.txt",
  "status_file": "apps/your-app/status.json"
}
```

### 4. Create `patch.py`

Create `apps/your-app/patch.py` with a `patch()` function:

```python
import os
import re

def patch(decompiled_dir: str) -> bool:
    """
    Apply your patch to the decompiled APK.
    
    Args:
        decompiled_dir: Path to the apktool-decompiled directory.
    
    Returns:
        True if patch applied successfully, False otherwise.
    """
    # Walk through the smali files and apply your changes
    target = "YourTargetFile.smali"
    
    for root, dirs, files in os.walk(decompiled_dir):
        if target in files:
            file_path = os.path.join(root, target)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply your patch here
            # new_content = content.replace(old, new)
            
            # with open(file_path, 'w', encoding='utf-8') as f:
            #     f.write(new_content)
            
            return True
    
    return False
```

### 5. Initialize Version Tracking

```bash
echo "0.0.0" > apps/your-app/version.txt
echo '{"success": true, "failed_version": "", "error_message": "", "updated_at": ""}' > apps/your-app/status.json
```

### 6. Test Locally

```bash
# Verify your app is discovered
python run.py --list

# Test the download step (requires internet)
python run.py --app your-app --step download
```

### 7. Open a Pull Request

Push your changes and open a PR. The maintainers will review and test your patch.

## Guidelines

- **One app per folder** — each app is self-contained under `apps/`
- **Return bool** — your `patch()` function must return `True` on success, `False` on failure
- **Print progress** — use `print()` statements with `[+]`, `[-]`, `[*]` prefixes for consistency
- **Don't `sys.exit()`** — The orchestrator handles exit codes
- **Test your regex** — smali patterns can vary between versions; make them flexible
