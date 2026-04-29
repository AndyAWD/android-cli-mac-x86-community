# android-cli-mac-x86-community：Intel macOS 的 Android CLI 社群移植版

## Context（背景）

使用者有一台 2012 Intel MacBook Pro，但 Google 的 Android CLI 只發行 `darwin_arm64`，Intel macOS 沒有官方版本。直接逆向 / 二次散布 Google 的 binary 在條款上、技術上都不可行。

不過 Android CLI 的本質是把 Android 開發工具鏈（`adb`、`sdkmanager`、`avdmanager`、`emulator`、Gradle）包成現代化、agent 友善的 CLI 體驗。**這些底層工具在 Intel macOS 上都是可以取得且官方支援的**。所以替代方案是：**自己寫一個新的 CLI（指令名 `android-cli-mac-x86-community`），在 Intel macOS 上提供與 Android CLI 相似的指令介面，內部呼叫現有 Intel-Mac 兼容的官方工具**。

這不是 Android CLI 的反向工程或仿冒品，而是針對相同底層 SDK 工具的新 UX 殼。

預期成果：使用者在 2012 Intel MBP 上輸入 `android-cli-mac-x86-community run --apks app.apk` 會跟 Android CLI 在 Windows 上輸入 `android run --apks app.apk` 行為相似（部署 APK 到接上的裝置）。

## 命名與商標處理

- **指令名**：`android-cli-mac-x86-community`（`-community` 後綴在指令名本身就標示出非官方身分，是最強的商標合理使用標示位置）
- **使用者自訂短別名建議**：在 README 提示使用者可在 `~/.zshrc` 加 `alias acli='android-cli-mac-x86-community'`，由使用者自行決定，但我們不在套件裡預設安裝任何短別名（避免別名繞過官方識別字串）
- **專案完整名稱**：`Android CLI for Intel Mac (Community Port)`
- **GitHub repo description / Homebrew formula description**：`Unofficial community port of Android CLI for Intel macOS x86_64. Not affiliated with Google LLC.`
- **每次 `--version` 與 `--help` 結尾都會印一段免責聲明**：
  ```
  This is an unofficial community port. Not affiliated with or endorsed by
  Google LLC. "Android" is a trademark of Google LLC, used here under
  nominative fair use to indicate compatibility with Google's Android CLI.
  Source: <repo URL>
  ```
- **README 第一段必須粗體標示**：「非官方社群移植版，與 Google 無關，請勿向 Google 回報問題。」
- **不得使用** Android 綠色機器人 logo、Google 公司商標、Material Design 官方圖示等視覺元素，避免越過商標合理使用界線。
- **Bug 回報模板**：在 GitHub issue template 開頭重複一次「請勿向 Google 回報」訊息。

這套組合走的是商標法上的「指稱性合理使用（nominative fair use）」路線：使用 Android 一詞是為了讓使用者知道相容性對象，但所有露出表面都明示與 Google 無關，因此風險可控。

## 指令對應表（規格核心）

從 Windows 上實測 Android CLI 的 help，整理出每個指令在新 CLI 該怎麼實作。✅ 表示用現成工具直接組成；⚠️ 表示要自寫邏輯但不困難。所有 13 個指令都能達到行為一致（含 `skills`，因為 skill 包就是公開 GitHub repo `github.com/android/skills`，不存在無法重建的私有後端）。

