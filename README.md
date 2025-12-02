
# OpenAI Status Watcher

A lightweight Python script that automatically detects and logs live incident updates from the **OpenAI Status Page**, without relying on manual refresh or inefficient polling.

---

## Features

- Detects new incidents, outages, and degradation updates.
- Identifies the affected OpenAI API product (Chat Completions, Responses API, etc.).
- Efficient update tracking using `ETag` and `Last-Modified` headers (conditional GET).
- Logs each incident update only once.
- Console output only — no database or UI required.

---

## Example Output


[2025-11-03 14:32:00] Product: OpenAI API - Chat Completions
Status: Degraded performance due to upstream issue
--------------------------------------------------


---

## Requirements

- Python **3.10+**
- Install dependency:

```bash
pip install aiohttp
````

---

## Run

```bash
python openai_status_watcher.py
```

The script remains running and prints updates automatically as the status feed changes.

---

## Scaling

The architecture supports tracking 100+ status feeds by running multiple watchers concurrently with `asyncio.gather` while still minimizing network calls via conditional requests.

---
