[![English](https://img.shields.io/badge/lang-English-lightgrey?style=for-the-badge)](./README.md)
[![繁體中文](https://img.shields.io/badge/lang-繁體中文-red?style=for-the-badge)](./README.zh-TW.md)

# android-cli-mac-x86-community

**這是非官方社群移植版，與 Google LLC 沒有任何關係，也未獲其背書。請勿向 Google 回報本工具的問題。**

一個讓 **Intel macOS（x86_64）** 也能用上類似 Android CLI 體驗的指令列工具。Google 沒有為 Intel Mac 發行官方版本，所以這個專案在現有的 Android SDK 工具（`adb`、`sdkmanager`、`avdmanager`、Android 模擬器，這些在 Intel macOS 上都是官方支援的）之上，包了一層相似的 UX。

## 為什麼有這個專案

Google 的 [Android CLI](https://developer.android.com/tools/agents/android-cli/archive?hl=zh-tw) 在 macOS 平台只發行 `darwin_arm64`，Intel Mac 使用者沒有官方選項。這個專案利用已經存在於 Intel macOS 上的 Android SDK 命令列工具，提供相似的使用體驗。

它**不是** Google binary 的反向工程版本，而是用 Python 重新寫的薄殼，呼叫公開且有文件記載的底層工具。

## 安裝

需要 Intel macOS 上有 Python 3.11+ 與 Android SDK 命令列工具。

```bash
# 1. 前置（一次性）
brew install openjdk@17 python@3.11
# 接著依下面的官方說明安裝 Android command-line tools：
# https://developer.android.com/studio#command-line-tools-only

# 2. 從 GitHub 安裝本工具
pip install git+https://github.com/AndyAWD/android-cli-mac-x86-community.git

# 3. 驗證
android-cli-mac-x86-community info
```

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
| `sdk list` | 列出已安裝與可用的 SDK 套件 |
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
| `screen resolve` | 視覺定位 UI 元件 |
| `layout` | 取得 layout tree |
| `create` | 建立新的 Android 專案 |
| `describe` | 輸出 JSON 描述專案結構 |
| `docs search/fetch` | 搜尋／抓取 Android 文件 |
| `skills add/remove/list/find` | 管理 skills（從 `github.com/android/skills` 即時抓取） |
| `update` | 自我更新 |

完整選項請執行 `android-cli-mac-x86-community --help` 或 `android-cli-mac-x86-community help <command>`。

## Skills 來源

Skill 包來自公開的 [`github.com/android/skills`](https://github.com/android/skills) 倉庫（Apache-2.0 授權）。本工具透過 GitHub Contents API 即時抓取，本地快取放在 `~/.android-cli-mac-x86-community/skills/`。本專案**不再散布**任何 skill 內容，上游 repo 是唯一的來源。

匿名 GitHub API 每小時限 60 次請求，如果遇到限流可在環境變數裡設 `GITHUB_TOKEN`。

## 商標聲明

「Android」是 Google LLC 的商標。本專案在名稱與說明中使用此商標，是基於商標法的指稱性合理使用（nominative fair use），目的是讓使用者知道相容對象是 Google 的 Android CLI。本專案與 Google LLC 沒有任何附屬、背書或贊助關係。

## 授權

MIT — 詳見 [LICENSE](./LICENSE)。
