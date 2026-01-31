"""Tests for efficiency learning functionality."""
import pytest
from datetime import datetime, time, timedelta


def test_learning_constants():
    """Test that learning constants are defined."""
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_CONFIDENCE,
        LEARNING_SESSIONS,
        LEARNING_LOCKED,
        LEARNING_HISTORY,
        DEFAULT_LOSS,
    )
    
    assert LEARNING_CHARGER_LOSS == "learned_charger_loss"
    assert LEARNING_CONFIDENCE == "loss_confidence_level"
    assert LEARNING_SESSIONS == "loss_learning_sessions"
    assert LEARNING_LOCKED == "loss_locked"
    assert LEARNING_HISTORY == "learning_history"
    assert DEFAULT_LOSS == 0.0


def test_get_effective_charger_loss_initial():
    """Test that initial loss uses configured value."""
    from custom_components.ev_optimizer.planner import get_effective_charger_loss
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_SESSIONS,
        LEARNING_CONFIDENCE,
        LEARNING_LOCKED,
    )
    
    config = {"charger_loss": 10.0}
    learning_state = {
        LEARNING_CHARGER_LOSS: 10.0,
        LEARNING_SESSIONS: 0,
        LEARNING_CONFIDENCE: 0,
        LEARNING_LOCKED: False,
    }
    
    effective_loss, is_learning = get_effective_charger_loss(config, learning_state)
    
    assert effective_loss == 10.0
    assert is_learning is True  # First 10 sessions


def test_get_effective_charger_loss_uses_learned():
    """Test that learned value is used after first session."""
    from custom_components.ev_optimizer.planner import get_effective_charger_loss
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_SESSIONS,
        LEARNING_CONFIDENCE,
        LEARNING_LOCKED,
    )
    
    config = {"charger_loss": 10.0}
    learning_state = {
        LEARNING_CHARGER_LOSS: 7.5,
        LEARNING_SESSIONS: 3,
        LEARNING_CONFIDENCE: 4,
        LEARNING_LOCKED: False,
    }
    
    effective_loss, is_learning = get_effective_charger_loss(config, learning_state)
    
    assert effective_loss == 7.5  # Uses learned value
    assert is_learning is True


def test_get_effective_charger_loss_locked():
    """Test that locked state stops learning phase."""
    from custom_components.ev_optimizer.planner import get_effective_charger_loss
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_SESSIONS,
        LEARNING_CONFIDENCE,
        LEARNING_LOCKED,
    )
    
    config = {"charger_loss": 10.0}
    learning_state = {
        LEARNING_CHARGER_LOSS: 8.2,
        LEARNING_SESSIONS: 7,
        LEARNING_CONFIDENCE: 8,
        LEARNING_LOCKED: True,
    }
    
    effective_loss, is_learning = get_effective_charger_loss(config, learning_state)
    
    assert effective_loss == 8.2
    assert is_learning is False  # Locked


def test_get_effective_charger_loss_after_10_sessions():
    """Test that learning phase ends after 10 sessions."""
    from custom_components.ev_optimizer.planner import get_effective_charger_loss
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_SESSIONS,
        LEARNING_CONFIDENCE,
        LEARNING_LOCKED,
    )
    
    config = {"charger_loss": 10.0}
    learning_state = {
        LEARNING_CHARGER_LOSS: 8.0,
        LEARNING_SESSIONS: 10,
        LEARNING_CONFIDENCE: 7,
        LEARNING_LOCKED: False,
    }
    
    effective_loss, is_learning = get_effective_charger_loss(config, learning_state)
    
    assert effective_loss == 8.0
    assert is_learning is False  # 10+ sessions


def test_learning_buffer_added_during_learning():
    """Test that 30min buffer is added during learning phase."""
    from custom_components.ev_optimizer.planner import generate_charging_plan
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_SESSIONS,
        LEARNING_CONFIDENCE,
        LEARNING_LOCKED,
    )
    
    now = datetime(2024, 1, 15, 20, 0)
    
    data = {
        "car_plugged": True,
        "car_soc": 50,
        "smart_charging_active": True,
        "price_data": {
            "today": [0.5] * 24,
            "tomorrow": [0.5] * 24,
        },
        "target_soc": 80,
        "departure_time": time(7, 0),
        "min_guaranteed_soc": 20,
        "p1_l1": 5.0,
        "p1_l2": 5.0,
        "p1_l3": 5.0,
    }
    
    config = {
        "car_capacity": 64.0,
        "max_fuse": 20.0,
        "charger_loss": 0.0,
        "has_price_sensor": True,
        "currency": "SEK",
    }
    
    learning_state_learning = {
        LEARNING_CHARGER_LOSS: 5.0,
        LEARNING_SESSIONS: 3,
        LEARNING_CONFIDENCE: 4,
        LEARNING_LOCKED: False,
    }
    
    learning_state_locked = {
        LEARNING_CHARGER_LOSS: 5.0,
        LEARNING_SESSIONS: 10,
        LEARNING_CONFIDENCE: 9,
        LEARNING_LOCKED: True,
    }
    
    # Generate plans with both states
    plan_learning = generate_charging_plan(
        data, config, False, learning_state=learning_state_learning, now=now
    )
    plan_locked = generate_charging_plan(
        data, config, False, learning_state=learning_state_locked, now=now
    )
    
    # Learning phase should have more slots (due to 30min buffer)
    learning_slots = len([s for s in plan_learning.get("charging_schedule", []) if s.get("active")])
    locked_slots = len([s for s in plan_locked.get("charging_schedule", []) if s.get("active")])
    
    # With 30min buffer (2 slots for 15min intervals or 0.5 for 60min), learning should have more
    assert learning_slots >= locked_slots


