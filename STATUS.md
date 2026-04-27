# 開發狀態

## 當前焦點

M3-① 與 M3-③ 完成。M3-② 擱置待 Windows 端查 search endpoint。

## 最近動向

- 2026-04-27：M3-③ `create` 完成 — `empty_compose` 範本（11 檔，AGP 8.5 / Kotlin 2.0 / Compose BOM 2024.06）、scaffold 變數替換含路徑（`{{package_path}}`）、gradle wrapper 走 PATH（沒裝就 warning skip）。`utils/scaffold.py` 通用化。pytest 55 passed（+6 scaffold、+4 CLI）。
- 2026-04-27：M3-② 擱置 — 原假設「developer.android.com 用 Algolia DocSearch」WebFetch 兩次都驗不到，需在 Windows 端 DevTools 查實際搜尋後端。研究筆記與候選方案見 `notes/m3-docs-search.md`。
- 2026-04-27：M3-① `screen resolve` 完成 — 結構式 selector（--text/--id/--desc/--class），bounds 解析含中心點。重構：抽 `_capture_xml` → `utils/uiautomator.capture_layout_xml`。pytest 45 passed（+10 unit、+4 CLI）。
- 2026-04-27：Intel MBP 接手 — sdkmanager / avdmanager 透過 `brew install --cask android-commandlinetools` 取得，並 symlink 至 `~/Library/Android/sdk/cmdline-tools/latest/`（cli.py 硬編碼此路徑）。editable install + pytest 31 passed，三個煙霧指令（--version / info / emulator list）通過。端到端（emulator start / run apk）尚未實跑。
- 2026-04-27：M2 完成（emulator stop/remove、sdk update/remove、init、describe、layout）+ 14 個新單元測試，pytest 31 passed
- 2026-04-27：遠端 repo 已建立並 push 初始 commit：<https://github.com/AndyAWD/android-cli-mac-x86-community>
- 2026-04-27：M1 本機 scaffold + 工具封裝 + 五個指令 + 17 個單元測試完成，CLI 入口可跑、`--version` / `--help` 都帶免責聲明
- 規劃書凍結於 `C:\Users\Andy\.claude\plans\install-cmd-dazzling-stream.md`

## 已完成

- [x] 規劃書（M1~M4 拆分、命名、商標策略、skills 線上抓取決策）
- [x] M1 scaffold（pyproject.toml、README EN+zh-TW、LICENSE、.gitignore、issue template）
- [x] `utils/android_home.py` SDK 路徑探測
- [x] `tools/{adb,sdkmanager,avdmanager,emulator,_subprocess}.py` 薄封裝
- [x] M1 指令：info、sdk list/install、emulator create/start/list、run、screen capture
- [x] M2 指令：emulator stop/remove、sdk update/remove、init、describe、layout
- [x] `utils/config.py`（~/.android-cli-mac-x86-community/ 路徑與 ensure_layout）
- [x] `utils/layout_xml.py`（uiautomator dump XML → JSON tree、diff 演算法）
- [x] `cli.py` 串起所有 8 個頂層子指令
- [x] M3-① `screen resolve`（find_nodes / parse_bounds、capture_layout_xml 抽出共用）
- [x] M3-③ `create`（utils/scaffold + empty_compose 範本 + gradle wrapper 走 PATH）
- [x] 55 個單元 + CLI 測試通過

## 進行中

無。

## 下一步

- [ ] 端到端整合測試：emulator start → run --apks → screen capture / resolve（已有 AVD `Medium_Phone_API_36.1`）
- [ ] 端到端：用 `create` 真產一個專案、`gradle wrapper` 後跑 `./gradlew assembleDebug` 驗 build 能過（環境裝的 Gradle 9.3.1 vs 範本 AGP 8.5 相容性待測）
- [ ] M3-② docs search/fetch — 擱置，待 Windows 端 DevTools 查 developer.android.com 實際 search endpoint 後再定（候選見 `notes/m3-docs-search.md`）

## 卡點

無。

## 跨機器備忘

- Python 套件目錄使用底線：`src/android_cli_mac_x86_community/`（規劃書原寫的連字號版本不合法）
- 散布名稱（pip / GitHub repo / CLI 指令）保持連字號：`android-cli-mac-x86-community`
- 開發環境驗證：
  - Windows + Python 3.14（M1 17 passed，已停用）
  - macOS Intel + Python 3.13.12（2026-04-27 起，M2 31 passed），openjdk@17 brew、cmdline-tools brew cask + symlink
- 注意：所有 `tools/*.py` 在執行時會去找 SDK 路徑，所以 Windows 上沒裝 Android SDK 也能跑單元測試（測試用 `fake_sdk` fixture），但跑真實指令必須在已安裝 SDK 的 macOS 上做
