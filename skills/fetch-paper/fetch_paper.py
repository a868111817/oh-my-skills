#!/usr/bin/env python3
"""
ArXiv 論文搜尋
自動搜尋 arXiv 上與關鍵字相關的論文，輸出為 Markdown（含原文摘要）。
"""

import argparse
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


# ──────────────────────────────────────────────
# arXiv API 搜尋
# ──────────────────────────────────────────────

ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_NS = "{http://www.w3.org/2005/Atom}"


def search_arxiv(keyword: str, max_results: int = 5) -> list[dict]:
    """透過 arXiv API 搜尋論文，回傳論文清單。"""
    params = urllib.parse.urlencode({
        "search_query": f"all:{keyword}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            xml_data = resp.read()
    except Exception as exc:
        print(f"[錯誤] 無法連線至 arXiv API：{exc}", file=sys.stderr)
        sys.exit(1)

    root = ET.fromstring(xml_data)
    papers = []

    for entry in root.findall(f"{ARXIV_NS}entry"):
        arxiv_id_url = entry.findtext(f"{ARXIV_NS}id", "").strip()
        arxiv_id = arxiv_id_url.split("/abs/")[-1] if "/abs/" in arxiv_id_url else arxiv_id_url

        title = (entry.findtext(f"{ARXIV_NS}title") or "").strip().replace("\n", " ")
        abstract = (entry.findtext(f"{ARXIV_NS}summary") or "").strip().replace("\n", " ")
        published = (entry.findtext(f"{ARXIV_NS}published") or "")[:10]

        authors = [
            a.findtext(f"{ARXIV_NS}name", "")
            for a in entry.findall(f"{ARXIV_NS}author")
        ]

        pdf_link = ""
        for link in entry.findall(f"{ARXIV_NS}link"):
            if link.attrib.get("title") == "pdf":
                pdf_link = link.attrib.get("href", "")
                break
        if not pdf_link and arxiv_id:
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}"

        papers.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "published": published,
            "abstract": abstract,
            "url": arxiv_id_url,
            "pdf": pdf_link,
        })

    return papers


# ──────────────────────────────────────────────
# Markdown 輸出
# ──────────────────────────────────────────────

def build_markdown(keyword: str, papers: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# arXiv 論文搜尋結果",
        "",
        f"**搜尋關鍵字**：`{keyword}`  ",
        f"**搜尋時間**：{now}  ",
        f"**論文數量**：{len(papers)} 篇",
        "",
        "---",
        "",
    ]

    for i, paper in enumerate(papers, 1):
        authors_str = ", ".join(paper["authors"][:3])
        if len(paper["authors"]) > 3:
            authors_str += f" 等 {len(paper['authors'])} 位作者"

        lines += [
            f"## {i}. {paper['title']}",
            "",
            f"- **作者**：{authors_str}",
            f"- **發表日期**：{paper['published']}",
            f"- **arXiv 連結**：[{paper['id']}]({paper['url']})",
            f"- **PDF**：[下載]({paper['pdf']})",
            "",
            "### 原文摘要",
            "",
            f"> {paper['abstract']}",
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="搜尋 arXiv 論文並以繁體中文摘要輸出 Markdown"
    )
    parser.add_argument("keyword", help="搜尋關鍵字（支援英文或中文）")
    parser.add_argument(
        "-n", "--num", type=int, default=5,
        help="搜尋論文數量（預設：5，上限：20）"
    )
    parser.add_argument(
        "-o", "--output", default="",
        help="輸出 Markdown 檔案路徑（預設：自動命名）"
    )
    args = parser.parse_args()

    max_results = min(args.num, 20)

    print(f"[1/3] 正在搜尋 arXiv：關鍵字「{args.keyword}」，數量 {max_results} 篇...")
    papers = search_arxiv(args.keyword, max_results)

    if not papers:
        print("[警告] 未找到任何論文，請嘗試其他關鍵字。")
        sys.exit(0)

    print(f"  找到 {len(papers)} 篇論文")

    print("[2/2] 正在輸出 Markdown...")
    md_content = build_markdown(args.keyword, papers)

    output_dir = Path(__file__).parent.parent.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = output_dir / args.output
    else:
        safe_keyword = args.keyword.replace(" ", "_")[:30]
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = output_dir / f"{date_str}_{safe_keyword}.md"

    output_path.write_text(md_content, encoding="utf-8")
    print(f"\n完成！結果已儲存至：{output_path.resolve()}")


if __name__ == "__main__":
    main()
