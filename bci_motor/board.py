"""Conexión con la placa OpenBCI a través de BrainFlow."""
import time

from brainflow.board_shim import BoardIds, BoardShim, BrainFlowInputParams

BOARDS = {
    "synthetic": BoardIds.SYNTHETIC_BOARD,
    "cyton": BoardIds.CYTON_BOARD,
    "cyton_daisy": BoardIds.CYTON_DAISY_BOARD,
    "ganglion": BoardIds.GANGLION_BOARD,
    "ganglion_native": BoardIds.GANGLION_NATIVE_BOARD,
}

FTDI_VIDS = {0x0403}                                      # dongle USB de OpenBCI
ARDUINO_VIDS = {0x2341, 0x2A03, 0x1A86, 0x10C4, 0x303A}  # Arduino, CH340, CP210x, ESP32-S
DAISY_IDS = "QWERTYUI"                                   # canales 9-16 en los comandos del Cyton
ADS1299_VREF = 4.5                                       # V, fondo de escala = VREF / ganancia


def find_port(vids):
    """Primer puerto serie cuyo fabricante USB (VID) esté en `vids`, o ''."""
    from serial.tools import list_ports
    for p in list_ports.comports():
        if p.vid in vids:
            return p.device
    return ""


def rail_uv(board_name, gain):
    """Valor (µV) a partir del cual consideramos el canal saturado."""
    if not board_name.startswith("cyton"):
        return float("inf")
    return ADS1299_VREF / gain * 1e6 * 0.95


def channel_command(ch_index, gain=8, bias=False, srb2=True):
    """Comando de configuración de canal del Cyton: x<CH><POWER><GAIN><INPUT><BIAS><SRB2><SRB1>X.

    ch_index empieza en 0. Ganancia admitida: 1, 2, 4, 6, 8, 12, 24.
    """
    gain_codes = {1: 0, 2: 1, 4: 2, 6: 3, 8: 4, 12: 5, 24: 6}
    ch = "12345678"[ch_index] if ch_index < 8 else DAISY_IDS[ch_index - 8]
    return f"x{ch}0{gain_codes[gain]}0{int(bias)}{int(srb2)}0X"


class Board:
    """Envoltorio sencillo sobre BoardShim (abrir, configurar, leer, cerrar)."""

    def __init__(self, name, port="", mac=""):
        self.name = name
        self.board_id = BOARDS[name].value
        params = BrainFlowInputParams()
        params.serial_port = port
        params.mac_address = mac
        BoardShim.disable_board_logger()
        self.shim = BoardShim(self.board_id, params)
        self.fs = BoardShim.get_sampling_rate(self.board_id)
        self.eeg = BoardShim.get_eeg_channels(self.board_id)
        self.prepared = False

    @property
    def n_channels(self):
        return len(self.eeg)

    def start(self, gain=None, bias=False):
        self.shim.prepare_session()
        self.prepared = True
        if gain and self.name.startswith("cyton"):
            for i in range(self.n_channels):
                self.shim.config_board(channel_command(i, gain=gain, bias=bias))
        self.shim.start_stream()

    def window(self, seconds):
        """Últimos `seconds` segundos de datos, o None si aún no hay suficientes."""
        n = int(seconds * self.fs)
        d = self.shim.get_current_board_data(n)
        return d if d.shape[1] >= n else None

    def count(self):
        return self.shim.get_board_data_count()

    def wait_for_data(self, seconds=2.0, timeout=15.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            n = self.count()
            print(f"\r  Esperando datos del OpenBCI... {n} muestras", end="", flush=True)
            if n >= seconds * self.fs:
                print("  OK")
                return
            time.sleep(0.5)
        print()
        raise RuntimeError("El OpenBCI no envía datos. Apaga y enciende el Cyton "
                           "(interruptor en PC), acerca el dongle y vuelve a lanzar.")

    def close(self):
        if self.prepared:
            try:
                self.shim.stop_stream()
            except Exception:
                pass
            self.shim.release_session()
            self.prepared = False