| 指令 | Android CLI 行為 | MBP CLI 實作策略 | 難度 |
|---|---|---|---|
| `android-cli-mac-x86-community info [<field>]` | 印出 SDK 位置等環境資訊 | 讀 `$ANDROID_HOME` / `$ANDROID_SDK_ROOT` / 預設位置；輸出 `sdk_location`、`adb_version`、`java_version` 等欄位 | ✅ 簡單 |
| `android-cli-mac-x86-community init` | 初始化 skills 等環境 | 建立 `~/.android-cli-mac-x86-community/` 目錄、寫預設設定 | ✅ 簡單 |
| `android-cli-mac-x86-community create [--name --minSdk --output --list <template>]` | 建立 Android 專案 | 用內建的 Gradle / AGP 範本（單一 Activity、Compose、Library 等少數幾個）做檔案展開 | ⚠️ 中 |
| `android-cli-mac-x86-community describe --project_dir` | 輸出 JSON 描述專案結構與 APK 輸出位置 | 跑 `gradlew :app:tasks --all` + 解析 `app/build/outputs/`；輸出統一 JSON schema | ⚠️ 中 |
| `android-cli-mac-x86-community docs search/fetch` | 搜尋/抓取 Android 官方文件 | 呼叫 `https://developer.android.com/_search` 或直接 `curl` + HTML 轉 markdown | ✅ 簡單 |
| `android-cli-mac-x86-community emulator create/start/stop/list/remove` | AVD 管理 | 純粹 wrap `avdmanager`、`emulator`、`adb emu kill` | ✅ 簡單 |
| `android-cli-mac-x86-community layout [--diff --device --output --pretty]` | 取得 App 的 UI tree | wrap `adb shell uiautomator dump` → 抓 XML → 轉 JSON；`--diff` 在本地存上一次的快照做比對 | ⚠️ 中 |
| `android-cli-mac-x86-community run --apks ... [--activity --device --type --debug]` | 部署 APK 並啟動 | `adb install` 多 APK 用 `adb install-multiple`；之後 `adb shell am start -n pkg/.activity` | ✅ 簡單 |
| `android-cli-mac-x86-community screen capture` | 截圖成 PNG | `adb exec-out screencap -p > out.png` | ✅ 簡單 |
| `android-cli-mac-x86-community screen resolve` | 視覺方式定位 UI 元件 | 結合 `uiautomator dump` + 螢幕座標；提供互動式或語意搜尋 | ⚠️ 中 |
| `android-cli-mac-x86-community sdk install/update/remove/list` | SDK 套件管理 | 純粹 wrap `sdkmanager` | ✅ 簡單 |
| `android-cli-mac-x86-community skills add/remove/list/find` | 管理 agent skills | Skill 包來源是公開 repo `github.com/android/skills`：`list` 用 GitHub Contents API 列出 repo 子目錄；`find` 在清單做 keyword filter；`add` 用 `git clone --depth 1` 或下載 tarball 解壓到 `~/.android-cli-mac-x86-community/skills/<name>/`；`remove` 直接砍目錄 | ✅ 簡單 |
| `android-cli-mac-x86-community update [--url]` | 自我更新 | 從我們自己的 release 端點下載新版 | ✅ 簡單 |

## 架構設計

### 語言選擇：Python 3.11+

理由：
- 2012 MBP 上要安裝起來最容易（macOS 內建 Python，或 `brew install python`）。
- 大部分指令都是 wrap shell 工具（`subprocess`），Python 寫起來最直接。
- 容易讀、容易改，使用者本人後續也比較能維護。
- 缺點是不像 Rust 編譯成單一 binary，但對個人工具足夠了。

### 模組結構

```
android-cli-mac-x86-community/
├── pyproject.toml
├── README.md
├── src/android-cli-mac-x86-community/
│   ├── __main__.py          # entry point, 接 CLI 框架（typer 或 click）
│   ├── cli.py               # 頂層子指令路由
│   ├── commands/
│   │   ├── info.py
│   │   ├── init.py
│   │   ├── create.py
│   │   ├── describe.py
│   │   ├── docs.py
│   │   ├── emulator.py
│   │   ├── layout.py
│   │   ├── run.py
│   │   ├── screen.py
│   │   ├── sdk.py
│   │   ├── skills.py
│   │   └── update.py
│   ├── tools/               # 對外部工具的薄封裝
│   │   ├── adb.py
│   │   ├── sdkmanager.py
│   │   ├── avdmanager.py
│   │   └── emulator.py
│   ├── templates/           # create 指令用的專案範本
│   │   └── basic_compose/
│   └── utils/
│       ├── android_home.py  # 找 SDK 路徑
│       └── json_io.py
└── tests/
```

