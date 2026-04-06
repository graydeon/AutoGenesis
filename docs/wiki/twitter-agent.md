# Twitter Agent

## Architecture

```
Pinchtab MCP → TwitterBrowser → browse_feed() → tweets
                                                    ↓
                                          PreEngagementFilter → filtered tweets
                                                    ↓
                                          Codex agent reasons about tweets
                                                    ↓
                                          TwitterPostTool → ConstitutionalCheck → QueueManager
                                                    ↓
                                          Human approves via approval queue
                                                    ↓
                                          TwitterPoster → Gateway → Twitter API
```

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `TwitterBrowser` | `browser.py` | Pinchtab MCP wrapper, browse_feed with scroll + dedup |
| `PreEngagementFilter` | `guardrails.py` | Block injection, hate speech, off-topic |
| `ConstitutionalCheck` | `guardrails.py` | Check for identity leaks (4 regex patterns) |
| `QueueManager` | `queue.py` | SQLite draft queue: pending → approved → posted |
| `TwitterPoster` | `poster.py` | HTTP client to gateway, exponential backoff retry |
| `GatewayHandler` | `gateway.py` | HTTP server signing tweets with real API creds |
| `TwitterScheduler` | `scheduler.py` | Permission gate, active hours, cycle loop |
| `WorldviewManager` | `worldview.py` | Emergent opinions/topics/people tracking |
| `tweet parser` | `parser.py` | Extract tweets from page text, detect injection |

## Tweet Lifecycle

1. **Browse**: Scheduler triggers `browser.browse_feed()` via Pinchtab
2. **Filter**: `PreEngagementFilter.should_engage()` — blocks injection attempts, hate speech, off-topic
3. **Reason**: Codex agent decides which tweets to engage with, drafts responses
4. **Constitutional check**: `ConstitutionalCheck` verifies no identity leaks before queuing
5. **Queue**: Draft saved to `twitter_queue.db` (status: pending)
6. **Approve**: Human reviews in approval queue (approve/reject/edit)
7. **Post**: Scheduler posts approved items via `TwitterPoster` → Gateway → Twitter API

## Prompt Injection Defense (3 layers)

1. **Structured extraction** — `parser.py` extracts tweets via line-by-line state machine, not raw text
2. **Tagged boundaries** — `format_tweet_for_llm()` wraps content in `[UNTRUSTED_TWEET_CONTENT]` tags
3. **Constitutional self-check** — `ConstitutionalCheck` regex scans for identity leak patterns

## Gateway

Runs on a configurable host/port (set `AUTOGENESIS_TWITTER__GATEWAY_URL`). Requires Twitter API credentials via environment variables:

- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_SECRET`
- `TWITTER_BEARER_TOKEN`

```bash
python -m autogenesis_twitter.gateway --gateway-token <token>
```

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (`{"status": "ok"}`) |
| `/twitter/tweet` | POST | Sign and forward tweet to Twitter API |

Auth: Bearer token in `Authorization` header (matches `--gateway-token`).

Register the gateway in your service manager if you use one.

## Scheduler

```bash
autogenesis twitter start   # foreground, Ctrl+C to stop
```

- Checks `twitter.enabled` config
- Runs only during `active_hours_start` — `active_hours_end` (configurable timezone)
- Cycles at `session_interval_minutes` intervals
- Posts approved queue items each cycle
- Browser requires Pinchtab MCP (uses null browser fallback if unavailable)

## Config

```yaml
twitter:
  enabled: false
  active_hours_start: "09:00"
  active_hours_end: "17:00"
  timezone: "America/New_York"
  session_interval_minutes: 30
  max_drafts_per_session: 10
  gateway_url: ""                # set to your gateway's URL, e.g. "http://127.0.0.1:1456"
  queue_path: ""           # defaults to $XDG_STATE_HOME/autogenesis/twitter_queue.db
  worldview_path: ""       # defaults to $XDG_STATE_HOME/autogenesis/twitter_worldview.json
  selectors_path: ""       # CSS/aria selectors for Pinchtab
```

## Approval Queue Integration

Any dashboard or admin UI can read the tweet queue directly from the SQLite DB:
- API endpoints to implement: `GET /api/twitter/queue`, `POST /api/twitter/queue/{id}/approve`, etc.
- Reads same SQLite DB as QueueManager
- DB path configurable via `AUTOGENESIS_TWITTER_QUEUE_DB` env var
