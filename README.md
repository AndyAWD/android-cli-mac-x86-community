[![English](https://img.shields.io/badge/lang-English-blue?style=for-the-badge)](./README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-lightgrey?style=for-the-badge)](./README.zh-TW.md)

# android-cli-mac-x86-community

**This is an unofficial community port. Not affiliated with or endorsed by Google LLC. Please do not report issues to Google.**

A command-line tool that brings an Android-CLI-like experience to **Intel macOS (x86_64)**, where Google does not ship an official binary. Internally it wraps `adb`, `sdkmanager`, `avdmanager`, and the Android emulator — all of which are officially supported on Intel macOS.

## Why this exists

Google's [Android CLI](https://developer.android.com/tools/agents/android-cli/archive) ships only `darwin_arm64` for macOS, leaving Intel Mac users without an official option. This project provides a similar UX on top of the existing Android SDK command-line tools that *are* available for Intel macOS.

It is **not** a reverse-engineered copy of Google's binary. It is a separate Python wrapper around publicly documented tools.

## Installation

Requires Python 3.11+ on Intel macOS, plus the Android SDK command-line tools.

```bash
# 1. Prerequisites (one-time)
brew install openjdk@17 python@3.11
# Then install Android command-line tools per:
# https://developer.android.com/studio#command-line-tools-only

# 2. Install this CLI from GitHub
pip install git+https://github.com/AndyAWD/android-cli-mac-x86-community.git

# 3. Verify
android-cli-mac-x86-community info
```

## Quick start

```bash
android-cli-mac-x86-community sdk list
android-cli-mac-x86-community emulator create --name pixel7 --image "system-images;android-34;google_apis;x86_64"
android-cli-mac-x86-community emulator start --name pixel7
android-cli-mac-x86-community run --apks app-debug.apk
android-cli-mac-x86-community screen capture > out.png
```

## Command reference

| Command | What it does |
|---|---|
| `info [<field>]` | Print SDK location and environment info |
| `init` | Initialize local config and skills directory |
| `sdk list` | List installed and available SDK packages |
| `sdk install <pkg>` | Install an SDK package |
| `sdk update` | Update one or all packages |
| `sdk remove <pkg>` | Remove a package |
| `emulator create` | Create a virtual device |
| `emulator start` | Launch a virtual device |
| `emulator stop` | Stop a virtual device |
| `emulator list` | List virtual devices |
| `emulator remove` | Delete a virtual device |
| `run --apks <files>` | Deploy and launch an APK |
| `screen capture` | Capture device screen as PNG |
| `screen resolve` | Locate UI elements visually |
| `layout` | Dump the layout tree |
| `create` | Scaffold a new Android project |
| `describe` | Output JSON describing a project |
| `docs search/fetch` | Search/fetch Android documentation |
| `skills add/remove/list/find` | Manage skills (fetched live from `github.com/android/skills`) |
| `update` | Self-update |

Run `android-cli-mac-x86-community --help` or `android-cli-mac-x86-community help <command>` for full options.

## Skills

Skills come from the public [`github.com/android/skills`](https://github.com/android/skills) repository (Apache-2.0). This project fetches them live via the GitHub Contents API and caches them locally under `~/.android-cli-mac-x86-community/skills/`. We do **not** redistribute skill content; the upstream repo is the source of truth.

Anonymous GitHub API requests are limited to 60/hour. If you hit the limit, set `GITHUB_TOKEN` in your environment.

## Trademark notice

"Android" is a trademark of Google LLC, used in this project's name and documentation under nominative fair use to indicate compatibility with Google's Android CLI. This project is not affiliated with, endorsed by, or sponsored by Google LLC.

## License

MIT — see [LICENSE](./LICENSE).