### 核心設計原則

1. **薄封裝優先**：能 `subprocess.run` 解決的就不要自己重造。`android-cli-mac-x86-community sdk install` 內部就是組好參數丟給 `sdkmanager`，不要自己解析套件 manifest。
2. **JSON 輸出第一**：所有非互動指令都支援 `--json` 旗標，輸出 schema 與 Android CLI `describe` 對齊，方便外部工具串接。
3. **錯誤訊息要可定位**：包裝外部工具時，把 stderr 原樣保留，加上自己的 context（哪個指令、用了哪個內部工具）。
4. **`skills` 採取「本地 manifest 模式」**：不接任何 LLM agent runtime，只做檔案層級的 add/remove/list；如未來想接 Claude / Gemini SDK 再開新指令。

## 前置工具（Intel macOS 上需要）

使用者要先確保下列東西在 2012 MBP 上裝起來：

1. **Java JDK 17**：`brew install openjdk@17`
2. **Android Command-line Tools**：從 https://developer.android.com/studio#command-line-tools-only 下載 `commandlinetools-mac-*.zip`，解壓到 `~/Library/Android/sdk/cmdline-tools/latest/`
3. **adb / platform-tools**：透過 `sdkmanager "platform-tools"` 安裝
4. **Python 3.11+**：`brew install python@3.11`

這部分要寫進 `android-cli-mac-x86-community/README.md` 與 `android-cli-mac-x86-community init` 的環境檢查邏輯。

## 開發工作流（兩台機器分工）

開發機與目標機不同台，建議用 GitHub 當同步通道：

| 階段 | 機器 | 任務 |
|---|---|---|
| 寫程式碼、單元測試 | Windows（D:\Project\Android CLI\） | 編輯、`pytest tests/`，搭配 mocked subprocess 測試指令拼接邏輯 |
| 行為對照（與官方 Android CLI） | Windows | 在同一台直接執行 Windows 上已裝好的 `android` 並比對 JSON 輸出 schema |
| 整合測試（真實 adb / sdkmanager / emulator） | Intel MBP | `git pull` → `pip install -e .` → 連實機或 AVD 跑端到端 |
| 釋出 | Windows 或 Mac 任一台 | `git tag vX.Y.Z` → push → GitHub Actions 跑 release（純 Python sdist + wheel，不用編譯） |

簡而言之：**邏輯開發在 Windows，硬體相依測試在 Intel MBP**，靠 `git push` / `git pull` 同步。Python 純邏輯部分跨平台，不會因為在哪台寫而行為不同。

### 跨機器進度同步（避免「我現在做到哪了」迷路）

三層機制各司其職：

1. **Git commit history**：基本層。切機器前必 `git push`，到另一台必先 `git pull`，`git log --oneline` 一目瞭然。允許 WIP 提交（`git commit -m "WIP: ..."`），上正式 main 前再用 `git rebase -i` 整理。
2. **GitHub Issues + Project Board**：把 M1~M4 每個指令拆成 issue，狀態用 Project Board 的 Todo / In Progress / Done 欄位管理。瀏覽器在哪台都看得到，無縫跨機器。
3. **repo 根目錄的 `STATUS.md`**：用最白話的方式紀錄「當前焦點」「卡點」「下一步」。優點是 `git pull` 完不需要開瀏覽器就能讀，特別適合在 Intel MBP 沒網路時也能對齊。每次切機器前更新它，跟著 commit。

工作流範例：

