# M3-② `docs search` / `docs fetch` — 研究筆記

## TL;DR

**問題已解決，方向徹底翻轉。** 不需要去查 `developer.android.com` 的搜尋後端，因為**上游 `android docs` 根本不搜那個網站**。它下載一份預打包的 Knowledge Base zip 到本地，用 Apache Lucene 建索引離線搜尋。

community fork 直接 mirror 同一機制即可：下載同一份公開 zip，用 Python FTS 引擎建本地索引。零 API key、零 scrape、零外部依賴。

## 進度時間軸

- 2026-04-27 macOS 端：M3-① `screen resolve` 完成、M3-③ `create` 完成。
- 2026-04-27 macOS 端：嘗試實作 M3-② 策略 A（Algolia DocSearch），WebFetch 兩次驗證假設 → 不成立 → 擱置。
- 2026-04-27 Windows 端：直接執行已安裝的上游 `android docs search` 並逆向 `main.jar`，**找到完整實作機制**。原訂的 DevTools 驗證任務已撤銷（前提錯誤）。

## 已驗證為錯的假設（保留作為紀錄）

| 假設 | 驗證方式 | 結果 |
|---|---|---|
| developer.android.com 用 Algolia DocSearch | WebFetch `https://developer.android.com/docs` | HTML 內找不到 `algolia` 字樣 |
| 搜尋結果頁 `/s/results?q=...` 是靜態 HTML | WebFetch `https://developer.android.com/s/results?q=Activity` | 空殼頁，搜尋結果由 JS 動態載入 |
| **上游 `android docs` 是去打 developer.android.com 的搜尋 API** | 執行 `android docs search "Activity lifecycle"`、檢查 `~/.android/cli/`、解壓 `main.jar` | **完全錯。它走本地 Lucene + 預打包 KB zip。** |

## ⭐ Windows 端逆向結果（2026-04-27）

### 上游架構

`android.exe`（4.5 MB Rust binary）會：

1. 啟動內嵌 JVM（`~/.android/cli/bundles/<sha1>/jre/`）
2. 載入 `main.jar`（40 MB Kotlin + Apache Lucene + 業務邏輯）
3. `docs search` / `docs fetch` 由 `com/android/cli/docs/DocsCLI.class` 處理
4. 檢索引擎：`org/apache/lucene/...`（標準 Apache Lucene）

啟動時 log（開 `RUST_LOG=debug` 看到）：

```
[INFO] Using embedded data zip
[DEBUG] Setting DLL search path
[DEBUG] [JVM] Adding "...\bundles\<sha1>\jre\bin" to the DLL search path
Waiting for index to be ready...
New version available. Downloading...
Downloading Knowledge Base ... ...
Knowledge Base zip updated successfully.
```

### Knowledge Base zip 下載

從 `main.jar` 內 `com/android/cli/docs/KnowledgeBaseConstants.class` 抓到的常數：

| 項目 | 值 |
|---|---|
| **下載 URL** | `https://dl.google.com/dac/dac_kb.zip` |
| **HTTP 客戶端** | `java.net.http.HttpClient`（Java 11+ 內建） |
| **新鮮度檢查** | HTTP ETag（檔案 `dac.etag`，當前值 `"5bee57a"`） |
| **檔案大小** | 約 19 MB |
| **解壓大小** | 約 63 MB，9616 個檔案（4808 entry × 2 檔） |
| **API key / 認證** | 無，完全公開 CDN |
| **快取位置** | `~/.android/cli/docs/kbzip/dac.zip` |
| **本地索引位置** | `~/.android/cli/docs/index/`（Lucene `_N.cfe`/`_N.cfs`/`_N.si`/`segments_1`） |
| **索引完成標記** | `index/index_ready.json`（含 `zipHash` SHA-256） |

### KB zip 內容格式

每筆 entry 兩個檔案：

```
android/guide/components/activities/activity-lifecycle.json
android/guide/components/activities/activity-lifecycle.md.txt
```

`.json` 範例：

```json
{
    "short_description": "Overview of the user experience for ...",
    "keywords": "commissioning,UX,Fast Pair,Android,...",
    "title": "Commissioning UX on Android",
    "relative_url": "home/apis/android/ux/commissioning",
    "url": "kb://home/apis/android/ux/commissioning"
}
```

`.md.txt` 為純 Markdown 內文。

