# M3-② `docs search` / `docs fetch` — 研究筆記

## 狀態

**擱置中（2026-04-27）。** 原訂策略 A（Algolia DocSearch）前提錯誤；換策略前先在 Windows 桌機用 DevTools 查清楚 developer.android.com 的實際搜尋後端。

## 已嘗試

| 動作 | 結果 |
|---|---|
| WebFetch `https://developer.android.com/docs` | HTML 找不到 Algolia application_id / api_key / index name，沒有 `algolia` 或 `algolianet` 字樣 |
| WebFetch `https://developer.android.com/s/results?q=Activity` | 回傳的是空殼頁，搜尋結果由 JS 動態載入；靜態 fetch 看不到實際呼叫的 API endpoint |

**結論**：developer.android.com 的搜尋大機率不是 Algolia DocSearch（合理 — Google 不會付給 Algolia 搜自己的網站）。更可能是：

- Google Custom Search Engine / Programmable Search Engine
- 或 Google 內部搜尋（沒對外 API）

## 待查（Windows 桌機 + Chrome DevTools）

1. 打開 `https://developer.android.com/`，搜尋框輸入 `Activity` 按 Enter
2. DevTools → Network tab，看送出的 request：
   - host 是 `cse.google.com` / `*.googleapis.com` / 其他？
   - GET 還是 POST？query string 結構？
   - 回傳是 JSON 還是 HTML？
3. Sources tab 找 search engine ID（CX）或 API key 線索
4. 若是 Google Programmable Search Engine：
   - 公開的 CX 編號？
   - 是否需要 Google Cloud API key？

## 候選方案（待 Windows 端查清楚後再定）

| 選項 | 機制 | 優 | 缺 |
|---|---|---|---|
| **B** | `docs search "x"` 印出 `https://google.com/search?q=site:developer.android.com+x` 讓使用者點開 | 零依賴、零 API | 嚴格說不算搜尋 |
| **B+** | 同 B 但抓 Google 結果頁、parse 前 N 筆 | 真有結果 | Google 可能擋，無合約 |
| **C** | 只做 `docs fetch <url>`，不做 search | 最小但實用 | 沒搜尋能力 |
| **D** | 接 Google Programmable Search Engine API（環境變數帶 API key + CSE id） | 正規有合約 | 初始體驗差 |
| **E** | scrape `developer.android.com/s/results` HTML | 不需 API key | 動態 render，靜態 fetch 拿不到 |
| **C+B 混合** | `fetch` 做正事，`search` 印 Google `site:` URL 引導 | 簡單誠實 | — |

**目前傾向**：C+B 混合（最不容易踩雷），但等 Windows 端查實際 endpoint 後再決定。

## 不影響的事

- M3-① `screen resolve` 已完成（commit `17765c2`，pytest 45 passed）
- M3-③ `create`（scaffold 範本 + `gradle wrapper`）可在 ② 釐清前先做，與 ② 互不依賴
