import numpy as np

from bci_motor.calibration import select_channels

A_OPEN = np.array([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10])
A_CLOSED = np.array([0.50, 0.12, 0.11, 0.10, 0.12, 0.13, 0.25, 0.30])   # canal 1 = parpadeos
E_REST = np.full(8, 2.0)
E_CLENCH = np.array([2.5, 2.4, 2.2, 2.2, 3.5, 3.1, 2.6, 2.5])
ALL_GOOD = np.ones(8, bool)
CANDS = [2, 3, 4, 5, 6, 7]


def test_picks_best_alpha_among_candidates_and_best_emg():
    cal = select_channels(A_OPEN, A_CLOSED, E_REST, E_CLENCH, ALL_GOOD, CANDS)
    assert cal.alpha_ch == 7          # canal 8 (O2); el canal 1 no es candidato
    assert cal.emg_ch == 4            # canal 5 (T7)


def test_skips_bad_channels():
    good = ALL_GOOD.copy()
    good[[7, 4]] = False
    cal = select_channels(A_OPEN, A_CLOSED, E_REST, E_CLENCH, good, CANDS)
    assert cal.alpha_ch == 6          # cae a O1
    assert cal.emg_ch == 5            # cae a T8


def test_forced_channels_and_thresholds():
    cal = select_channels(A_OPEN, A_CLOSED, E_REST, E_CLENCH, ALL_GOOD, CANDS, alpha_ch=6, emg_ch=0)
    assert (cal.alpha_ch, cal.emg_ch) == (6, 0)
    assert cal.alpha_open < cal.alpha_threshold < cal.alpha_closed
    assert cal.emg_rest < cal.emg_threshold < cal.emg_clench


def test_all_bad_falls_back_to_all_channels():
    cal = select_channels(A_OPEN, A_CLOSED, E_REST, E_CLENCH, np.zeros(8, bool), CANDS)
    assert cal.alpha_ch == 7