### `kb://` URL schema

上游搜尋結果用的不是 `https://` 而是 `kb://<relative_url>`，例如：

```
kb://android/guide/components/activities/activity-lifecycle
```

→ 對應 zip 內 `android/guide/components/activities/activity-lifecycle.md.txt`。

`android docs fetch <kb-url>` 就是把 `kb://` prefix 拆掉、接上 `.md.txt`、從**本地快取 zip** 讀檔，**不發任何 network request**。

### KB 涵蓋範圍

不只 developer.android.com，例如也包含：

- `android/...`（Android 官方文件）
- `JetBrains/kotlin-multiplatform-dev-docs/...`
- `JetBrains/kotlin-agent-skills/...`

實際 entry 數：4808 筆（`Index created with 4808 items and committed.`）。

## community fork 實作方案（方案 F：mirror 上游機制）

### `docs search <query>` 流程

1. 確保 `~/.android-cli-mac-x86-community/docs/dac_kb.zip` 存在且新鮮
   - 第一次：直接下載
   - 之後：發 `If-None-Match: <local etag>` 的 HEAD/GET，304 就跳過、200 就更新
2. 確保本地 FTS 索引已建好（zip hash 對得上時跳過重建）
3. 跑搜尋，輸出 top N 結果（title、kb URL、short_description）

### `docs fetch <kb-url>` 流程

1. 解析 `kb://<path>` → `<path>.md.txt`
2. 從快取 zip 讀檔（`zipfile.ZipFile.read`），輸出純文字
3. 不存在就回 error 訊息

### 技術選型建議

**FTS 引擎候選**：

| 選項 | 優 | 缺 |
|---|---|---|
| **SQLite FTS5** | 標準庫、零依賴、tokenizer 夠用 | 中文分詞要自己處理（但 KB 內容大多英文，影響小） |
| `whoosh` | 純 Python、零原生編譯 | 已長期不維護（最後 release 2022） |
| `tantivy-py` | Rust 引擎、效能最好、最接近 Lucene 行為 | 多一個原生依賴 |

**首選 SQLite FTS5**——Python 內建、4808 筆規模綽綽有餘、跨平台無編譯。

### 預期檔案

- `src/android_cli_mac_x86_community/commands/docs.py` — `docs.app` typer subapp，含 `search` / `fetch` 兩個 subcommand
- `src/android_cli_mac_x86_community/utils/docs_kb.py` — KB zip 下載 + ETag 快取 + 本地路徑解析
- `src/android_cli_mac_x86_community/utils/docs_index.py` — SQLite FTS5 建索引 + 查詢
- `tests/test_docs.py` — mock `httpx`/`urllib` 驗 ETag 流程；用小型 fake zip 驗索引/查詢/fetch

### 依賴

- `httpx`（已在 `pyproject.toml`）—— 下載 zip
- `sqlite3`（標準庫）—— FTS5 索引
- `zipfile`（標準庫）—— 讀 KB 內容

### 合法性與授權

`https://dl.google.com/dac/dac_kb.zip` 是 Google 公開 CDN、無認證、無 robots 限制（Google 自家工具 `android docs` 就靠它）。下載 + 本地索引使用屬合理使用。重新發布 zip 內容要看內容本身的授權（Android docs 多為 CC BY 4.0，但本工具不重發布、只當 client，這個風險不存在）。

## 不影響的事

- M3-① `screen resolve` 已完成（commit `17765c2`，pytest 45 passed）
- M3-③ `create` 已完成（commit `b78ab2a`，pytest 55 passed）
- 與 M3-② 互不相依

## 候選方案（保留作參考）

下表是 Windows 逆向**前**討論的備案，已被方案 F 取代，僅作紀錄：

| 選項 | 機制 | 現況 |
|---|---|---|
| B | `docs search` 印 `google.com/search?q=site:...` 讓使用者點 | 棄用 |
| B+ | scrape Google 結果頁 | 棄用 |
| C | 只做 `docs fetch <url>` | 棄用 |
| D | Google Programmable Search Engine API | 棄用 |
| E | scrape `developer.android.com/s/results` | 棄用（已驗證動態 render） |
| C+B | fetch 做正事、search 印 Google URL | 棄用 |
| **F**（新） | **mirror 上游：下載 `dl.google.com/dac/dac_kb.zip` + 本地 FTS** | **採用** |