- 在 Windows 寫到一半要切去 MBP 跑整合測試 → 更新 `STATUS.md` 寫「已完成 sdk list 的 unit test，下一步去 MBP 驗 sdkmanager 真實輸出」→ `git commit -am "WIP: ..." && git push`
- 在 MBP 開機 → `git pull` → 讀 `STATUS.md` 知道要做什麼 → 跑整合測試 → 發現 stderr 格式不同 → 在對應 issue 留言 → 修 `STATUS.md` → `commit && push`
- 回 Windows → `git pull` → 接著修

## GitHub repo 初始化（M1 第一步）

用 `gh` CLI 建立公開 repo，授權 MIT，描述為英文：

```bash
gh repo create android-cli-mac-x86-community \
  --public \
  --description "Unofficial community port of Android CLI for Intel macOS (x86_64). Wraps adb / sdkmanager / avdmanager / emulator to provide an Android-CLI-like UX. Not affiliated with Google LLC." \
  --license MIT \
  --add-readme
```

repo 建好後立刻補上：

- `LICENSE`：MIT 授權全文（`gh repo create --license MIT` 會自動產生）
- `README.md`：**英文版為主**，最上方放兩個語言切換按鈕（用 shields.io）：
  ```markdown
  [![English](https://img.shields.io/badge/lang-English-blue)](./README.md)
  [![繁體中文](https://img.shields.io/badge/lang-繁體中文-red)](./README.zh-TW.md)
  ```
  其下英文內容包含：
  - 一句話 tagline（與 GitHub description 一致）
  - **粗體 disclaimer**：Unofficial community port. Not affiliated with or endorsed by Google LLC.
  - Why this exists（Intel macOS 沒有官方 binary 的事實）
  - Installation（`pip install` from GitHub URL）
  - Quick start（最小可跑範例）
  - Command reference 表格（13 個指令對應 Android CLI）
  - Trademark notice（"Android" is a trademark of Google LLC, used under nominative fair use）
  - License: MIT
- `README.zh-TW.md`：繁體中文版（台灣用語），結構與英文版一致，最上方同樣放兩顆語言按鈕（指向 `./README.md` 與 `./README.zh-TW.md`），把當前語言那顆改顏色或加 `(active)` 表示
- `.github/ISSUE_TEMPLATE/bug_report.md`：bug 模板，第一段強制提醒「This is an unofficial community port. DO NOT report issues to Google.」
- `pyproject.toml`：套件 metadata，`description` 用英文（與 GitHub repo description 對齊）
- `STATUS.md`：跨機器進度同步用，初始內容「Project initialized. Starting M1.」

## 階段性里程碑

避免一次做完 13 個指令導致無限期收不回來，分四階段：

### M1（MVP，1–2 週可完成）

完成最低有用集合，能跑通「裝 SDK → 起模擬器 → 跑 APK → 截圖」這條 loop：

- `android-cli-mac-x86-community info`
- `android-cli-mac-x86-community sdk list/install`
- `android-cli-mac-x86-community emulator create/start/list`
- `android-cli-mac-x86-community run`
- `android-cli-mac-x86-community screen capture`

### M2（補齊開發體驗）

- `android-cli-mac-x86-community emulator stop/remove`
- `android-cli-mac-x86-community sdk update/remove`
- `android-cli-mac-x86-community init`
- `android-cli-mac-x86-community describe`
- `android-cli-mac-x86-community layout`

### M3（內容類）

- `android-cli-mac-x86-community docs search/fetch`
- `android-cli-mac-x86-community create`（先支援 1 個範本）
- `android-cli-mac-x86-community screen resolve`

### M4（補齊）

- `android-cli-mac-x86-community skills add/remove/list/find`：透過 GitHub Contents API 列舉 `github.com/android/skills` 的子目錄作為可用 skills；`add` 下載 tarball 解壓到 `~/.android-cli-mac-x86-community/skills/<name>/`；`find` 對清單做關鍵字過濾；`remove` 直接砍目錄
- `android-cli-mac-x86-community update`
- 多範本支援

## 要建立 / 修改的檔案

