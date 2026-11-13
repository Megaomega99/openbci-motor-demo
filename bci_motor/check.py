"""Comprobación rápida de la señal: python -m bci_motor.check [--active] [--bias]

Graba 6 s y muestra, por canal, el EEG (1-40 Hz), el ruido de la red eléctrica,
el offset DC y si el canal está OK, saturado, plano o con ruido.
"""
import argparse
import time

from .board import BOARDS, FTDI_VIDS, Board, find_port, rail_uv
from .features import channel_status, mains_amplitude

STATUS_TEXT = {"ok": "OK", "saturado": "SATURADO / sin señal",
               "plano": "plano", "ruido": "mucho ruido (movimiento / mal contacto)"}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bci_motor.check", description=__doc__)
    ap.add_argument("--board", default="cyton", choices=BOARDS.keys())
    ap.add_argument("--port", default="auto")
    ap.add_argument("--active", action="store_true")
    ap.add_argument("--bias", action="store_true")
    ap.add_argument("--mains", type=float, default=50.0, help="Frecuencia de red (50 o 60 Hz)")
    ap.add_argument("--seconds", type=float, default=6.0)
    args = ap.parse_args(argv)

    if args.port == "auto":
        args.port = "" if args.board == "synthetic" else find_port(FTDI_VIDS)
        if args.board.startswith("cyton") and not args.port:
            raise SystemExit("No encuentro el dongle OpenBCI. ¿Está conectado al USB?")
    print(f"OpenBCI {args.board} en {args.port or '-'}")

    gain = 8 if args.active else None
    board = Board(args.board, args.port)
    try:
        board.start(gain=gain, bias=args.bias)
        time.sleep(args.seconds)
        d = board.shim.get_board_data()
    finally:
        board.close()

    fs = board.fs
    rail = rail_uv(args.board, gain or 24)
    print(f"Muestras: {d.shape[1]} en {args.seconds:g} s (esperado ~{int(args.seconds * fs)}, fs={fs} Hz)")
    print(f"Canal | EEG 1-40Hz (µV) | {args.mains:g}Hz (µV) | offset DC (µV) | estado")
    for i, c in enumerate(board.eeg, 1):
        raw = d[c][int(fs):]                      # descarta el primer segundo
        status, rms = channel_status(raw, fs, rail)
        print(f"{i:5d} | {rms:15.1f} | {mains_amplitude(raw, fs, args.mains):9.1f} | "
              f"{raw.mean():14.0f} | {STATUS_TEXT[status]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