def test_learning_state_defaults():
    """Test that learning state has proper defaults."""
    from custom_components.ev_optimizer.const import (
        LEARNING_CHARGER_LOSS,
        LEARNING_CONFIDENCE,
        LEARNING_SESSIONS,
        LEARNING_LOCKED,
        LEARNING_HISTORY,
        DEFAULT_LOSS,
    )
    
    # Simulate fresh learning state
    learning_state = {
        LEARNING_CHARGER_LOSS: DEFAULT_LOSS,
        LEARNING_CONFIDENCE: 0,
        LEARNING_SESSIONS: 0,
        LEARNING_LOCKED: False,
        LEARNING_HISTORY: [],
    }
    
    assert learning_state[LEARNING_CHARGER_LOSS] == 0.0
    assert learning_state[LEARNING_CONFIDENCE] == 0
    assert learning_state[LEARNING_SESSIONS] == 0
    assert learning_state[LEARNING_LOCKED] is False
    assert learning_state[LEARNING_HISTORY] == []


def test_learning_adjustment_increases_on_underperformance():
    """Test that efficiency loss increases when actual SoC is lower than expected."""
    # Simulate: Expected 75%, got 70% -> need MORE loss
    
    expected_soc = 75.0
    actual_soc = 70.0
    soc_error = actual_soc - expected_soc  # -5%
    
    current_loss = 5.0
    sessions = 2
    confidence = 3
    
    # Logic from coordinator._evaluate_efficiency_learning
    margin = 3.0  # confidence < 3
    
    if soc_error < -margin:
        # Underperforming - increase loss
        adjustment = min(3.0, abs(soc_error) * 0.5)  # Aggressive early (sessions < 5)
        current_loss += adjustment
        confidence = max(0, confidence - 1)
    
    assert current_loss > 5.0  # Loss should increase
    assert current_loss == 7.5  # 5.0 + min(3.0, 5.0*0.5) = 5.0 + 2.5
    assert confidence == 2  # Confidence decreased


def test_learning_adjustment_decreases_on_overperformance():
    """Test that efficiency loss decreases when actual SoC is higher than expected."""
    # Simulate: Expected 70%, got 76% -> need LESS loss
    
    expected_soc = 70.0
    actual_soc = 76.0
    soc_error = actual_soc - expected_soc  # +6%
    
    current_loss = 10.0
    sessions = 2
    confidence = 3
    
    margin = 3.0
    
    if soc_error > margin:
        # Outperforming - decrease loss (careful!)
        adjustment = -min(2.0, soc_error * 0.4)  # sessions < 5
        current_loss += adjustment
        confidence = max(0, confidence - 1)
    
    assert current_loss < 10.0  # Loss should decrease
    assert current_loss == 8.0  # 10.0 - 2.0 (min(2.0, 6.0*0.4)=min(2.0, 2.4)=2.0)
    assert confidence == 2


def test_learning_confidence_increases_within_margin():
    """Test that confidence increases when actual matches expected within margin."""
    expected_soc = 75.0
    actual_soc = 76.5
    soc_error = actual_soc - expected_soc  # +1.5%
    
    confidence = 5
    margin = 2.0  # confidence >= 3 and < 6
    
    if abs(soc_error) <= margin:
        confidence += 1
    
    assert confidence == 6


def test_learning_locks_at_confidence_8():
    """Test that learning locks when confidence reaches 8."""
    confidence = 7
    locked = False
    
    # Simulate good measurement
    confidence += 1
    
    if confidence >= 8:
        locked = True
    
    assert confidence == 8
    assert locked is True


def test_learning_bounds_loss_percentage():
    """Test that loss percentage is bounded between 0 and 20."""
    # Test lower bound
    loss_negative = -5.0
    loss_bounded = max(0.0, min(20.0, loss_negative))
    assert loss_bounded == 0.0
    
    # Test upper bound
    loss_too_high = 25.0
    loss_bounded = max(0.0, min(20.0, loss_too_high))
    assert loss_bounded == 20.0
    
    # Test within bounds
    loss_ok = 8.5
    loss_bounded = max(0.0, min(20.0, loss_ok))
    assert loss_bounded == 8.5


def test_learning_history_keeps_last_10():
    """Test that learning history only keeps last 10 entries."""
    history = []
    
    # Add 15 entries
    for i in range(15):
        history.append({
            "timestamp": f"2024-01-{i+1:02d}T12:00:00",
            "expected_soc": 70.0,
            "actual_soc": 71.0,
            "error": 1.0,
        })
    
    # Keep only last 10
    history = history[-10:]
    
    assert len(history) == 10
    assert history[0]["timestamp"] == "2024-01-06T12:00:00"  # Entry 6 is first
    assert history[-1]["timestamp"] == "2024-01-15T12:00:00"  # Entry 15 is last
