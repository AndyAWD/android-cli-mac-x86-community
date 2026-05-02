# 開發狀態

## 當前焦點

M3 與 M4 全部完成、v0.1.0 已釋出、CI 已上線、Windows 與 macOS 跨平台修補完成。macOS 端 `create` + `assembleDebug` 三範本端到端驗證通過。剩 `screen resolve` 在 Intel Mac × Android 16 模擬器組合下因 OOM 不穩定（見卡點）。

## 最近動向

- 2026-05-02：**`create` 支援自訂 Gradle 版本** — 實作 `--gradle-version` 旗標（預設維持 8.7 以匹配 AGP 8.5），讓使用者在 scaffold 專案時可覆寫 Gradle wrapper 版本，避免寫死在程式碼中。新增 2 個單元測試並更新雙語 README。
- 2026-05-02：**Intel MBP 端到端全鏈驗證通過** — 用 `compose_navigation` 範本走完 `create` → `./gradlew assembleDebug` → `emulator start pixel_api31` → `run --apks` → `screen capture` → 點「Open detail 42」按鈕 → 再 capture，Home 與 Detail 兩頁都正確 render（320×640 PNG）。Build 1m 17s（依賴已快取，非首次）；APK 8.7 MB；`mResumedActivity = com.example.e2etestapp/.MainActivity`、`pidof` 拿到 PID。**補完上一條「下一步」中「驗 `run --apks` 安裝剛 build 出的 APK」**。觀察：cold boot 後 SystemUI 偶發 ANR（系統層 dialog 蓋掉畫面），`adb shell am crash com.android.systemui` 重啟即恢復；繞過 CLI 直跑 `emulator -avd` 也重現，與本專案無關，但已記入「下一步」做 helper。順帶清理舊 AVD（`test_api32`/`test_api33`/`Medium_Phone_API_36.1`），本機只留 `pixel_api31`。
- 2026-04-28：**macOS 端到端驗證 + 跨平台修補** — 兩個 bug 修掉：(1) `_subprocess._windows_executable_suffixes()` 切 PATHEXT 寫死用 `;`（不是 `os.pathsep`），讓 monkeypatch sys.platform 在非 Windows 也能正確切（`PATHEXT` 規格永遠分號分隔，跟 PATH 不同），修好 `test_resolve_finds_exe_suffix_on_windows` 在 macOS 失敗。(2) `commands/create._run_gradle_wrapper()` 加 `--gradle-version 8.7 --distribution-type bin`，避開環境 Gradle 9.3.1 對 AGP 8.5 plugin 解析卡 5+ 分鐘的相容性問題，wrapper 統一鎖在 Gradle 8.7 (AGP 8.5 對應穩定版)。實機驗證：`docs search`/`skills list`/`update --check` 全通過；三範本（empty_compose / empty_views / compose_navigation）`create` + `./gradlew assembleDebug` 全部 BUILD SUCCESSFUL（首次 12m33s 含下載，後續 5m9s / 1m40s）；`screen capture` 抓到 1080×2400 PNG。pytest 115 passed。
- 2026-04-28：**Windows 跨平台修補** — `android_home.py` 加入 `%LOCALAPPDATA%\Android\Sdk` 與 `~/AppData/Local/Android/Sdk` 兩個 Windows 預設路徑（Android Studio 預設安裝位置）；`tools/_subprocess.resolve()` 在 Windows 對絕對路徑探測 PATHEXT 副檔名（`.exe` / `.bat` / ...），讓 `tool_path("platform-tools/adb")` 在 Windows 也找得到 `adb.exe`。新增 5 個測試。Windows 真實機器（已裝 Android Studio）端到端通過：`info` 自動找到 SDK 並印 adb 版本、`emulator list` 列出 AVD。pytest 115 passed（+5）。
- 2026-04-28：**v0.1.0 釋出 + GitHub Actions CI 上線** — `.github/workflows/test.yml` 對 ubuntu/macos/windows × Python 3.11/3.12/3.13 共 9 個矩陣跑 `pytest -q`，push/PR 觸發。版本由 `0.1.0.dev0` → `0.1.0`，打 annotated tag `v0.1.0` 並 `gh release create`，自此 `update` 指令真的有東西可裝。
- 2026-04-28：**M4-(2) `update` 完成** — `utils/self_update.py` 查 GitHub Releases API（`/releases/latest`），無 release 回 None；`is_newer` 比版本（strip `v` prefix）；`pip_install_command` 用 `sys.executable -m pip` 確保跑當前環境的 pip。`commands/update.py`：預設裝最新 tag、`--check` 只檢查不裝、`--url` 安裝任意 pip target、`--repo` 改 owner/name；無 release 時 fallback 裝 default branch。新增 17 個測試（mock GitHub API + mock pip subprocess）。
- 2026-04-28：**M4-(3) 多範本完成** — 新增 `empty_views`（AppCompat + ConstraintLayout + ViewBinding，給不想用 Compose 的使用者）與 `compose_navigation`（Compose + navigation-compose 2.7.7，含 Home → Detail 路由示範）。`create` 加 `--list-templates`；參數改成 path/name/package 都改 Optional 以便支援單跑 `--list-templates`。新增 4 個測試。Windows 真實 GitHub `update --check` 跑通（顯示 no published releases 且 exit 0）。pytest 110 passed（93 → 110，+17 update +4 templates）。
- 2026-04-28：**M4-(1) `skills add/remove/list/find` 完成（Windows 端）** — `utils/skills_repo.py`：GitHub Contents API 列舉 `android/skills` 子目錄（5 分鐘 in-memory TTL cache）、`/repos/.../tarball` 下載 default-branch tarball 並只解壓目標 subtree（含 zip-slip 防護）、原子替換暫存 dir 避免半解壓。`commands/skills.py`：4 個子指令、`--json` / `--upstream` / `--no-cache` 選項、`add/remove` 對 `~/.android-cli-mac-x86-community/skills/<name>/` 操作、`upstream` 從 `config.toml [skills]` 讀（fallback `android/skills`）。新增 18 個測試（list/find/cache/error path、tarball 解壓只取 subtree、replace existing、未知 skill、path traversal 拒絕、CLI 全路徑）。pytest 89 passed（+18）。Windows 真實 GitHub 端到端通過：list 7 個 skill、`add navigation`（24 檔）、`remove` 乾淨。
- 2026-04-27：**M3-② `docs search` / `docs fetch` 完成（Windows 端實作）** — 採方案 F：`utils/docs_kb.py` 走 `https://dl.google.com/dac/dac_kb.zip` + HTTP ETag 快取、`utils/docs_index.py` 用 SQLite FTS5 建索引（zip SHA-256 變才重建）、`commands/docs.py` 提供 `search`（含 `--json` / `--limit` / `--refresh`）與 `fetch <kb://...>`。新增 16 個測試（FTS5 query escape、ETag 304/200/force/error、CLI search/fetch 正反路徑）。pytest 71 passed（+16）。Windows 真實 CDN 端到端煙霧測通過。
- 2026-04-27：M3-② Windows 端逆向上游 `android docs` — 確認非 AI、是 Apache Lucene 離線搜尋。下載 URL `https://dl.google.com/dac/dac_kb.zip`（19 MB、4808 entries、ETag 快取、無 API key）。原本要去查 `developer.android.com` 搜尋後端的方向作廢，改採方案 F：mirror 上游機制 + Python SQLite FTS5。詳 `notes/m3-docs-search.md`。
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
- [x] M3-② `docs search` / `docs fetch`（utils/docs_kb ETag 快取 + utils/docs_index SQLite FTS5 + commands/docs）
- [x] M4-(1) `skills add/remove/list/find`（utils/skills_repo + commands/skills，GitHub tarball + subtree 解壓 + zip-slip 防護）
- [x] M4-(3) 多範本（templates/empty_views + templates/compose_navigation；`create --list-templates`）
- [x] M4-(2) `update`（utils/self_update + commands/update，GitHub Releases API + `sys.executable -m pip`，含 --check / --url / --repo）
- [x] `commands/create --gradle-version` 支援自訂 Gradle 版本
- [x] 115 個單元 + CLI 測試通過（含 Windows SDK 路徑解析與 PATHEXT 探測）
- [x] v0.1.0 GitHub Release（tag `v0.1.0`）
- [x] GitHub Actions CI（ubuntu/macos/windows × Python 3.11/3.12/3.13）

