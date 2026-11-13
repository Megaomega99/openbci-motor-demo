"""Programa principal: python -m bci_motor [opciones]

  * Ojos cerrados      -> sube el ritmo ALFA (8-12 Hz) -> el motor GIRA
  * Apretar mandíbula  -> ráfaga de EMG               -> el motor CAMBIA de sentido

Ejemplos:
  python -m bci_motor --board synthetic --no-motor          # probar sin hardware
  python -m bci_motor --active --bias --motor motorinador   # ThinkPulse + Motorinador
"""
import argparse
import os
import sys
import time
from datetime import datetime

from .board import ARDUINO_VIDS, BOARDS, FTDI_VIDS, Board, find_port, rail_uv
from .calibration import run_calibration
from .controller import Controller
from .features import alpha_feature, emg_feature
from .motor import Motor
from .sound import beep


def build_parser():
    ap = argparse.ArgumentParser(prog="bci_motor", description="Mueve un motor con el cerebro (OpenBCI).")
    g = ap.add_argument_group("OpenBCI")
    g.add_argument("--board", default="cyton", choices=BOARDS.keys())
    g.add_argument("--port", default="auto", help="Puerto del dongle (p. ej. COM6) o 'auto'")
    g.add_argument("--mac", default="", help="MAC del Ganglion (opcional)")
    g.add_argument("--active", action="store_true",
                   help="Electrodos activos (ThinkPulse): ganancia x8 y SRB2")
    g.add_argument("--bias", action="store_true", help="Incluir BIAS (clip de BIAS conectado)")
    g.add_argument("--gain", type=int, default=None, choices=[1, 2, 4, 6, 8, 12, 24],
                   help="Ganancia del Cyton (por defecto 8 con --active, si no la de fábrica)")

    g = ap.add_argument_group("Motor")
    g.add_argument("--arduino", default="auto", help="Puerto del Arduino/ESP32 (p. ej. COM7) o 'auto'")
    g.add_argument("--no-motor", "--no-serial", dest="no_motor", action="store_true",
                   help="No usar Arduino (solo pantalla)")
    g.add_argument("--motor", default="simple", choices=Motor.PROTOCOLS,
                   help="'simple' = firmware/motor_bci, 'motorinador' = proyecto Motorinador")
    g.add_argument("--rpm", type=float, default=None, help="Motorinador: RPM (1-120)")

    g = ap.add_argument_group("Calibración")
    g.add_argument("--cal", type=float, default=8, help="Segundos por paso de calibración")
    g.add_argument("--alpha-ch", type=int, default=0, help="Canal para alfa (0 = automático)")
    g.add_argument("--emg-ch", type=int, default=0, help="Canal para mandíbula (0 = automático)")
    g.add_argument("--alpha-cands", default="3,4,5,6,7,8",
                   help="Candidatos para alfa en modo automático (sin Fp1/Fp2 por los parpadeos)")
    return ap


def resolve_ports(args):
    if args.port == "auto":
        args.port = "" if args.board == "synthetic" else find_port(FTDI_VIDS)
        if args.board.startswith("cyton") and not args.port:
            raise SystemExit("No encuentro el dongle OpenBCI. ¿Está conectado al USB?")
    if args.no_motor:
        args.arduino = None
    elif args.arduino == "auto":
        args.arduino = find_port(ARDUINO_VIDS) or None
        print(f"Arduino detectado en {args.arduino}" if args.arduino
              else "No hay Arduino conectado: la demo funcionará solo en pantalla.")


def main(argv=None):
    args = build_parser().parse_args(argv)
    resolve_ports(args)
    gain = args.gain or (8 if args.active else None)

    board = Board(args.board, args.port, args.mac)
    print(f"Conectando a {args.board} ({args.port or 'sin puerto'}) ... fs = {board.fs} Hz")
    motor = None
    try:
        board.start(gain=gain, bias=args.bias)
        if gain:
            print(f"Cyton configurado: ganancia x{gain}, BIAS {'on' if args.bias else 'off'}, SRB2 on")
        motor = Motor(args.arduino, args.motor, args.rpm)
        board.wait_for_data()
        time.sleep(1)

        cal = run_calibration(
            board, rail_uv(args.board, gain or 24), seconds=args.cal,
            alpha_candidates=[int(c) - 1 for c in args.alpha_cands.split(",")],
            alpha_ch=args.alpha_ch - 1 if args.alpha_ch else None,
            emg_ch=args.emg_ch - 1 if args.emg_ch else None)

        from .display import Dashboard
        ui = Dashboard(board.fs, cal, motor.connected)
        ctl = Controller(cal.alpha_threshold, cal.emg_threshold, alpha_start=cal.alpha_open)
        a_ch, e_ch = board.eeg[cal.alpha_ch], board.eeg[cal.emg_ch]
        fs = board.fs
        print("\nDemo en marcha. Cierra la ventana o pulsa Q para salir.")

        while ui.is_open:
            d = board.window(4.0)
            if d is None:
                ui.pause()
                continue
            now = time.time()
            emg = emg_feature(d[e_ch][-int(0.5 * fs):], fs)
            toggled = ctl.update(alpha_feature(d[a_ch][-int(2 * fs):], fs), emg, now)
            motor.set_running(ctl.running)
            if toggled:
                motor.toggle_direction()
                beep(1200, 80)
            ui.update(d[a_ch], ctl.alpha, emg, ctl.running, ctl.forward,
                      flash=now - ctl.last_toggle < 0.4)
            ui.pause()
    except KeyboardInterrupt:
        pass
    finally:
        if motor:
            motor.close()
        board.close()
        print("Sesión cerrada.")
    return 0


class _Tee:
    """Duplica la salida de consola en un archivo de registro."""

    def __init__(self, stream, f):
        self.stream, self.f = stream, f

    def write(self, s):
        self.stream.write(s)
        self.f.write(s)
        self.f.flush()

    def flush(self):
        self.stream.flush()
        self.f.flush()


def run(argv=None):
    """Punto de entrada: guarda todo lo que se imprime en logs/demo_<fecha>.log."""
    logdir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logdir, exist_ok=True)
    path = os.path.join(logdir, datetime.now().strftime("demo_%Y%m%d_%H%M%S.log"))
    with open(path, "w", encoding="utf-8") as log:
        sys.stdout = _Tee(sys.__stdout__, log)
        sys.stderr = _Tee(sys.__stderr__, log)
        try:
            return main(argv)
        finally:
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
