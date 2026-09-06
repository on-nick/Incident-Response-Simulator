from detector import analyze


def test_port_scan_below_threshold_no_alert():
    events = [{"port": p} for p in [21, 22, 23]]  # 3 distinct ports, threshold is 5
    assert analyze("port_scan", events) == []


def test_port_scan_at_threshold_raises_alert():
    events = [{"port": p} for p in [21, 22, 23, 80, 443]]  # 5 distinct ports
    alerts = analyze("port_scan", events)
    assert len(alerts) == 1
    assert alerts[0]["scenario"] == "port_scan"
    assert alerts[0]["severity"] == "MEDIUM"


def test_syn_flood_below_threshold_no_alert():
    events = [{"dst_port": 80}] * 5  # threshold is 10
    assert analyze("syn_flood_lite", events) == []


def test_syn_flood_at_threshold_raises_alert():
    events = [{"dst_port": 80}] * 10
    alerts = analyze("syn_flood_lite", events)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"


def test_brute_force_below_threshold_no_alert():
    events = [{"username": "admin", "result": "failed"}] * 3  # threshold is 5
    assert analyze("brute_force_login", events) == []


def test_brute_force_at_threshold_raises_alert():
    events = [{"username": "admin", "result": "failed"}] * 5
    alerts = analyze("brute_force_login", events)
    assert len(alerts) == 1
    assert "5 failed" in alerts[0]["message"]


def test_brute_force_ignores_successful_logins():
    events = [{"username": "admin", "result": "success"}] * 5
    assert analyze("brute_force_login", events) == []


def test_malware_beacon_below_threshold_no_alert():
    events = [{"dst_port": 443, "protocol": "HTTPS"}] * 2  # threshold is 3
    assert analyze("malware_beacon", events) == []


def test_malware_beacon_at_threshold_raises_alert():
    events = [{"dst_port": 443, "protocol": "HTTPS"}] * 3
    alerts = analyze("malware_beacon", events)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "CRITICAL"


def test_unknown_scenario_returns_empty_list():
    assert analyze("not_a_real_scenario", [{"foo": "bar"}]) == []


def test_empty_events_returns_empty_list():
    assert analyze("port_scan", []) == []
