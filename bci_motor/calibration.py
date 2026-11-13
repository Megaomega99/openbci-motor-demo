"""Calibración: mide alfa y EMG en todos los canales y elige los mejores."""
import time
from dataclasses import dataclass

import numpy as np

from .features import alpha_feature, channel_status, emg_feature
from .sound import beep


@dataclass
class Calibration:
    alpha_ch: int          # índice 0-based dentro de la lista de canales EEG
    emg_ch: int
    alpha_open: float
    alpha_closed: float
    emg_rest: float
    emg_clench: float

    @property
    def alpha_threshold(self):
        return float(np.sqrt(self.alpha_open * self.alpha_closed))   # media geométrica

    @property
    def emg_threshold(self):
        return (self.emg_rest + self.emg_clench) / 2                  # ya está en escala log

    @property
    def alpha_gain(self):
        return self.alpha_closed / (self.alpha_open + 1e-12)

    @property
    def emg_gain(self):
        return self.emg_clench - self.emg_rest


def check_channels(board, rail):
    """Estado de cada canal a partir de los últimos 2 s. Devuelve (estados, rms, buenos)."""
    d = board.window(2.0)
    states, rms = [], []
    for c in board.eeg:
        s, r = channel_status(d[c], board.fs, rail)
        states.append(s)
        rms.append(r)
    good = np.array([s == "ok" for s in states])
    return states, np.array(rms), good


def collect(board, seconds, message):
    """Mide alfa y EMG en todos los canales durante `seconds`. Devuelve medianas por canal."""
    print(f"\n>>> {message}  ({seconds:g} s)")
    beep(660)
    A, E = [], []
    fs = board.fs
    t0 = time.time()
    while time.time() - t0 < seconds:
        time.sleep(0.1)
        d = board.window(2.0)
        if d is None or time.time() - t0 < 1.0:      # descarta el primer segundo (transición)
            continue
        A.append([alpha_feature(d[c], fs) for c in board.eeg])
        E.append([emg_feature(d[c][-int(0.5 * fs):], fs) for c in board.eeg])
    beep(990, 400)
    print(f"    ventanas válidas: {len(A)}")
    if not A:
        raise RuntimeError("No llegaron datos del OpenBCI durante este paso. Revisa la batería "
                           "del Cyton y que el dongle esté cerca, y vuelve a lanzar.")
    return np.median(A, axis=0), np.median(E, axis=0)


def select_channels(a_open, a_closed, e_rest, e_clench, good, alpha_candidates,
                    alpha_ch=None, emg_ch=None):
    """Elige el canal con mayor aumento de alfa y el de mayor respuesta a la mandíbula.

    Todos los índices son 0-based. `alpha_ch`/`emg_ch` fuerzan un canal concreto.
    """
    n = len(good)
    good_idx = [i for i in range(n) if good[i]] or list(range(n))
    ratio = np.asarray(a_closed) / (np.asarray(a_open) + 1e-12)
    diff = np.asarray(e_clench) - np.asarray(e_rest)
    if alpha_ch is None:
        cands = [i for i in alpha_candidates if i < n and i in good_idx] or good_idx
        alpha_ch = max(cands, key=lambda i: ratio[i])
    if emg_ch is None:
        emg_ch = max(good_idx, key=lambda i: diff[i])
    return Calibration(alpha_ch, emg_ch,
                       float(a_open[alpha_ch]), float(a_closed[alpha_ch]),
                       float(e_rest[emg_ch]), float(e_clench[emg_ch]))


def run_calibration(board, rail, seconds=8.0, alpha_candidates=(2, 3, 4, 5, 6, 7),
                    alpha_ch=None, emg_ch=None):
    states, rms, good = check_channels(board, rail)
    print("\nCalidad de canales:")
    for i, (s, r) in enumerate(zip(states, rms)):
        print(f"  canal {i + 1:2d}: EEG {r:7.1f} µV  {'OK' if s == 'ok' else s.upper() + ' (no se usará)'}")
    if not good.any():
        print("AVISO: ningún canal parece bueno; se usarán todos igualmente.")

    a_open, e_rest = collect(board, seconds, "Relájate con los OJOS ABIERTOS")
    a_closed, _ = collect(board, seconds, "CIERRA LOS OJOS (ábrelos al oír el pitido agudo)")
    _, e_clench = collect(board, max(3.0, seconds / 2), "APRIETA LA MANDÍBULA")

    cal = select_channels(a_open, a_closed, e_rest, e_clench, good, alpha_candidates,
                          alpha_ch, emg_ch)

    ratio = a_closed / (a_open + 1e-12)
    diff = e_clench - e_rest
    print("\nCanal | alfa abiertos | alfa cerrados | aumento alfa | mandíbula")
    for i in range(len(good)):
        mark = ""
        if i == cal.alpha_ch:
            mark += "  <- ALFA"
        if i == cal.emg_ch:
            mark += "  <- MANDÍBULA"
        if not good[i]:
            mark += "  (malo)"
        print(f"  {i + 1:3d} | {a_open[i]:13.3f} | {a_closed[i]:13.3f} | x{ratio[i]:11.2f} | "
              f"{diff[i]:+8.2f}{mark}")

    print(f"\n==> ALFA en canal {cal.alpha_ch + 1} (x{cal.alpha_gain:.2f}),"
          f" MANDÍBULA en canal {cal.emg_ch + 1} ({cal.emg_gain:+.2f})")
    if cal.alpha_gain < 1.2:
        print("AVISO: poca diferencia de alfa. Revisa los electrodos de la nuca y repite.")
    if cal.emg_gain < 0.3:
        print("AVISO: poca diferencia al apretar la mandíbula.")
    return cal
