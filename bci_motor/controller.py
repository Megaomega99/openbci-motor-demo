"""Lógica de decisión: de características de la señal a órdenes para el motor."""


class Controller:
    """Alfa sostenido -> motor en marcha; pico de EMG -> cambio de sentido.

    hold:        segundos que el alfa debe superar el umbral antes de arrancar.
    refractory:  segundos mínimos entre dos cambios de sentido.
    smoothing:   peso de la muestra nueva en el suavizado exponencial del alfa.
    """

    def __init__(self, alpha_threshold, emg_threshold, alpha_start=0.0,
                 hold=0.5, refractory=1.0, smoothing=0.3):
        self.alpha_threshold = alpha_threshold
        self.emg_threshold = emg_threshold
        self.hold = hold
        self.refractory = refractory
        self.smoothing = smoothing
        self.alpha = alpha_start
        self.running = False
        self.forward = True
        self.last_toggle = float("-inf")
        self._above_since = None

    def update(self, alpha, emg, now):
        """Procesa una nueva muestra. Devuelve True si hay que invertir el sentido."""
        self.alpha = (1 - self.smoothing) * self.alpha + self.smoothing * alpha

        if self.alpha > self.alpha_threshold:
            if self._above_since is None:
                self._above_since = now
        else:
            self._above_since = None
        self.running = self._above_since is not None and now - self._above_since >= self.hold

        if emg > self.emg_threshold and now - self.last_toggle > self.refractory:
            self.last_toggle = now
            self.forward = not self.forward
            return True
        return False
