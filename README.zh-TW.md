[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](https://github.com/AndyAWD/android-cli-mac-x86-community/releases/tag/v0.1.0)
[![English](https://img.shields.io/badge/lang-English-lightgrey?style=for-the-badge)](./README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red?style=for-the-badge)](./README.zh-TW.md)

# android-cli-mac-x86-community

**這是非官方社群移植版，與 Google LLC 沒有任何關係，也未獲其背書。請勿向 Google 回報本工具的問題。**

一個讓 **Intel macOS（x86_64）** 也能用上類似 Android CLI 體驗的指令列工具。Google 沒有為 Intel Mac 發行官方版本，所以這個專案在現有的 Android SDK 工具（`adb`、`sdkmanager`、`avdmanager`、Android 模擬器，這些在 Intel macOS 上都是官方支援的）之上，包了一層相似的 UX。

本工具雖然針對 Intel Mac 優化，但也具備 **Windows 與 Linux 的實驗性支援**，提供跨平台一致的 Android CLI 體驗。

## 為什麼有這個專案

Google 的 [Android CLI](https://developer.android.com/tools/agents/android-cli/archive?hl=zh-tw) 在 macOS 平台只發行 `darwin_arm64`，Intel Mac 使用者沒有官方選項。這個專案利用已經存在於 Intel macOS 上的 Android SDK 命令列工具，提供相似的使用體驗。

它**不是** Google binary 的反向工程版本，而是用 Python 重新寫的薄殼，呼叫公開且有文件記載的底層工具。

## 安裝

需要 Intel macOS 上有 Python 3.11+ 與 Android SDK 命令列工具。

```bash
# 1. 前置（一次性）
brew install openjdk@17 gradle pipx
brew install --cask android-commandlinetools

# 把 cmdline-tools 「複製」（不要 symlink）到標準 SDK 路徑。
# 用 symlink 會被 sdkmanager 解析回 /usr/local/share/android-commandlinetools，
# 它把那當成 SDK 根目錄，會看不到後續安裝的 build-tools / platforms / system-images。
mkdir -p ~/Library/Android/sdk/cmdline-tools
cp -R /usr/local/share/android-commandlinetools/cmdline-tools/latest \
      ~/Library/Android/sdk/cmdline-tools/latest

# 告訴工具鏈 SDK 在哪（建議寫進 shell rc）。
export ANDROID_HOME="$HOME/Library/Android/sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

# 2. 透過 pipx 從 GitHub 安裝本工具
pipx ensurepath  # 一次性；把 ~/.local/bin 加進 PATH，請重開 shell 或 `source ~/.zshrc`
pipx install git+https://github.com/AndyAWD/android-cli-mac-x86-community.git

# 之後升級用：
android-cli-mac-x86-community update
```

### 為什麼每個前置都需要

- **`pipx`**：把 Python 命令列工具裝進隔離的 virtualenv，並把指令暴露到
  `PATH`。建議用 `pipx` 而不是直接 `pip install`，因為 Homebrew 的 Python 標
  記為 `EXTERNALLY-MANAGED`（PEP 668），全域 `pip install` 會被擋下。`pipx`
  也會自動帶一個相容的 Python，所以你不用再另外釘 `python@3.11`。
- **`gradle`**：`create` 在 scaffold 完成後會呼叫 `gradle wrapper` 來產生
  `gradlew` / `gradlew.bat`（預設使用 Gradle 8.7，可透過 `--gradle-version` 覆寫，
  或用 `--no-wrapper` 完全跳過）。少了它，wrapper 步驟會被跳過，產生的專案就無法
  `./gradlew assembleDebug` 直到自己另裝 Gradle。
- **要用 `cp -R` 而不是 `ln -s`**：原因如上方註解所說，symlink 會讓
  `sdkmanager` 把連結目標誤判為 SDK 根目錄。
- **`ANDROID_HOME`**：跑 `assembleDebug`（AGP 建置）時會讀這個變數，即便本
  工具能自己找到 SDK，產生出來的 Gradle 專案沒設它仍然 build 不過去。

## 快速上手

```bash
android-cli-mac-x86-community sdk list
android-cli-mac-x86-community emulator create --name pixel7 --image "system-images;android-34;google_apis;x86_64"
android-cli-mac-x86-community emulator start --name pixel7
android-cli-mac-x86-community run --apks app-debug.apk
android-cli-mac-x86-community screen capture > out.png
```

## 指令一覽

| 指令 | 功能 |
|---|---|
| `info [<field>]` | 印出 SDK 位置與環境資訊 |
| `init` | 初始化本機設定與 skills 目錄 |
| `sdk list` | 列出已安裝與可用的 SDK 套件（使用 `--all` 查看完整倉庫） |
| `sdk install <pkg>` | 安裝 SDK 套件 |
| `sdk update` | 更新一個或全部套件 |
| `sdk remove <pkg>` | 移除套件 |
| `emulator create` | 建立虛擬裝置 |
| `emulator start` | 啟動虛擬裝置 |
| `emulator stop` | 停止虛擬裝置 |
| `emulator list` | 列出虛擬裝置 |
| `emulator remove` | 刪除虛擬裝置 |
| `run --apks <files>` | 部署並啟動 APK |
| `screen capture` | 將裝置畫面擷取成 PNG |
| `screen resolve` | 視覺定位 UI 元件（JSON 輸出） |
| `layout` | 取得 layout tree |
| `create` | 建立新的 Android 專案（使用 `--list-templates` 查看可用範本） |
| `describe` | 輸出 JSON 描述專案結構 |
| `docs search/fetch` | 搜尋／抓取 Android 文件（離線知識庫） |
| `skills add/remove/list/find` | 管理 skills（從 `github.com/android/skills` 即時抓取） |
| `update` | 從 GitHub 自我更新（使用 `--check` 僅檢查） |

完整選項請執行 `android-cli-mac-x86-community --help` 或 `android-cli-mac-x86-community help <command>`。

## Skills 來源

Skill 包來自公開的 [`github.com/android/skills`](https://github.com/android/skills) 倉庫（Apache-2.0 授權）。本工具透過 GitHub Contents API 即時抓取，本地快取放在 `~/.android-cli-mac-x86-community/skills/`。本專案**不再散布**任何 skill 內容，上游 repo 是唯一的來源。

匿名 GitHub API 每小時限 60 次請求，如果遇到限流可在環境變數裡設 `GITHUB_TOKEN`。

## 商標聲明

「Android」是 Google LLC 的商標。本專案在名稱與說明中使用此商標，是基於商標法的指稱性合理使用（nominative fair use），目的是讓使用者知道相容對象是 Google 的 Android CLI。本專案與 Google LLC 沒有任何附屬、背書或贊助關係。

## 授權

MIT — 詳見 [LICENSE](./LICENSE)。
