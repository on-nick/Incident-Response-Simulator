from safety import is_safe_target, check_target


def test_loopback_is_safe():
    assert is_safe_target("127.0.0.1") is True


def test_public_ip_is_unsafe():
    assert is_safe_target("8.8.8.8") is False


def test_malformed_ip_is_unsafe():
    assert is_safe_target("not-an-ip") is False


def test_none_target_is_unsafe():
    assert is_safe_target(None) is False


def test_unwhitelisted_private_ip_is_unsafe():
    # Private, but not in config.LAB_TARGETS by default
    assert is_safe_target("192.168.50.50") is False


def test_check_target_returns_reason_string():
    ok, reason = check_target("8.8.8.8")
    assert ok is False
    assert isinstance(reason, str)
    assert len(reason) > 0


def test_check_target_success_reason():
    ok, reason = check_target("127.0.0.1")
    assert ok is True
    assert "loopback" in reason.lower()
