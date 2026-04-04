from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


class StatusBar(Widget):
    """Top bar: app name, model, connection state, token count."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        layout: horizontal;
        background: $surface;
        padding: 0 1;
    }
    StatusBar Label {
        margin: 0 2 0 0;
    }
    StatusBar #title {
        color: $primary;
        text-style: bold;
    }
    """

    session_tokens: reactive[int] = reactive(0)
    connection_state: reactive[str] = reactive("connecting")
    model_name: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Label("⬡ AutoGenesis", id="title")
        yield Label("", id="model-label")
        yield Label("● connecting", id="conn-label")
        yield Label("0 tokens", id="token-label")

    def watch_session_tokens(self, tokens: int) -> None:
        self.query_one("#token-label", Label).update(f"{tokens:,} tokens")

    def watch_connection_state(self, state: str) -> None:
        symbol = "●" if state == "connected" else "⟳" if state in ("connecting", "reconnecting") else "○"
        self.query_one("#conn-label", Label).update(f"{symbol} {state}")

    def watch_model_name(self, name: str) -> None:
        if name:
            self.query_one("#model-label", Label).update(name)

    def update_tokens(self, tokens: int) -> None:
        self.session_tokens = tokens

    def update_connection(self, state: str, model: str = "") -> None:
        self.connection_state = state
        if model:
            self.model_name = model
