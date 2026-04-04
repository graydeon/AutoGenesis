from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Static

if TYPE_CHECKING:
    from textual.app import ComposeResult
    from textual.events import Click


class InputBar(Widget):
    """Bottom bar: target dropdown + text input."""

    DEFAULT_CSS = """
    InputBar {
        height: 3;
        layout: horizontal;
        background: $surface;
        padding: 0 1;
    }
    InputBar #target-label {
        width: 18;
        height: 1;
        color: $secondary;
        margin: 1 1 0 0;
        text-style: bold;
    }
    InputBar Input {
        width: 1fr;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+space", "toggle_target_menu", "Switch target", show=False),
    ]

    target: reactive[str] = reactive("CEO")

    class Submitted(Message):
        def __init__(self, target: str, text: str) -> None:
            super().__init__()
            self.target = target
            self.text = text

    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = ["CEO"]
        self._target_index: int = 0

    def compose(self) -> ComposeResult:
        yield Static("[ CEO ▾ ]", id="target-label")
        yield Input(placeholder="type a message...", id="chat-input")

    def load_targets(self, targets: list[str]) -> None:
        self.targets = list(targets)
        if "CEO" not in self.targets:
            self.targets.insert(0, "CEO")

    def set_target(self, target: str) -> None:
        self.target = target
        self.query_one("#target-label", Static).update(f"[ {target} ▾ ]")

    def action_toggle_target_menu(self) -> None:
        if not self.targets:
            return
        self._target_index = (self._target_index + 1) % len(self.targets)
        self.set_target(self.targets[self._target_index])

    def on_static_click(self, event: Click) -> None:
        """Clicking the target label cycles through available targets."""
        self.action_toggle_target_menu()
        event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if text:
            self.post_message(self.Submitted(target=self.target, text=text))
            event.input.value = ""
