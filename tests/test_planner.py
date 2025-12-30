import math
from datetime import datetime, time
import importlib.util
import sys
from pathlib import Path

# Load modules directly to avoid importing Home Assistant at package import-time
pkg_dir = Path(__file__).resolve().parents[1] / "custom_components" / "ev_smart_charger"

# Fixed timestamp for deterministic tests
FIXED_NOW = datetime(2025, 1, 15, 12, 0)


def _load_package_module(full_name, path):
    """Load a module using the provided full package-style name (e.g. custom_components.ev_smart_charger.const)
    This ensures relative imports inside the module work by preloading sibling modules into sys.modules.
    """
    spec = importlib.util.spec_from_file_location(full_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = mod
    spec.loader.exec_module(mod)
    return mod

# Load const first under the package namespace, then planner so relative imports succeed
const = _load_package_module("custom_components.ev_smart_charger.const", pkg_dir / "const.py")
planner = _load_package_module("custom_components.ev_smart_charger.planner", pkg_dir / "planner.py")


def make_price_list(length=96, base=2.0, low_indices=None, low_value=0.1, mid_indices=None, mid_value=1.4):
    """Create a price list (today) with optional low/mid price spikes."""
    prices = [float(base) for _ in range(length)]
    low_indices = low_indices or []
    mid_indices = mid_indices or []
    for i in low_indices:
        if 0 <= i < length:
            prices[i] = float(low_value)
    for i in mid_indices:
        if 0 <= i < length:
            prices[i] = float(mid_value)
    return prices


def test_low_price_triggers_high_target():
    # A very low price appears in the future -> target should be increased to target_1 (default 100)
    # place a low price a few slots in the future relative to now
    now = FIXED_NOW
    idx = (now.hour * 4) + (now.minute // 15) + 4
    raw_today = make_price_list(low_indices=[idx], low_value=0.1)

    data = {
        "price_data": {"today": raw_today},
        const.ENTITY_TARGET_SOC: 80,
        const.ENTITY_SMART_SWITCH: True,
        const.ENTITY_MIN_SOC: 20,
        const.ENTITY_DEPARTURE_TIME: time(23, 59),
        "car_soc": 30,
    }

    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}

    plan = planner.generate_charging_plan(data, config, manual_override=False, now=now)
    assert plan["planned_target_soc"] >= 100


def test_mid_price_triggers_medium_target_overrides_lower_user_target():
    # No very low prices, but a mid price <= price_limit_2 should increase a low user target
    now = FIXED_NOW
    idx = (now.hour * 4) + (now.minute // 15) + 5
    raw_today = make_price_list(mid_indices=[idx], mid_value=1.4)

    data = {
        "price_data": {"today": raw_today},
        const.ENTITY_TARGET_SOC: 70,
        const.ENTITY_SMART_SWITCH: True,
        const.ENTITY_MIN_SOC: 20,
        const.ENTITY_DEPARTURE_TIME: time(23, 59),
        "car_soc": 50,
    }

    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}

    plan = planner.generate_charging_plan(data, config, manual_override=False, now=now)
    # target_2 default is 80, so final_target should be raised to at least 80
    assert plan["planned_target_soc"] >= 80


def test_target_reached_selects_low_price_slots():
    # If car SoC already at/above target, the plan should select only slots with price <= price_limit_2
    raw_today = make_price_list(low_indices=[70, 71, 72], low_value=1.0, base=2.5)

    data = {
        "price_data": {"today": raw_today},
        const.ENTITY_TARGET_SOC: 80,
        const.ENTITY_SMART_SWITCH: True,
        const.ENTITY_MIN_SOC: 20,
        "car_soc": 90,  # already above target
    }

    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}

    plan = planner.generate_charging_plan(data, config, manual_override=False, now=FIXED_NOW)
    schedule = plan.get("charging_schedule", [])
    # All active slots should have price <= price_limit_2 (default 1.5)
    for slot in schedule:
        if slot.get("active"):
            assert slot["price"] <= data.get(const.ENTITY_PRICE_LIMIT_2, 1.5)


def test_manual_override_respected():
    raw_today = make_price_list(low_indices=[10], low_value=0.2)
    data = {
        "price_data": {"today": raw_today},
        const.ENTITY_TARGET_SOC: 80,
        const.ENTITY_TARGET_OVERRIDE: 50,
        const.ENTITY_SMART_SWITCH: True,
        const.ENTITY_MIN_SOC: 20,
        "car_soc": 40,
    }
    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}
    plan = planner.generate_charging_plan(data, config, manual_override=True, now=FIXED_NOW)
    assert int(plan["planned_target_soc"]) == 50


def test_calendar_event_sets_target_and_departure():
    # Calendar event with 90% in summary should set target
    now = FIXED_NOW
    evt_start = (now.replace(hour=(now.hour + 2) % 24)).isoformat()
    data = {
        "price_data": {"today": make_price_list()},
        const.ENTITY_SMART_SWITCH: True,
        const.ENTITY_MIN_SOC: 10,
        "car_soc": 30,
        "calendar_events": [{"start": evt_start, "summary": "Trip 90%"}],
    }
    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}
    plan = planner.generate_charging_plan(data, config, manual_override=False, now=now)
    assert int(plan["planned_target_soc"]) == 90
    assert plan.get("scheduled_start") is not None


def test_price_list_length_variations_handle_hourly_and_quarter():
    # Hourly price list (len <= 25)
    hourly = [1.0 for _ in range(24)]
    data_h = {"price_data": {"today": hourly}, const.ENTITY_SMART_SWITCH: True, "car_soc": 10}
    config = {"max_fuse": 20.0, "charger_loss": 10.0, "car_capacity": 64.0, "has_price_sensor": True}
    plan_h = planner.generate_charging_plan(data_h, config, manual_override=False, now=FIXED_NOW)
    assert isinstance(plan_h.get("charging_schedule"), list)

    # Quarter-hourly price list
    q = make_price_list(length=96)
    data_q = {"price_data": {"today": q}, const.ENTITY_SMART_SWITCH: True, "car_soc": 10}
    plan_q = planner.generate_charging_plan(data_q, config, manual_override=False, now=FIXED_NOW)
    assert isinstance(plan_q.get("charging_schedule"), list)


def test_calculate_load_balancing_with_zap_limit():
    data = {"p1_l1": 5.0, "p1_l2": 5.0, "p1_l3": 5.0, "ch_l1": 0.0, "ch_l2": 0.0, "ch_l3": 0.0, "zap_limit_value": 16.0}
    available = planner.calculate_load_balancing(data, max_fuse=20.0)
    # With zap_limit distributed, house load becomes zero and buffer=1 => available ~= 19
    assert math.isclose(available, 19.0, rel_tol=1e-3)

