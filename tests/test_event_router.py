"""Test event router."""
import time

import pytest

from swak.event_router import EventRouter
from swak.plugin import DummyOutput
from swak.plugins.filter.ref_filter import Filter


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


@pytest.fixture()
def filter():
    """Create filter plugin and returns it."""
    return Filter([("k", "V")])


@pytest.fixture()
def output():
    """Create default output and returns it."""
    return DummyOutput()


def test_event_router(def_output, filter, output):
    """Test event router."""
    # router with only default output.
    event_router = EventRouter(def_output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(def_output.events['test']) == 1

    # router with an output
    def_output.reset()
    event_router = EventRouter(def_output)
    event_router.add_rule("test", output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 1

    # router with reform & output.
    output.reset()
    assert len(output.events['test']) == 0
    event_router = EventRouter(def_output)
    event_router.add_rule("test", filter)
    event_router.add_rule("test", output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 0
