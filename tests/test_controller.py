from bci_motor.controller import Controller


def make():
    return Controller(alpha_threshold=1.0, emg_threshold=5.0, alpha_start=0.5,
                      hold=0.5, refractory=1.0, smoothing=1.0)   # sin suavizado: más fácil de probar


def test_motor_starts_only_after_sustained_alpha():
    c = make()
    c.update(2.0, 0, now=0.0)
    assert not c.running
    c.update(2.0, 0, now=0.6)
    assert c.running
    c.update(0.1, 0, now=0.7)
    assert not c.running


def test_short_alpha_burst_does_not_start_motor():
    c = make()
    c.update(2.0, 0, now=0.0)
    c.update(0.1, 0, now=0.2)
    c.update(2.0, 0, now=0.3)
    c.update(2.0, 0, now=0.6)
    assert not c.running


def test_clench_toggles_direction_with_refractory_period():
    c = make()
    assert c.update(0, 9.0, now=0.0) is True
    assert c.forward is False
    assert c.update(0, 9.0, now=0.5) is False     # dentro del periodo refractario
    assert c.update(0, 9.0, now=1.2) is True
    assert c.forward is True


def test_smoothing():
    c = Controller(1.0, 5.0, alpha_start=0.0, smoothing=0.5)
    c.update(1.0, 0, now=0)
    assert c.alpha == 0.5
