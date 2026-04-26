# 開發狀態

## 當前焦點

M1 本機部分完成，等待使用者確認後執行 `gh repo create` 建遠端。

## 最近動向

- 2026-04-27：M1 本機 scaffold + 工具封裝 + 五個指令 + 17 個單元測試完成，CLI 入口可跑、`--version` / `--help` 都帶免責聲明
- 規劃書凍結於 `C:\Users\Andy\.claude\plans\install-cmd-dazzling-stream.md`

## 已完成

- [x] 規劃書（M1~M4 拆分、命名、商標策略、skills 線上抓取決策）
- [x] M1 scaffold（pyproject.toml、README EN+zh-TW、LICENSE、.gitignore、issue template）
- [x] `utils/android_home.py` SDK 路徑探測
- [x] `tools/{adb,sdkmanager,avdmanager,emulator,_subprocess}.py` 薄封裝
- [x] `commands/info.py`（含 --json 輸出）
- [x] `commands/sdk.py`（list / install）
- [x] `commands/emulator.py`（create / start / list）
- [x] `commands/run.py`
- [x] `commands/screen.py`（capture）
- [x] `cli.py` 串起所有子指令、`--version` / `--help` 帶免責聲明
- [x] 17 個單元測試通過（涵蓋 android_home、adb、sdkmanager、avdmanager）

## 進行中

無。

## 下一步

- [ ] 在使用者確認後執行 `gh repo create` 並 push 初始 commit
- [ ] 在 Intel MBP 上 `git pull` + `pip install -e .` 跑端到端整合測試（需要實機或 AVD）
- [ ] 進入 M2：`emulator stop/remove`、`sdk update/remove`、`init`、`describe`、`layout`

## 卡點

無。

## 跨機器備忘

- Python 套件目錄使用底線：`src/android_cli_mac_x86_community/`（規劃書原寫的連字號版本不合法）
- 散布名稱（pip / GitHub repo / CLI 指令）保持連字號：`android-cli-mac-x86-community`
- 開發環境驗證：Windows + Python 3.14（執行 pytest 17 passed）
- 注意：所有 `tools/*.py` 在執行時會去找 SDK 路徑，所以 Windows 上沒裝 Android SDK 也能跑單元測試（測試用 `fake_sdk` fixture），但跑真實指令必須在已安裝 SDK 的 macOS 上做
