"""Extracción de características de la señal (solo numpy, sin dependencias de hardware)."""
import numpy as np


def detrend(x):
    """Quita la media y la tendencia lineal (deriva lenta del electrodo)."""
    x = np.asarray(x, dtype=float)
    t = np.arange(len(x))
    return x - np.polyval(np.polyfit(t, x, 1), t)


def band_power(x, fs, lo, hi):
    """Potencia media en [lo, hi] Hz usando FFT con ventana de Hann."""
    x = detrend(x)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    m = (f >= lo) & (f <= hi)
    return float(spec[m].mean()) if m.any() else 0.0


def alpha_feature(x, fs):
    """Alfa relativo: potencia 8-12 Hz frente a 3-30 Hz.

    Al ser un cociente no depende de la amplitud absoluta de cada electrodo,
    así que sirve para comparar canales y personas distintas.
    """
    return band_power(x, fs, 8, 12) / (band_power(x, fs, 3, 30) + 1e-12)


def emg_feature(x, fs):
    """Actividad muscular (mandíbula): log10 de la potencia en banda alta, evitando 50/60 Hz."""
    hi = min(95, fs / 2 - 2)
    p = band_power(x, fs, 25, 45) + band_power(x, fs, 65, hi)
    return float(np.log10(p + 1e-12))


def eeg_rms(x, fs, lo=1.0, hi=40.0):
    """Desviación estándar de la señal filtrada (paso banda por FFT) en µV."""
    x = detrend(x)
    F = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    F[(f < lo) | (f > hi)] = 0
    return float(np.fft.irfft(F, len(x)).std())


def mains_amplitude(x, fs, freq=50.0):
    """Amplitud aproximada (µV) de la interferencia de la red eléctrica."""
    x = detrend(x)
    w = np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x * w)) * 2 / w.sum()
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    m = (f > freq - 1) & (f < freq + 1)
    return float(spec[m].max()) if m.any() else 0.0


def channel_status(raw, fs, rail_uv, max_rms=150.0):
    """Clasifica un canal: 'ok', 'saturado', 'plano' o 'ruido'. Devuelve (estado, rms)."""
    raw = np.asarray(raw, dtype=float)
    rms = eeg_rms(raw, fs)
    if np.abs(raw).max() > rail_uv or np.ptp(raw) < 1:
        return "saturado", rms
    if rms < 0.5:
        return "plano", rms
    if rms > max_rms:
        return "ruido", rms
    return "ok", rms
