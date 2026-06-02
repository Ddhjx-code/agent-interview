"""Fetch web content from Agent-Learning-Hub referenced URLs.

Scrapes official docs, GitHub READMEs, arxiv papers, and blog posts,
saves them as .md files with topic classification for indexing.

Usage:
    python -m interview_rag_server.knowledge_base.fetch_web_sources
"""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import html2text
import requests
from bs4 import BeautifulSoup


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
HUB_README = WORKSPACE_ROOT / "Agent-Learning-Hub" / "README.md"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WEB_SOURCES_DIR = DATA_DIR / "web_sources"
MAPPING_FILE = DATA_DIR / "web_source_mapping.json"

SKIP_DOMAINS = {"img.shields.io", "xiaohongshu.com"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SECTION_TOPIC_MAP = {
    "Stage 0": "agent",
    "Stage 1": "agent",
    "Stage 2": "rag",
    "Stage 3": "engineering",
    "Stage 4": "multi-agent",
    "Stage 5": "engineering",
    "Stage 6": "agent",
    "Stage 7": "evaluation",
    "Stage 8": "engineering",
    "Project Ladder": "engineering",
    "Official Guides": "engineering",
    "Project Map": "agent",
    "Skills, Protocols": "engineering",
    "Modern Agent": "agent",
    "Legacy": "agent",
    "Papers": "agent",
    "GitHub Repositories": "agent",
    "Thoughtful Blogs": "agent",
    "Claude Code Study": "engineering",
    "Learning Principles": "agent",
}

URL_TOPIC_OVERRIDES = {
    "anthropic.com/engineering/building-effective-agents": "agent",
    "openai.com/business/guides-and-resources": "agent",
    "docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview": "engineering",
    "docs.anthropic.com/en/docs/agents-and-tools/tool-use/computer-use": "agent",
    "code.claude.com": "engineering",
    "modelcontextprotocol.io": "engineering",
    "google-a2a.github.io": "engineering",
    "agentclientprotocol.com": "engineering",
    "platform.openai.com/docs/guides/function-calling": "engineering",
    "platform.openai.com/docs/guides/agents-sdk": "agent",
    "platform.openai.com/docs/guides/evals": "evaluation",
    "docs.llamaindex.ai": "rag",
    "docs.langchain.com": "rag",
    "docs.smith.langchain.com": "evaluation",
    "lilianweng.github.io": "agent",
    "arxiv.org/abs/2210.03629": "agent",
    "arxiv.org/abs/2302.04761": "agent",
    "arxiv.org/abs/2303.11366": "agent",
    "arxiv.org/abs/2304.03442": "memory",
    "arxiv.org/abs/2305.16291": "agent",
    "arxiv.org/abs/2307.13854": "agent",
    "arxiv.org/abs/2308.03688": "evaluation",
    "arxiv.org/abs/2308.08155": "multi-agent",
    "arxiv.org/abs/2310.06770": "evaluation",
    "arxiv.org/abs/2405.15793": "engineering",
    "arxiv.org/abs/2604.14228": "engineering",
    "arxiv.org/abs/2604.17460": "engineering",
    "arxiv.org/abs/2605.13357": "engineering",
    "arxiv.org/abs/2602.08004": "engineering",
    "arxiv.org/abs/2602.14690": "engineering",
    "arxiv.org/abs/2603.15401": "engineering",
    "arxiv.org/abs/2604.04759": "engineering",
    "arxiv.org/abs/2401.13649": "agent",
    "github.com/mem0ai": "memory",
    "github.com/letta-ai": "memory",
    "github.com/khoj-ai": "rag",
    "github.com/infiniflow": "rag",
    "github.com/Mintplex-Labs": "rag",
    "github.com/onyx-dot-app": "rag",
    "github.com/assafelovic": "rag",
    "github.com/langchain-ai/open_deep_research": "rag",
    "github.com/stanford-oval": "rag",
    "github.com/browser-use": "agent",
    "github.com/bytedance/UI-TARS": "agent",
    "github.com/NirDiamant": "agent",
    "github.com/microsoft/ai-agents": "agent",
    "pydantic.dev": "engineering",
    "google.github.io/adk-docs": "engineering",
    "blog.langchain.com": "engineering",
    "docs.crewai.com": "multi-agent",
    "microsoft.github.io/autogen": "multi-agent",
}


def _url_to_filename(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:10]
    parsed = urlparse(url)
    domain = parsed.netloc.replace(".", "_")
    path_slug = parsed.path.strip("/").replace("/", "_")[:60]
    return f"{domain}__{path_slug}__{h}.md"


def _classify_url(url: str, section_context: str) -> str:
    for pattern, topic in URL_TOPIC_OVERRIDES.items():
        if pattern in url:
            return topic
    for section_key, topic in SECTION_TOPIC_MAP.items():
        if section_key.lower() in section_context.lower():
            return topic
    return "agent"


def _classify_source_type(url: str) -> str:
    if "arxiv.org" in url:
        return "paper"
    if "github.com" in url:
        return "github"
    if any(d in url for d in ["docs.", "code.claude", "platform.openai", "google.github.io",
                               "modelcontextprotocol", "agentclientprotocol", "pydantic.dev"]):
        return "docs"
    return "blog"


def extract_urls_with_context(readme_path: Path) -> list[dict]:
    content = readme_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    results = []
    current_section = ""

    for line in lines:
        if line.startswith("#"):
            current_section = line.lstrip("#").strip()

        urls = re.findall(r'https?://[^\s\)\]]+', line)
        for url in urls:
            url = url.rstrip(".,;:!?")
            parsed = urlparse(url)
            if parsed.netloc in SKIP_DOMAINS:
                continue
            if parsed.netloc == "github.com" and url.count("/") <= 3:
                continue

            title_match = re.search(r'\[([^\]]+)\]\(' + re.escape(url), line)
            title = title_match.group(1) if title_match else ""

            results.append({
                "url": url,
                "title": title,
                "section": current_section,
                "topic": _classify_url(url, current_section),
                "source_type": _classify_source_type(url),
            })

    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)

    return deduped


