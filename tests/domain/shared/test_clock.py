"""Test cases for Clock abstraction."""

from datetime import datetime

import pytest

from dddpy.domain.shared.clock import Clock, SystemClock, FixedClock


def test_system_clock_returns_current_time():
    """Test that SystemClock returns current time."""
    clock = SystemClock()

    # Get time before and after calling clock.now()
    before = datetime.now()
    current = clock.now()
    after = datetime.now()

    # The time returned should be between before and after
    assert before <= current <= after


def test_fixed_clock_returns_fixed_time():
    """Test that FixedClock returns the fixed time."""
    fixed_time = datetime(2023, 1, 1, 12, 0, 0)
    clock = FixedClock(fixed_time)

    # Should always return the same fixed time
    assert clock.now() == fixed_time
    assert clock.now() == fixed_time


def test_fixed_clock_consistency():
    """Test that FixedClock is consistent across multiple calls."""
    fixed_time = datetime(2023, 6, 15, 14, 30, 45)
    clock = FixedClock(fixed_time)

    # Multiple calls should return the same time
    times = [clock.now() for _ in range(10)]
    assert all(t == fixed_time for t in times)


class MockClock(Clock):
    """Mock Clock implementation for testing."""

    def __init__(self, return_time: datetime):
        self.return_time = return_time

    def now(self) -> datetime:
        return self.return_time


def test_clock_is_abstract():
    """Test that Clock cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Clock()  # Should raise TypeError because it's abstract


def test_mock_clock_implementation():
    """Test that custom Clock implementations work correctly."""
    test_time = datetime(2023, 12, 25, 9, 30, 0)
    mock_clock = MockClock(test_time)

    assert mock_clock.now() == test_time
