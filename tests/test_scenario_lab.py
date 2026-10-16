
import pytest

from src.scenario_lab import build_scenario, SCENARIO_DESCRIPTIONS
from src.validator import validate_message


def test_valid_scenario_is_accepted():
    result = validate_message(build_scenario("valid"))
    assert result["accepted"] is True


@pytest.mark.parametrize(
    "scenario_name",
    [
        "temperature_out_of_range",
        "unauthorized_command",
        "missing_required_field",
        "stale_timestamp",
        "negative_sequence",
    ],
)
def test_invalid_scenarios_are_rejected(scenario_name):
    result = validate_message(build_scenario(scenario_name))
    assert result["accepted"] is False


def test_all_scenarios_have_descriptions():
    for name in SCENARIO_DESCRIPTIONS:
        assert build_scenario(name)


def test_unknown_scenario_raises_error():
    with pytest.raises(ValueError):
        build_scenario("not_a_real_scenario")