這份計畫會在 `D:\Project\Android CLI\android-cli-mac-x86-community\`（或使用者指定的另一個目錄）下新建整個 Python 專案。Windows 上 `D:\Project\Android CLI\install.cmd` 與三個官方 binary 都不動。

關鍵新檔（M1 階段）：

- `D:\Project\Android CLI\android-cli-mac-x86-community\pyproject.toml`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\__main__.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\cli.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\commands\info.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\commands\sdk.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\commands\emulator.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\commands\run.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\commands\screen.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\tools\adb.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\tools\sdkmanager.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\tools\avdmanager.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\src\android-cli-mac-x86-community\utils\android_home.py`
- `D:\Project\Android CLI\android-cli-mac-x86-community\README.md`

## 驗證方式

每個指令在 M1 結束時，至少要通過下列「對照測試」：

1. **環境**：在 Intel MBP 上裝完 `android-cli-mac-x86-community` 與前置工具後，`android-cli-mac-x86-community info` 應正確列出 SDK 路徑、`adb` 版本。
2. **功能對照**：使用同一台 Android 實機（或 AVD），分別在 Windows + Android CLI 與 MBP + android-cli-mac-x86-community 上執行下列腳本，輸出語意應一致：
   ```
   <cli> sdk list                          # 兩邊套件清單應一致
   <cli> emulator list                     # 兩邊看到一致 AVD
   <cli> run --apks app-debug.apk          # 兩邊都成功安裝並啟動
   <cli> screen capture > out.png          # 兩邊截圖檔案 size > 0、PNG 解碼正常
   ```
3. **JSON schema 一致**：`android-cli-mac-x86-community describe --project_dir <repo>` 的輸出與 Android CLI `describe` 同一專案的輸出，頂層欄位（build targets、APK paths）名稱一致，方便外部工具雙向支援。
4. **單元測試**：`tests/` 目錄至少覆蓋每個 `tools/*.py` 的指令拼接邏輯（用 mocked subprocess）。

## 後續討論點（M1 開工前要決定）

1. ~~CLI 名稱~~：已決定為 `android-cli-mac-x86-community`，專案名為 `Android CLI for Intel Mac (Community Port)`。
2. ~~`skills` 是否要做~~：已確認 skill 來源是公開 repo `github.com/android/skills`，可完整實作，列入 M4。
3. ~~散布方式~~：已決定走 GitHub。在 `github.com/<owner>/android-cli-mac-x86-community` 建立公開 repo，每個版本透過 GitHub Releases 釋出 `android-cli-mac-x86-community-vX.Y.Z.tar.gz`（含原始碼與內建 skills 子集）。安裝方式為 `pip install` 直接從 GitHub URL，或日後有需要再追加 Homebrew tap。
4. ~~skills 散布~~：上游 `github.com/android/skills` 採 Apache License 2.0。為簡化實作與避免再散布的法律負擔，**決定走純線上抓取**：
   - 我們**不在自己的 release 中內建任何 skill 內容**，只在 README 註明「skills 來源：https://github.com/android/skills」
   - `skills list` / `skills find`：直接打 GitHub Contents API 列舉 repo 子目錄，加 5 分鐘 in-memory cache 避免短時間內重複請求
   - `skills add <name>`：下載對應子目錄的 tarball，解壓到 `~/.android-cli-mac-x86-community/skills/<name>/`，作為本機快取；之後 LLM agent 或其他工具讀的就是這個快取，不會每次都打網路
   - `skills remove <name>`：砍 `~/.android-cli-mac-x86-community/skills/<name>/`
   - GitHub API 匿名上限是 60 req/hour，對個人開發者足夠；若日後超量再考慮加上「使用者自帶 GitHub token」的選項
   - 因為我們不再 redistribute，原本要在 release 裡放的 Apache-2.0 LICENSE / NOTICE / commit-hash 註記**全部不再需要**
