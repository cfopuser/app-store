# APK Patcher

An open-source, modular platform that automatically patches Android apps and publishes them via GitHub Releases.

**Live site:** [https://cfopuser.github.io/bit-updates/](https://cfopuser.github.io/bit-updates/)

## How It Works

```
APKMirror → Download → Decompile → Patch → Repack → Sign → Release
```

A GitHub Actions workflow runs daily, checking each registered app for updates. When a new version is found, it's automatically downloaded, patched, signed, and published as a GitHub Release.

## Supported Apps

| App | Package | Status |
|-----|---------|--------|
| Bit | `com.bnhp.payments.paymentsapp` | ✅ Active |

## Adding a New App

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for a step-by-step guide.

**Quick version:** Create a folder under `apps/` with an `app.json` (metadata) and `patch.py` (patch logic), then open a PR.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# List registered apps
python run.py --list

# Process a specific app
python run.py --app bit

# Download only
python run.py --app bit --step download
```

## Project Structure

```
apps/           ← One subfolder per supported app
  bit/          ← Example app
    app.json    ← App metadata & config
    patch.py    ← Patch logic
core/           ← Shared framework
  downloader.py ← Generic APKMirror downloader
  patcher.py    ← Dynamic patch loader
  utils.py      ← Shared helpers
run.py          ← CLI orchestrator
apkmirror.py    ← APKMirror scraper
index.html      ← Landing page (GitHub Pages)
```

## License

See [LICENSE](LICENSE).