def fetch_arxiv(url: str) -> Optional[str]:
    arxiv_id = url.split("/abs/")[-1]
    api_url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")
        entry = soup.find("entry")
        if not entry:
            return None
        title = entry.find("title").get_text(strip=True) if entry.find("title") else ""
        summary = entry.find("summary").get_text(strip=True) if entry.find("summary") else ""
        authors = [a.find("name").get_text(strip=True) for a in entry.find_all("author")]
        return f"# {title}\n\nAuthors: {', '.join(authors)}\n\nArXiv: {url}\n\n## Abstract\n\n{summary}\n"
    except Exception as e:
        print(f"  [WARN] arxiv fetch failed for {url}: {e}")
        return None


def fetch_github_readme(url: str) -> Optional[str]:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2:
        return None
    owner, repo = parts[0], parts[1]

    if len(parts) > 2 and parts[2] == "blob":
        file_path = "/".join(parts[4:])
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{parts[3]}/{file_path}"
    else:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"

    try:
        resp = requests.get(raw_url, headers=HEADERS, timeout=30)
        if resp.status_code == 404:
            raw_url = raw_url.replace("/main/", "/master/")
            resp = requests.get(raw_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  [WARN] GitHub fetch failed for {url}: {e}")
        return None


def fetch_web_page(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.body_width = 0
        return converter.handle(resp.text)
    except Exception as e:
        print(f"  [WARN] web fetch failed for {url}: {e}")
        return None


def fetch_url_content(url: str, source_type: str) -> Optional[str]:
    if source_type == "paper":
        return fetch_arxiv(url)
    if source_type == "github":
        return fetch_github_readme(url)
    return fetch_web_page(url)


def main():
    if not HUB_README.exists():
        alt = WORKSPACE_ROOT.parent / "Agent-Learning-Hub" / "README.md"
        if alt.exists():
            hub_readme = alt
        else:
            print(f"ERROR: Agent-Learning-Hub README not found at {HUB_README}")
            print("Please clone: git clone https://github.com/datawhalechina/Agent-Learning-Hub.git")
            return
    else:
        hub_readme = HUB_README

    print("=" * 60)
    print("Fetching web sources from Agent-Learning-Hub")
    print("=" * 60)

    WEB_SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Extracting URLs from README...")
    url_entries = extract_urls_with_context(hub_readme)
    print(f"  Found {len(url_entries)} unique URLs")

    print("\n[2/3] Fetching content...")
    mapping = []
    success_count = 0

    for i, entry in enumerate(url_entries):
        url = entry["url"]
        filename = _url_to_filename(url)
        filepath = WEB_SOURCES_DIR / filename

        if filepath.exists() and filepath.stat().st_size > 100:
            print(f"  [{i+1}/{len(url_entries)}] [CACHED] {url[:80]}")
            mapping.append({
                "url": url,
                "title": entry["title"],
                "topic": entry["topic"],
                "source_type": entry["source_type"],
                "section": entry["section"],
                "file": str(filepath.relative_to(DATA_DIR)),
            })
            success_count += 1
            continue

        print(f"  [{i+1}/{len(url_entries)}] [{entry['source_type'].upper()}] {url[:80]}")
        content = fetch_url_content(url, entry["source_type"])

        if content and len(content.strip()) > 50:
            header = f"---\nurl: {url}\ntitle: {entry['title']}\ntopic: {entry['topic']}\nsource_type: {entry['source_type']}\n---\n\n"
            filepath.write_text(header + content, encoding="utf-8")
            mapping.append({
                "url": url,
                "title": entry["title"],
                "topic": entry["topic"],
                "source_type": entry["source_type"],
                "section": entry["section"],
                "file": str(filepath.relative_to(DATA_DIR)),
            })
            success_count += 1
        else:
            print(f"    → No content or too short, skipping")

        time.sleep(0.5)

    print(f"\n[3/3] Saving mapping ({success_count}/{len(url_entries)} URLs)...")
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump({"sources": mapping}, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {success_count} sources saved to {WEB_SOURCES_DIR}")
    print(f"Mapping saved to {MAPPING_FILE}")

    by_topic = {}
    for m in mapping:
        by_topic.setdefault(m["topic"], []).append(m)
    print("\nBy topic:")
    for topic, items in sorted(by_topic.items()):
        print(f"  {topic}: {len(items)} sources")


if __name__ == "__main__":
    main()
