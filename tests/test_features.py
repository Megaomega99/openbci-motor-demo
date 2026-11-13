import numpy as np

from bci_motor.features import alpha_feature, channel_status, eeg_rms, emg_feature, mains_amplitude

FS = 250
T = np.arange(2 * FS) / FS
RNG = np.random.default_rng(0)


def noise(scale=5.0, n=len(T)):
    return RNG.normal(0, scale, n)


def test_alpha_rises_with_10hz_rhythm():
    eyes_open = noise()
    eyes_closed = noise() + 30 * np.sin(2 * np.pi * 10 * T)
    assert alpha_feature(eyes_closed, FS) > 3 * alpha_feature(eyes_open, FS)


def test_alpha_ignores_dc_offset():
    x = noise() + 20 * np.sin(2 * np.pi * 10 * T)
    assert np.isclose(alpha_feature(x, FS), alpha_feature(x + 250_000, FS), rtol=1e-6)


def test_emg_rises_with_muscle_activity():
    rest = noise(2.0, FS // 2)
    clench = rest + noise(40.0, FS // 2)
    assert emg_feature(clench, FS) > emg_feature(rest, FS) + 1.0


def test_emg_ignores_mains_interference():
    t = np.arange(FS // 2) / FS
    rest = noise(2.0, FS // 2)
    hum = rest + 500 * np.sin(2 * np.pi * 50 * t)
    assert emg_feature(hum, FS) < emg_feature(rest, FS) + 1.0


def test_mains_amplitude_measures_50hz():
    x = 100 * np.sin(2 * np.pi * 50 * T)
    assert 80 < mains_amplitude(x, FS) < 120


def test_eeg_rms_removes_drift():
    x = 10 * np.sin(2 * np.pi * 10 * T) + 1000 * T     # rampa lenta + alfa
    assert 5 < eeg_rms(x, FS) < 12


def test_channel_status():
    rail = 4.5 / 8 * 1e6 * 0.95
    assert channel_status(noise(20) - 250_000, FS, rail)[0] == "ok"
    assert channel_status(np.full(len(T), 562_500.0), FS, rail)[0] == "saturado"
    assert channel_status(noise(500), FS, rail)[0] == "ruido"
