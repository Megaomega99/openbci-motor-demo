"""Control del motor por puerto serie (115200 baudios).

Protocolos:
  simple       -> firmware/motor_bci/motor_bci.ino   R1 / R0 / D / S<us>
  motorinador  -> https://github.com/Megaomega99/Motorinador   1 / 0 / f / b / v<rpm>
"""
import time


class Motor:
    PROTOCOLS = ("simple", "motorinador")

    def __init__(self, port=None, protocol="simple", rpm=None, serial_factory=None):
        if protocol not in self.PROTOCOLS:
            raise ValueError(f"Protocolo desconocido: {protocol}")
        self.protocol = protocol
        self.forward = True
        self.running = None
        self.ser = None
        if port:
            if serial_factory is None:
                import serial
                serial_factory = serial.Serial
            self.ser = serial_factory(port, 115200, timeout=0)
            time.sleep(2.0)                 # algunos Arduino se reinician al abrir el puerto
            self.ser.reset_input_buffer()
            self._init_motor(rpm)

    @property
    def connected(self):
        return self.ser is not None

    def _init_motor(self, rpm):
        if self.protocol == "motorinador":
            self.send("0")
            self.send("f")
            if rpm:
                self.send(f"v{rpm:g}")
        else:
            self.send("R0")

    def send(self, cmd):
        if not self.ser:
            return
        self.ser.write((cmd + "\n").encode())
        if self.ser.in_waiting:             # el firmware puede enviar telemetría: la descartamos
            self.ser.reset_input_buffer()

    def set_running(self, on):
        if on == self.running:
            return
        self.running = on
        if self.protocol == "motorinador":
            self.send("1" if on else "0")
        else:
            self.send("R1" if on else "R0")

    def toggle_direction(self):
        self.forward = not self.forward
        if self.protocol == "motorinador":
            self.send("f" if self.forward else "b")
        else:
            self.send("D")

    def close(self):
        if self.ser:
            self.send("0" if self.protocol == "motorinador" else "R0")
            self.ser.close()
            self.ser = None
