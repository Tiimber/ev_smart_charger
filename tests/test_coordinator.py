from datetime import datetime


def test_fetch_sensor_data_reads_values(pkg_loader, hass_mock):
    const = pkg_loader("const")
    coordinator_mod = pkg_loader("coordinator")

    # Create fake states
    class State:
        def __init__(self, state, attributes=None):
            self.state = state
            self.attributes = attributes or {}

    hass_mock.states = type("S", (), {"get": lambda self, e: {
        "sensor.p1_l1": State("5.0"),
        "sensor.p1_l2": State("3.0"),
        "sensor.p1_l3": State("2.0"),
        "number.zap_limit": State("15"),
        "sensor.car_soc": State("40"),
    }.get(e)})()

    # Minimal entry stub
    class Entry:
        def __init__(self):
            self.options = {}
            self.data = {
                const.CONF_P1_L1: "sensor.p1_l1",
                const.CONF_P1_L2: "sensor.p1_l2",
                const.CONF_P1_L3: "sensor.p1_l3",
                const.CONF_ZAPTEC_LIMITER: "number.zap_limit",
                const.CONF_CAR_SOC_SENSOR: "sensor.car_soc",
                const.CONF_MAX_FUSE: const.DEFAULT_MAX_FUSE,
                const.CONF_CHARGER_LOSS: const.DEFAULT_LOSS,
                const.CONF_CAR_CAPACITY: const.DEFAULT_CAPACITY,
            }
            self.entry_id = "test"

    entry = Entry()
    coord = coordinator_mod.EVSmartChargerCoordinator(hass_mock, entry)

    data = coord._fetch_sensor_data()

    assert data["p1_l1"] == 5.0
    assert data["p1_l2"] == 3.0
    assert data["p1_l3"] == 2.0
    assert data["zap_limit_value"] == 15.0
    assert data["car_soc"] == 40.0


def test_fetch_sensor_data_handles_unavailable(pkg_loader, hass_mock):
    coordinator_mod = pkg_loader("coordinator")
    const = pkg_loader("const")

    class State:
        def __init__(self, state):
            self.state = state

    # Return None or unavailable
    hass_mock.states = type("S", (), {"get": lambda self, e: None})()

    class Entry:
        def __init__(self):
            self.options = {}
            self.data = {
                const.CONF_P1_L1: None,
                const.CONF_P1_L2: None,
                const.CONF_P1_L3: None,
                const.CONF_ZAPTEC_LIMITER: None,
                const.CONF_CAR_SOC_SENSOR: None,
                const.CONF_MAX_FUSE: const.DEFAULT_MAX_FUSE,
                const.CONF_CHARGER_LOSS: const.DEFAULT_LOSS,
                const.CONF_CAR_CAPACITY: const.DEFAULT_CAPACITY,
            }
            self.entry_id = "test"

    entry = Entry()
    coord = coordinator_mod.EVSmartChargerCoordinator(hass_mock, entry)
    data = coord._fetch_sensor_data()

    assert data["p1_l1"] == 0.0
    assert data["ch_l1"] == 0.0
    assert data.get("zap_limit_value", 0.0) == 0.0
