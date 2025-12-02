# OpenAI Status Page Tracker

A scalable, event-based solution for tracking service status updates from OpenAI (and other services) using RSS feeds.

## Features

- **Event-based architecture**: Uses RSS feeds with HTTP caching headers (ETag, Last-Modified) to detect changes efficiently
- **Scalable design**: Async HTTP requests allow concurrent monitoring of 100+ status pages without blocking
- **Minimal bandwidth**: Only downloads feed content when it has actually changed
- **Clean output**: Parses HTML descriptions to extract status, message, and affected components

## Installation

```bash
pip install -r requirements.txt
```

Or install dependencies directly:

```bash
pip install aiohttp feedparser
```

## Usage

### Basic Usage

```bash
python status_tracker.py
```

This will start monitoring the OpenAI status page and print new incidents as they occur.

### Example Output

```
Starting status tracker for 1 feed(s)...
Poll interval: 30 seconds
============================================================
Performing initial feed sync...
Synced 85 existing incidents
Monitoring for new updates... (Press Ctrl+C to stop)
============================================================

[2025-11-03 14:32:00] Source: OpenAI
Product: Chat Completions, Responses
Incident: Elevated error rates on API
Status: Investigating - We are currently investigating elevated error rates
Link: https://status.openai.com/incidents/...
------------------------------------------------------------
```

### Adding More Status Pages

The tracker is designed to scale to 100+ feeds. Simply add more feeds in `main()`:

```python
tracker = StatusTracker(poll_interval=30)

# Add multiple status pages
tracker.add_feed("OpenAI", "https://status.openai.com/feed.rss")
tracker.add_feed("GitHub", "https://www.githubstatus.com/history.rss")
tracker.add_feed("Stripe", "https://status.stripe.com/history.rss")
tracker.add_feed("AWS", "https://status.aws.amazon.com/rss/all.rss")
tracker.add_feed("Cloudflare", "https://www.cloudflarestatus.com/history.rss")
# ... add more as needed
```

### Programmatic Usage

```python
import asyncio
from status_tracker import StatusTracker

async def monitor():
    tracker = StatusTracker(poll_interval=60)
    tracker.add_feed("OpenAI", "https://status.openai.com/feed.rss")
    await tracker.run()

asyncio.run(monitor())
```

## Design Decisions for Scalability

### Why RSS Feeds?

1. **Standard format**: Most status pages (Atlassian Statuspage, incident.io, etc.) provide RSS feeds
2. **Built-in caching**: RSS clients can use HTTP caching headers to avoid unnecessary downloads
3. **Lightweight**: Only incident data is transferred, not full HTML pages

### HTTP Caching Strategy

The tracker uses conditional HTTP requests:

- **ETag**: A unique identifier for the current version of the feed
- **Last-Modified**: Timestamp of when the feed was last updated

When polling, we send these headers:
```
If-None-Match: "abc123"
If-Modified-Since: Wed, 21 Oct 2025 07:28:00 GMT
```

If the feed hasn't changed, the server returns `304 Not Modified` with no body, saving bandwidth and processing time.

### Async Architecture

Using `aiohttp` with `asyncio.gather()` allows all feeds to be checked concurrently. This means checking 100 feeds takes roughly the same time as checking 1 feed (limited by the slowest response).

### Memory Efficiency

- Only stores incident IDs (not full content) to track seen incidents
- Uses dataclasses for clean, memory-efficient data structures

## Extending the Tracker

### Custom Incident Handlers

Modify `_display_incident()` to send to Slack, Discord, email, etc.:

```python
def _display_incident(self, incident: Incident) -> None:
    # Print to console
    print(f"[{incident.published}] {incident.title}")
    
    # Send to Slack
    # slack_client.post_message(channel="#alerts", text=str(incident))
    
    # Write to database
    # db.incidents.insert(incident.__dict__)
```

### Webhook Support

For true event-based updates without polling, some status pages support webhooks. You could extend this tracker to also receive webhook notifications when available.

## License

MIT
# bolna-assessment
