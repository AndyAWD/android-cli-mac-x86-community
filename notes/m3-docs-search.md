# M3-② `docs search` / `docs fetch` — 研究筆記

## TL;DR

擱置中。原訂策略「用 Algolia DocSearch」假設錯誤（developer.android.com 不是用 Algolia）。
要請 Windows 端用 Chrome DevTools 真實操作搜尋一次，把實際 search endpoint 的 host / 請求 / 回應結構記錄下來，再回到 macOS 端據此決定方案並實作。

## 進度時間軸

- 2026-04-27 macOS 端：M3-① `screen resolve` 完成、M3-③ `create` 完成。
- 2026-04-27 macOS 端：嘗試實作 M3-② 策略 A（Algolia DocSearch），WebFetch 兩次驗證假設 → 不成立 → 擱置。
- **下一步：Windows 端驗證 search endpoint。**

## 已驗證為錯的假設

| 假設 | 驗證方式 | 結果 |
|---|---|---|
| developer.android.com 用 Algolia DocSearch（有公開 application_id / search-only api_key / index name） | WebFetch `https://developer.android.com/docs` | HTML 內找不到 `algolia` / `algolianet` 字樣，沒有 application_id / api_key |
| 搜尋結果頁 `/s/results?q=...` 是靜態 HTML，可以 scrape | WebFetch `https://developer.android.com/s/results?q=Activity` | 回傳空殼頁，搜尋結果由 JS 動態載入；靜態 fetch 看不到實際 API call |

**目前推測**（待 Windows 端證實或推翻）：

- 比較可能是 **Google Custom Search Engine / Programmable Search Engine**（畢竟 Google 不會付錢給 Algolia 搜自家網站）
- 或者是 **Google 內部搜尋**（沒對外 API，純頁面渲染）

## ⭐ 給 Windows 端的驗證任務

### 環境

- Windows + Chrome（或 Edge）+ DevTools
- 不需 clone repo（看完寫回 notes 即可），但建議先 `git pull origin main` 拉到 macOS 端剛 push 的 commit `b78ab2a`

### 步驟

1. 開 Chrome **無痕模式**（避免擴充 / cookies 干擾），按 `F12` 開 DevTools，切到 **Network** tab、勾選 **Preserve log** 與 **Disable cache**。
2. 進 `https://developer.android.com/`。
3. 在頁首搜尋框輸入 `Activity`，按 Enter。
4. 觀察 Network tab：
   - 過濾 `XHR / Fetch` 看是哪個 API call 取回搜尋結果
   - 用 `algolia` / `cse` / `search` / `googleapis` 過濾關鍵字逐一檢查
5. 點開最像「搜尋 API」的那筆，記錄：
   - **Request URL**（完整含 query string）
   - **Method**（GET / POST）
   - **Request Headers**（特別是 `X-Algolia-API-Key`、`X-Algolia-Application-Id`、`Authorization`、`X-Goog-Api-Key`）
   - **Request Payload**（POST body 的完整 JSON）
   - **Response**（前 30 行 JSON 結構，特別是結果條目的欄位名稱）
6. **Sources** tab：用 `Ctrl+Shift+F` 全域搜尋下列關鍵字，貼回找到的片段（前後各 5 行）：
   - `algolia`
   - `appId`
   - `apiKey`
   - `cx=`（Google CSE 識別碼）
   - `googleapis.com`
7. 試 `docs fetch` 那一面：抓任一參考頁如 `https://developer.android.com/reference/android/app/Activity`，確認：
   - 直接 `curl -s` / `httpx.get()` 能不能拿到完整內文？
   - 還是內文也是 JS 動態載入的（→ 靜態 fetch 拿到空殼）？

### 回報格式

請把結果寫進 **本檔案** 底下的 `## Windows 驗證結果（YYYY-MM-DD）` 區段，然後 commit + push（branch 用 `main` 即可，與 macOS 端不衝突）：

```
## Windows 驗證結果（2026-04-XX）

### 搜尋 API
- host:
- method:
- request URL（範例）:
- 必要 headers / API key:
- response schema（重點欄位）:

### Sources tab 找到的線索
- ...

### docs fetch 可行性
- 對 reference 頁 curl 結果：完整 / 空殼 / 部分
- ...

### 建議方案
- 從 B / B+ / C / D / E / C+B 混合 中挑一個，附理由。
```

## 候選方案（Windows 端回報後再挑）

| 選項 | 機制 | 優 | 缺 |
|---|---|---|---|
| **B** | `docs search "x"` 印出 `https://google.com/search?q=site:developer.android.com+x` 讓使用者點開 | 零依賴、零 API | 嚴格說不算搜尋 |
| **B+** | 同 B 但抓 Google 結果頁、parse 前 N 筆 | 真有結果 | Google 可能擋，無合約 |
| **C** | 只做 `docs fetch <url>`，不做 search | 最小但實用 | 沒搜尋能力 |
| **D** | 接 Google Programmable Search Engine API（環境變數帶 `GOOGLE_API_KEY` + CSE id） | 正規有合約 | 初始體驗差，使用者要去 Google Cloud 開 key |
| **E** | scrape `developer.android.com/s/results` HTML | 不需 API key | 動態 render，靜態 fetch 拿不到（已驗） |
| **C+B 混合** | `fetch` 做正事、`search` 印 Google `site:` URL 引導 | 簡單誠實 | — |
| **若 Windows 查到實際 endpoint** | 直接接那個 endpoint | 真實做事 | 看是否有公開 API key、是否有合約 |

**macOS 端目前傾向**：C+B 混合（無論 Windows 端查到什麼，這方案都能落地），但若 Windows 查到公開且穩定的 endpoint，可升級成那個。

## 實作骨架（Windows 確認方案後可參考）

預期檔案：

- `src/android_cli_mac_x86_community/commands/docs.py` — `docs.app` typer subapp，含 `search` / `fetch` 兩個 subcommand
- `src/android_cli_mac_x86_community/utils/docs.py` — 純函式：`search(query, limit) → list[dict]`、`fetch(url) → str`
- `tests/test_docs.py` — mock `httpx` 驗 URL 組裝、結果 parsing；CLI integration 測 stdout JSON
- `cli.py` 註冊 `app.add_typer(docs.app, name="docs", help="...")`

依賴：`httpx` 已在 `pyproject.toml`。HTML→text 若需要：
- 用 stdlib `html.parser`（最少依賴，但要自己處理）
- 加 `markdownify` 或 `html2text`（依方案而定）

## 不影響的事

- M3-① `screen resolve` 已完成（commit `17765c2`，pytest 45 passed）
- M3-③ `create` 已完成（commit `b78ab2a`，pytest 55 passed）
- 與 M3-② 互不相依，待 Windows 回報後再啟動 ②