## 進行中

無。

## 下一步

- [ ] 端到端：在 ARM Mac 或更輕量 system image（API 33/34）上把 `screen resolve` 跑通
- [x] `emulator start` UX helper：加 `--wait-boot`（內建 `adb wait-for-device` + 輪詢 `sys.boot_completed` / `init.svc.bootanim`）與 `--unlock`（內建 keyevent 82 + 4）旗標。已內建 ANR dialog 偵測 → `am crash com.android.systemui` 重啟。

## 卡點

- **`screen resolve` 在 Intel Mac × Android 16（API 36）模擬器上 OOM**：`adb shell uiautomator dump` 偶爾能成、多數時候 device 端 binary 被 SIGKILL（exit 137），原因是模擬器 RAM 2 GB 已 ~94% 用滿（surfaceflinger ~235% CPU），UiAutomation service 連線 5 秒 timeout。`screen capture` 不需 UiAutomation 故穩定通過。建議改 ARM Mac 或換 API 33/34 image 再驗。

## 跨機器備忘

- Python 套件目錄使用底線：`src/android_cli_mac_x86_community/`（規劃書原寫的連字號版本不合法）
- 散布名稱（pip / GitHub repo / CLI 指令）保持連字號：`android-cli-mac-x86-community`
- 開發環境驗證：
  - Windows + Python 3.14（M1 17 passed，已停用）
  - macOS Intel + Python 3.13.12（2026-04-27 起，M2 31 passed），openjdk@17 brew、cmdline-tools brew cask + symlink
- 注意：所有 `tools/*.py` 在執行時會去找 SDK 路徑，所以 Windows 上沒裝 Android SDK 也能跑單元測試（測試用 `fake_sdk` fixture），但跑真實指令必須在已安裝 SDK 的 macOS 上做
