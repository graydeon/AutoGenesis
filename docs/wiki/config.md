# Configuration

## 6-Layer Cascade (later overrides earlier)

| Layer | Source | Path |
|-------|--------|------|
| 1 | Defaults | Built into Pydantic models |
| 2 | System | `/etc/autogenesis/config.yaml` |
| 3 | User | `$XDG_CONFIG_HOME/autogenesis/config.yaml` |
| 4 | Project | `.autogenesis/config.yaml` (walks up from cwd) |
| 5 | Environment | `AUTOGENESIS_*` vars (`__` = nesting separator) |
| 6 | CLI flags | Per-command flags |

## All Config Fields

```yaml
codex:
  model: "gpt-5.3-codex"
  api_base_url: "https://api.openai.com/v1"
  timeout: 300.0
  max_retries: 3

tokens:
  max_tokens_per_session: 500000
  max_tokens_per_day: 5000000

security:
  guardrails_enabled: true

twitter:
  enabled: false
  active_hours_start: "09:00"
  active_hours_end: "17:00"
  timezone: "America/New_York"
  session_interval_minutes: 30
  max_drafts_per_session: 10
  queue_path: ""
  worldview_path: ""
  gateway_url: "http://127.0.0.1:1456"
  selectors_path: ""

employees:
  enabled: false
  global_roster_path: ""
  standup_enabled: true
  standup_time: "09:00"
  standup_timezone: "America/New_York"
  max_meeting_rounds: 3
  brain_memory_limit: 1000
  brain_context_limit: 20
  changelog_context_limit: 10
  dispatch_timeout: 300.0

gitnexus:
  enabled: true
  binary: "gitnexus"
  auto_index: true
  query_limit: 3
  max_context_chars: 3000
  command_timeout_seconds: 20.0
  index_timeout_seconds: 600.0

credential_provider: "env"   # env | file | gateway
credential_path: ""
```

## Environment Variable Override Examples

```bash
AUTOGENESIS_CODEX__MODEL=gpt-4o              # codex.model
AUTOGENESIS_EMPLOYEES__ENABLED=true          # employees.enabled
AUTOGENESIS_TWITTER__GATEWAY_URL=http://...  # twitter.gateway_url
AUTOGENESIS_GITNEXUS__ENABLED=true           # gitnexus.enabled
AUTOGENESIS_CREDENTIAL_PROVIDER=gateway      # credential_provider
```

Pattern: `AUTOGENESIS_` prefix + `__` for nesting + uppercase field name.

## Credential Providers

| Provider | Source | Use case |
|----------|--------|----------|
| `env` | `AUTOGENESIS_ACCESS_TOKEN` env var | Local dev |
| `file` | `~/.local/share/autogenesis/auth.json` | After `autogenesis login` |
| `gateway` | `/run/autogenesis/credentials.json` | VM mode (host-mounted) |
