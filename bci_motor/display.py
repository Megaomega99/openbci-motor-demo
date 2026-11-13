"""Panel en pantalla (pensado para proyectar): EEG en vivo, barras de alfa/EMG y estado del motor."""
import numpy as np

BG = "#111111"
COLORS = {"eeg": "#4fc3f7", "alpha": "#ab47bc", "emg": "#ff7043", "flash": "#ffeb3b",
          "on": "#66bb6a", "off": "#777777", "grid": "#444444", "text": "#ffffff"}


class Dashboard:
    def __init__(self, fs, cal, motor_connected, seconds=4.0):
        import matplotlib
        import matplotlib.pyplot as plt
        matplotlib.rcParams["toolbar"] = "None"
        self.plt = plt
        plt.ion()

        self.fs = fs
        self.n = int(seconds * fs)
        self.closed = False

        fig = plt.figure("Demo BCI - mueve el motor con el cerebro", figsize=(13, 7), facecolor=BG)
        fig.canvas.mpl_connect("key_press_event", self._on_key)
        fig.canvas.mpl_connect("close_event", lambda e: setattr(self, "closed", True))
        gs = fig.add_gridspec(2, 3, height_ratios=[1, 2.2])
        self.ax_raw = fig.add_subplot(gs[0, :])
        ax_a = fig.add_subplot(gs[1, 0])
        ax_e = fig.add_subplot(gs[1, 1])
        ax_s = fig.add_subplot(gs[1, 2])
        for ax in (self.ax_raw, ax_a, ax_e, ax_s):
            ax.set_facecolor(BG)
            ax.tick_params(colors="#aaaaaa")
            for s in ax.spines.values():
                s.set_color(COLORS["grid"])

        t = np.arange(self.n) / fs
        (self.line,) = self.ax_raw.plot(t, np.zeros(self.n), color=COLORS["eeg"], lw=0.8)
        self.ax_raw.set_title(f"EEG en vivo (canal {cal.alpha_ch + 1})", color=COLORS["text"])
        self.ax_raw.set_xticks([])

        self.a_max = max(cal.alpha_closed * 1.6, cal.alpha_threshold * 2, 1e-3)
        self.bar_a = ax_a.bar([0], [0], color=COLORS["alpha"], width=0.6)[0]
        ax_a.axhline(cal.alpha_threshold, color=COLORS["text"], ls="--")
        ax_a.set_ylim(0, self.a_max)
        ax_a.set_xticks([])
        ax_a.set_title(f"ALFA - ojos cerrados (canal {cal.alpha_ch + 1})",
                       color=COLORS["text"], fontsize=14)

        lo, hi = sorted((cal.emg_rest, cal.emg_clench))
        self.e_lo, self.e_hi = lo - 0.5, hi + 0.5
        self.bar_e = ax_e.bar([0], [0], color=COLORS["emg"], width=0.6, bottom=self.e_lo)[0]
        ax_e.axhline(cal.emg_threshold, color=COLORS["text"], ls="--")
        ax_e.set_ylim(self.e_lo, self.e_hi)
        ax_e.set_xticks([])
        ax_e.set_yticks([])
        ax_e.set_title(f"MANDÍBULA - EMG (canal {cal.emg_ch + 1})", color=COLORS["text"], fontsize=14)

        ax_s.axis("off")
        kw = dict(ha="center", va="center", transform=ax_s.transAxes)
        self.txt_state = ax_s.text(0.5, 0.65, "", fontsize=32, fontweight="bold", **kw)
        self.txt_dir = ax_s.text(0.5, 0.40, "", fontsize=26, color=COLORS["text"], **kw)
        ax_s.text(0.5, 0.12, "motor conectado" if motor_connected else "sin motor (solo pantalla)",
                  fontsize=12, color="#aaaaaa", **kw)
        ax_s.text(0.5, 0.02, "Q / Esc para salir", fontsize=10, color="#666666", **kw)
        fig.tight_layout()
        self.fig = fig

    def _on_key(self, event):
        if event.key in ("q", "escape"):
            self.plt.close(self.fig)

    def update(self, raw, alpha, emg, running, forward, flash):
        raw = np.asarray(raw[-self.n:], dtype=float)
        raw = raw - raw.mean()
        if len(raw) == self.n:
            self.line.set_ydata(raw)
            lim = max(50.0, np.percentile(np.abs(raw), 99) * 1.2)
            self.ax_raw.set_ylim(-lim, lim)
        self.bar_a.set_height(min(alpha, self.a_max))
        self.bar_e.set_height(float(np.clip(emg, self.e_lo, self.e_hi)) - self.e_lo)
        self.bar_e.set_color(COLORS["flash"] if flash else COLORS["emg"])
        self.txt_state.set_text("MOTOR GIRANDO" if running else "motor parado")
        self.txt_state.set_color(COLORS["on"] if running else COLORS["off"])
        self.txt_dir.set_text("sentido: ADELANTE" if forward else "sentido: ATRÁS")

    def pause(self, seconds=0.05):
        self.plt.pause(seconds)

    @property
    def is_open(self):
        return not self.closed and self.plt.fignum_exists(self.fig.number)
