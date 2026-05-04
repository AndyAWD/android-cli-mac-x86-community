# android-cli-mac-x86-community

**This is an unofficial community port. Not affiliated with or endorsed by Google LLC. Please do not report issues to Google.**

[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/AndyAWD/android-cli-mac-x86-community/releases/tag/v0.1.0)
[![English](https://img.shields.io/badge/lang-English-blue?style=for-the-badge)](./README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-lightgrey?style=for-the-badge)](./README.zh-TW.md)

A command-line tool that brings an Android-CLI-like experience to **Intel macOS (x86_64)**, where Google does not ship an official binary. Internally it wraps `adb`, `sdkmanager`, `avdmanager`, and the Android emulator — all of which are officially supported on Intel macOS.

While optimized for Intel Mac, this tool also features **experimental support for Windows and Linux**, providing a consistent Android CLI experience across platforms.

## Why this exists

Google's [Android CLI](https://developer.android.com/tools/agents/android-cli/archive) ships only `darwin_arm64` for macOS, leaving Intel Mac users without an official option. This project provides a similar UX on top of the existing Android SDK command-line tools that *are* available for Intel macOS.

It is **not** a reverse-engineered copy of Google's binary. It is a separate Python wrapper around publicly documented tools.

## Installation

Requires Python 3.11+ on Intel macOS, plus the Android SDK command-line tools.

### 1. Setup Environment

```bash
brew install openjdk@17 gradle pipx
brew install --cask android-commandlinetools

mkdir -p ~/Library/Android/sdk/cmdline-tools
cp -R /usr/local/share/android-commandlinetools/cmdline-tools/latest ~/Library/Android/sdk/cmdline-tools/latest

export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

yes | sdkmanager --licenses
sdkmanager "platform-tools" "emulator"
```
*(Note: Add the `export` lines to your `~/.zshrc` or `~/.bash_profile`)*

### 2. Install CLI

```bash
pipx ensurepath
pipx install git+https://github.com/AndyAWD/android-cli-mac-x86-community.git
```
*(Note: You may need to restart your terminal after `pipx ensurepath`)*

**To upgrade later:** run `android-cli-mac-x86-community update`

### Why each prerequisite

- **`pipx`** — installs Python CLI tools into isolated virtualenvs and exposes
  them on `PATH`. Recommended over plain `pip install` because Homebrew's
  Python is `EXTERNALLY-MANAGED` (PEP 668) and global `pip install` is
  refused. `pipx` also pulls a compatible Python automatically, so you don't
  need to pin `python@3.11` yourself.
- **`gradle`** — `create` runs `gradle wrapper` after scaffolding so the new
  project gets `gradlew` / `gradlew.bat` (defaults to Gradle 8.7; override with
  `--gradle-version`, or skip entirely with `--no-wrapper`). Without it, the wrapper step is
  skipped and you can't `./gradlew assembleDebug` until you install Gradle
  yourself.
- **`cp -R` instead of `ln -s`** — see comment above; symlinking confuses
  `sdkmanager`'s SDK-root detection.
- **`ANDROID_HOME`** — Required by `assembleDebug` (the AGP build) even after
  this CLI finds the SDK on its own. Without it, your generated Gradle project
  will fail to build.

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
| `sdk list` | List installed and available SDK packages (use `--all` for full repo) |
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
| `screen resolve` | Locate UI elements visually (JSON output) |
| `layout` | Dump the layout tree |
| `create` | Scaffold a new Android project (use `--list-templates` to see options) |
| `describe` | Output JSON describing a project |
| `docs search/fetch` | Search/fetch Android documentation (offline KB) |
| `skills add/remove/list/find` | Manage skills (fetched live from `github.com/android/skills`) |
| `update` | Self-update from GitHub (use `--check` to check only) |

Run `android-cli-mac-x86-community --help` or `android-cli-mac-x86-community help <command>` for full options.

## Skills

Skills come from the public [`github.com/android/skills`](https://github.com/android/skills) repository (Apache-2.0). This project fetches them live via the GitHub Contents API and caches them locally under `~/.android-cli-mac-x86-community/skills/`. We do **not** redistribute skill content; the upstream repo is the source of truth.

Anonymous GitHub API requests are limited to 60/hour. If you hit the limit, set `GITHUB_TOKEN` in your environment.

## Trademark notice

"Android" is a trademark of Google LLC, used in this project's name and documentation under nominative fair use to indicate compatibility with Google's Android CLI. This project is not affiliated with, endorsed by, or sponsored by Google LLC.

## License

MIT — see [LICENSE](./LICENSE).
