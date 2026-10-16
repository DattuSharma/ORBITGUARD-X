
from src.sequence_guard import SequenceGuard


def test_first_sequence_is_accepted():
    guard = SequenceGuard()
    assert guard.check("SIM-01", 1)["accepted"] is True


def test_increasing_sequence_is_accepted():
    guard = SequenceGuard()
    guard.check("SIM-01", 1)
    assert guard.check("SIM-01", 2)["accepted"] is True


def test_duplicate_sequence_is_rejected():
    guard = SequenceGuard()
    guard.check("SIM-01", 5)
    result = guard.check("SIM-01", 5)
    assert result["accepted"] is False


def test_lower_sequence_is_rejected():
    guard = SequenceGuard()
    guard.check("SIM-01", 8)
    assert guard.check("SIM-01", 3)["accepted"] is False


def test_senders_are_tracked_separately():
    guard = SequenceGuard()
    guard.check("SIM-01", 10)
    assert guard.check("SIM-02", 1)["accepted"] is True
