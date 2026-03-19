"""Tests for synchronous pub/sub event system."""

from __future__ import annotations

from autogenesis_core.events import Event, EventBus, EventType, get_event_bus


class TestEventType:
    def test_all_42_event_types_exist(self):
        expected = {
            "loop.execution.start",
            "loop.execution.iteration",
            "loop.execution.end",
            "tool.call.start",
            "tool.call.end",
            "model.call.start",
            "model.call.end",
            "token.budget.warning",
            "token.budget.exceeded",
            "prompt.version.change",
            "security.guardrail.alert",
            "context.window.truncation",
            "auth.token.refresh",
            "auth.login.success",
            "auth.login.failed",
            "twitter.session.start",
            "twitter.session.end",
            "twitter.browse.cycle",
            "twitter.draft.created",
            "twitter.draft.posted",
            "twitter.guardrail.violation",
            "twitter.injection.blocked",
            "twitter.auth.required",
            "employee.session.start",
            "employee.session.end",
            "employee.session.failed",
            "employee.session.timeout",
            "employee.message.sent",
            "employee.message.delivered",
            "employee.standup.posted",
            "employee.meeting.start",
            "employee.meeting.end",
            "employee.hired",
            "employee.fired",
            "employee.trained",
            "employee.union.proposal",
            "ceo.goal.start",
            "ceo.subtask.assign",
            "ceo.subtask.complete",
            "ceo.subtask.fail",
            "ceo.escalation",
            "ceo.goal.complete",
        }
        actual = {e.value for e in EventType}
        assert actual == expected
        assert len(EventType) == 42


class TestEvent:
    def test_event_is_pydantic_serializable(self):
        event = Event(event_type=EventType.LOOP_EXECUTION_START, data={"session": "abc"})
        data = event.model_dump_json()
        restored = Event.model_validate_json(data)
        assert restored.event_type == EventType.LOOP_EXECUTION_START
        assert restored.data == {"session": "abc"}
        assert restored.timestamp is not None

    def test_event_default_data(self):
        event = Event(event_type=EventType.TOOL_CALL_START)
        assert event.data == {}


class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe(EventType.LOOP_EXECUTION_START, received.append)

        event = Event(event_type=EventType.LOOP_EXECUTION_START, data={"iter": 1})
        bus.emit(event)

        assert len(received) == 1
        assert received[0].data == {"iter": 1}

    def test_multiple_handlers_fire(self):
        bus = EventBus()
        results_a: list[Event] = []
        results_b: list[Event] = []
        bus.subscribe(EventType.TOOL_CALL_END, results_a.append)
        bus.subscribe(EventType.TOOL_CALL_END, results_b.append)

        event = Event(event_type=EventType.TOOL_CALL_END, data={"tool": "bash"})
        bus.emit(event)

        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_unsubscribe_removes_handler(self):
        bus = EventBus()
        received: list[Event] = []

        def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe(EventType.MODEL_CALL_START, handler)
        bus.unsubscribe(EventType.MODEL_CALL_START, handler)

        bus.emit(Event(event_type=EventType.MODEL_CALL_START))

        assert len(received) == 0

    def test_handler_exception_does_not_crash(self):
        bus = EventBus()
        results: list[Event] = []

        def bad_handler(_event: Event) -> None:
            msg = "handler crashed"
            raise RuntimeError(msg)

        bus.subscribe(EventType.TOKEN_BUDGET_WARNING, bad_handler)
        bus.subscribe(EventType.TOKEN_BUDGET_WARNING, results.append)

        bus.emit(Event(event_type=EventType.TOKEN_BUDGET_WARNING))

        # Second handler still fires despite first raising
        assert len(results) == 1

    def test_emit_with_no_subscribers(self):
        bus = EventBus()
        # Should not raise
        bus.emit(Event(event_type=EventType.SECURITY_GUARDRAIL_ALERT))

    def test_different_event_types_isolated(self):
        bus = EventBus()
        start_events: list[Event] = []
        end_events: list[Event] = []
        bus.subscribe(EventType.LOOP_EXECUTION_START, start_events.append)
        bus.subscribe(EventType.LOOP_EXECUTION_END, end_events.append)

        bus.emit(Event(event_type=EventType.LOOP_EXECUTION_START))

        assert len(start_events) == 1
        assert len(end_events) == 0


class TestGetEventBus:
    def test_singleton_returns_same_instance(self):
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    def test_singleton_reset(self):
        bus1 = get_event_bus()
        get_event_bus.cache_clear()
        bus2 = get_event_bus()
        assert bus1 is not bus2
