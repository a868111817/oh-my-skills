---
name: youtube-transcript
description: >
  Fetches YouTube video transcripts/subtitles using yt-dlp and saves them as Markdown files in a local `video/` folder.
  If the transcript is in a foreign language (not Chinese), automatically translates it to Traditional Chinese (Taiwan).
  Use this skill whenever the user shares a YouTube URL or video ID and wants to: extract transcript/subtitles,
  get a summary or text from a video, save video content locally, or translate YouTube content to Chinese.
  Trigger even if the user says things like "幫我抓這個影片的內容", "把這個 YouTube 抄下來", "transcript",
  "字幕", "影片文字", "影片內容", "download subtitles", or pastes a youtu.be / youtube.com link.
---

# YouTube 字幕擷取 Skill

使用 yt-dlp 自動抓取 YouTube 影片字幕，翻譯外文為台灣繁體中文，並儲存為 Markdown 檔案。

## 流程

### Step 1：執行擷取腳本

執行 `scripts/fetch_transcript.py`，傳入使用者提供的 YouTube URL 或影片 ID：

```bash
python <skill-dir>/scripts/fetch_transcript.py "<youtube_url_or_id>" --output-dir video
```

支援的額外參數：
- `--proxy http://127.0.0.1:7890`：使用代理伺服器（IP 被封鎖時）
- `--cookies /path/to/cookies.txt`：附帶瀏覽器 cookies（搭配 proxy 效果更好）

腳本輸出 JSON，正常情況包含：
- `error`：`false`
- `video_id`、`title`、`language`、`is_foreign`、`is_auto_generated`
- `plain_text`：純文字字幕（適合翻譯）
- `timestamped`：含時間戳記的字幕（格式：`[MM:SS] 文字`）
- `safe_title`：已清理特殊字元的標題（用於檔名）
- `date`：今天日期

若發生錯誤，JSON 會包含 `"error": true`、`error_type`、`message`、`hints`（繞過建議清單）。

字幕優先順序：手動中文字幕（zh-TW > zh > zh-CN）→ 其他手動字幕 → 自動生成中文字幕 → 其他自動生成字幕

### Step 2：翻譯（如需要）

若 `is_foreign` 為 `true`，將 `plain_text` 翻譯為**台灣繁體中文**。

翻譯注意事項：
- 保留專有名詞原文，並在後加中文對照，例如：`Claude（克勞德）`
- 維持自然的台灣用語（「軟體」不用「软件」、「網路」不用「网络」）
- 意譯為主，讓中文讀起來通順自然
- 保留段落結構

### Step 3：摘要整部影片

根據翻譯後的文字（或原始中文字幕），以**台灣繁體中文**撰寫影片摘要。

摘要注意事項：
- 長度約 200～400 字，涵蓋影片核心主題與重點
- 以條列式呈現主要論點或段落重點（3～7 點）
- 保留重要專有名詞（附原文）
- 不加入字幕原文沒有的內容，忠實反映影片內容

### Step 4：建立 Markdown 檔案

輸出目錄為使用者工作目錄下的 `video/`（不存在則建立）。

檔名格式：`{date}_{safe_title}.md`

```markdown
# {影片標題}

- **影片連結**：https://www.youtube.com/watch?v={video_id}
- **原始語言**：{language}（若為外文則加上「已翻譯為繁體中文」）
- **字幕類型**：{手動字幕 / 自動生成字幕}
- **擷取日期**：{date}

---

## 摘要

{200～400 字的影片重點摘要，條列主要論點}

---

## 內容

{翻譯後的文字，或原始中文字幕（timestamped 格式）}

---

## 原文字幕（含時間戳記）

{若原文為外文，保留 timestamped 原文；若原文為中文則省略此區塊}
```

### Step 5：確認完成

告訴使用者：儲存路徑、影片標題、原始語言、是否翻譯、字幕大約字數。

### 發生錯誤時

若腳本輸出 `"error": true`，根據 `error_type` 給使用者清楚說明：

**`ip_blocked`（最常見）：IP 被 YouTube 限速**

告知使用者並展示 `hints` 中的繞過方式：
1. **等待**：5～15 分鐘後重試
2. **Proxy**：加上 `--proxy http://<位址>:<埠>` 參數
3. **Cookies + Proxy**：在 Chrome 安裝「Get cookies.txt LOCALLY」擴充功能，匯出 `cookies.txt`，加上 `--cookies /path/to/cookies.txt`（注意：單獨使用 cookies 無法繞過 IP 層級的 429 封鎖，需搭配 proxy）
4. **手動**：YouTube 頁面點「…」→「開啟逐字稿」手動複製

**`no_transcript`**：影片無字幕，可能尚未生成，建議稍後再試

**`private_video`**：私人影片，無法存取

**`invalid_url`**：URL 格式不正確（支援：youtube.com/watch?v=xxx、youtu.be/xxx、11 碼 ID）

每種錯誤都應將 `hints` 陣列以條列方式呈現給使用者。

## 注意事項

- 腳本會自動安裝所需的 Python 套件（`yt-dlp`）
- `video/` 資料夾位置以使用者**當前工作目錄**為基準
- yt-dlp 同時支援手動字幕與 YouTube 自動生成字幕
