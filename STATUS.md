# 開發狀態

## 當前焦點

開發機切到 Intel MBP，環境就緒。準備進 M3。

## 最近動向

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
- [x] 31 個單元測試通過

## 進行中

無。

## 下一步

- [ ] 端到端整合測試：emulator start → run --apks → screen capture（已有 AVD `Medium_Phone_API_36.1`）
- [ ] 進入 M3：docs search/fetch、create（先支援 1 個範本）、screen resolve

## 卡點

無。

## 跨機器備忘

- Python 套件目錄使用底線：`src/android_cli_mac_x86_community/`（規劃書原寫的連字號版本不合法）
- 散布名稱（pip / GitHub repo / CLI 指令）保持連字號：`android-cli-mac-x86-community`
- 開發環境驗證：
  - Windows + Python 3.14（M1 17 passed，已停用）
  - macOS Intel + Python 3.13.12（2026-04-27 起，M2 31 passed），openjdk@17 brew、cmdline-tools brew cask + symlink
- 注意：所有 `tools/*.py` 在執行時會去找 SDK 路徑，所以 Windows 上沒裝 Android SDK 也能跑單元測試（測試用 `fake_sdk` fixture），但跑真實指令必須在已安裝 SDK 的 macOS 上做
