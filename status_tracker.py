#!/usr/bin/env python3
import asyncio
import datetime as dt
import logging
import re
import sys
from typing import Optional, Tuple

import aiohttp
import xml.etree.ElementTree as ET

FEED_URL = "https://status.openai.com/history.atom"

PRODUCT_PATTERNS = [
    ("chat/completions", "OpenAI API - Chat Completions"),
    ("chat completions", "OpenAI API - Chat Completions"),
    ("responses api", "OpenAI API - Responses"),
    ("assistants api", "OpenAI API - Assistants"),
    ("realtime api", "OpenAI API - Realtime"),
    ("files api", "OpenAI API - Files"),
    ("file api", "OpenAI API - Files"),
    ("embeddings api", "OpenAI API - Embeddings"),
    ("embeddings", "OpenAI API - Embeddings"),
    ("fine-tuning api", "OpenAI API - Fine-tuning"),
    ("fine tuning api", "OpenAI API - Fine-tuning"),
    ("openai api", "OpenAI API"),
]


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_product_and_message(
    title: str, body: str
) -> Tuple[Optional[str], Optional[str]]:
    full_text = f"{title} {body}".lower()

    for needle, product_label in PRODUCT_PATTERNS:
        if needle in full_text:
            return product_label, body.strip() or title.strip()

    if "api" in full_text:
        return "OpenAI API", body.strip() or title.strip()

    return None, None


class AtomStatusWatcher:
    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

    def __init__(self, feed_url: str, poll_interval_seconds: int = 60) -> None:
        self.feed_url = feed_url
        self.poll_interval = poll_interval_seconds
        self.etag: Optional[str] = None
        self.last_modified: Optional[str] = None
        self.seen_keys: set[str] = set()

    async def run_forever(self) -> None:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    changed = await self._check_once(session)
                    await asyncio.sleep(self.poll_interval)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logging.exception("Error while polling feed: %s", exc)
                    await asyncio.sleep(self.poll_interval)

    async def _fetch_if_changed(self, session: aiohttp.ClientSession) -> Optional[str]:
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag
        if self.last_modified:
            headers["If-Modified-Since"] = self.last_modified

        async with session.get(self.feed_url, headers=headers) as resp:
            if resp.status == 304:
                return None

            resp.raise_for_status()
            self.etag = resp.headers.get("ETag", self.etag)
            self.last_modified = resp.headers.get("Last-Modified", self.last_modified)
            return await resp.text()

    async def _check_once(self, session: aiohttp.ClientSession) -> bool:
        xml_text = await self._fetch_if_changed(session)
        if xml_text is None:
            return False

        root = ET.fromstring(xml_text)
        changed = False

        entries = root.findall("atom:entry", self.ATOM_NS)
        entries.reverse()

        for entry in entries:
            entry_id = entry.findtext("atom:id", default="", namespaces=self.ATOM_NS)
            updated = entry.findtext("atom:updated", default="", namespaces=self.ATOM_NS)
            key = f"{entry_id}|{updated}"

            if not entry_id or not updated:
                key = entry_id or updated or ""
                if key in self.seen_keys:
                    continue
            else:
                if key in self.seen_keys:
                    continue

            self.seen_keys.add(key)
            changed = True

            title = entry.findtext("atom:title", default="", namespaces=self.ATOM_NS)
            summary = entry.findtext("atom:summary", default="", namespaces=self.ATOM_NS)
            content = entry.findtext("atom:content", default="", namespaces=self.ATOM_NS)

            body_raw = summary or content or title or ""
            body_clean = strip_html(body_raw)

            product, message = detect_product_and_message(title, body_clean)
            if product and message:
                self._print_event(product, message)

        return changed

    @staticmethod
    def _print_event(product: str, message: str) -> None:
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] Product: {product}")
        print(f"Status: {message}")
        print("-" * 80, flush=True)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    watcher = AtomStatusWatcher(FEED_URL, poll_interval_seconds=60)
    await watcher.run_forever()


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        print("Python 3.10+ recommended.", file=sys.stderr)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
