הפרויקט מוגן תחת רישיון  וחל איסור להשתמש למטרות מסחריות. כול שהן.

# APK Patcher

An open-source, modular platform that automatically patches Android apps and publishes them via GitHub Releases.

**Live site:** [https://cfopuser.github.io/bit-updates/](https://cfopuser.github.io/bit-updates/)

## How It Works

```
APKMirror → Download → Decompile → Patch → Repack → Sign → Release
```

A GitHub Actions workflow runs daily, checking each registered app for updates. When a new version is found, it's automatically downloaded, patched, signed, and published as a GitHub Release.

## Adding a New App

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for a step-by-step guide.

## License

this project is protected under gpl3 license. any use of this project for commercial purposes is strictly prohibited.
more details in [LICENSE](LICENSE).
