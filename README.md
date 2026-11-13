# Mueve un motor con el cerebro 🧠⚙️

Demo de **interfaz cerebro-computador (BCI)** con un **OpenBCI Cyton** y un motor paso a paso,
pensada para enseñar en clase cómo se mide y se usa la actividad eléctrica del cerebro.

| Haces esto… | …el OpenBCI mide… | …y el motor |
|---|---|---|
| **Cierras los ojos** | sube el **ritmo alfa** (8–12 Hz) en la nuca | **gira** |
| **Abres los ojos** | baja el alfa | **se para** |
| **Aprietas la mandíbula** | ráfaga de **EMG** (músculo temporal) | **cambia de sentido** |

En pantalla se ve el EEG en vivo, una barra de alfa y otra de mandíbula con su umbral, y el estado del motor.

```
 Casco + Cyton ──radio──> Dongle USB ──> PC (Python + BrainFlow) ──USB serie──> Arduino ──> Driver ──> Motor
                                          │
                                          ├─ FFT: potencia 8-12 Hz  -> ¿ojos cerrados?
                                          └─ FFT: potencia 25-95 Hz -> ¿mandíbula apretada?
```

## Características

- **Calibración guiada por pitidos** (~20 s): ojos abiertos → ojos cerrados → mandíbula.
- **Elige los canales sola**: revisa la calidad de los 8 canales, descarta los saturados o ruidosos
  y se queda con el canal donde más sube el alfa y el que más responde a la mandíbula.
  Si el casco queda mal colocado en un lado, usa el otro.
- **Detecta los puertos** del dongle OpenBCI y del Arduino automáticamente.
- Funciona **sin motor** (solo pantalla) y **sin hardware** (`--board synthetic`).
- Compatible con el firmware de [Motorinador](https://github.com/Megaomega99/Motorinador)
  (NEMA17 + TMC2208) o con el sketch sencillo incluido en [`firmware/`](firmware/motor_bci/motor_bci.ino).
- Registro de cada sesión en `logs/`.

## Hardware

| Componente | Probado con |
|---|---|
| Placa EEG | OpenBCI **Cyton** (8 canales, 250 Hz) con dongle USB. También admite Cyton+Daisy y Ganglion. |
| Electrodos | **ThinkPulse** activos (casco Ultracortex). También electrodos pasivos con pasta. |
| Motor | Arduino Nano Every + TMC2208 + NEMA17 con firmware **Motorinador** |
| Alternativa | Arduino UNO/Nano o ESP32 + ULN2003 + 28BYJ-48, o A4988/DRV8825 + NEMA17 con [`motor_bci.ino`](firmware/motor_bci/motor_bci.ino) *(no probado aún con hardware)* |

## Instalación

Requiere [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (o Anaconda).

```bash
git clone https://github.com/Megaomega99/openbci-motor-demo.git
cd openbci-motor-demo
conda env create -f environment.yml
```

En Windows también puedes hacer doble clic en [`scripts/instalar.bat`](scripts/instalar.bat).

Opcional: el [OpenBCI GUI](https://github.com/OpenBCI/OpenBCI_GUI/releases) sirve para ver la señal
antes de la demo (ciérralo antes de lanzar la demo: solo un programa puede usar el dongle a la vez).

## Uso

### Windows: doble clic

| Script | Qué hace |
|---|---|
| [`scripts/comprobar_senal.bat`](scripts/comprobar_senal.bat) | Test de 6 s de los 8 canales |
| [`scripts/demo.bat`](scripts/demo.bat) | Demo completa (ThinkPulse + Motorinador a 30 RPM) |

Puedes crear accesos directos en el escritorio a estos dos archivos.

### Línea de comandos

```bash
conda activate bci

# 1. Comprobar la señal
python -m bci_motor.check --active --bias

# 2. Demo
python -m bci_motor --active --bias --motor motorinador --rpm 30   # ThinkPulse + Motorinador
python -m bci_motor --motor simple                                 # electrodos pasivos + motor_bci.ino
python -m bci_motor --board synthetic --no-motor                   # sin hardware
```

Durante la demo: **Q** o **Esc** para salir. El motor recibe la orden de paro al cerrar.

<details>
<summary>Todas las opciones</summary>

| Opción | Por defecto | Descripción |
|---|---|---|
| `--board` | `cyton` | `cyton`, `cyton_daisy`, `ganglion`, `ganglion_native`, `synthetic` |
| `--port` | `auto` | Puerto del dongle OpenBCI (p. ej. `COM6`) |
| `--active` | – | Electrodos activos: ganancia x8, SRB2 activado |
| `--bias` | – | Incluir BIAS (con el clip de BIAS conectado) |
| `--gain` | 8 con `--active` | Ganancia del Cyton: 1, 2, 4, 6, 8, 12, 24 |
| `--arduino` | `auto` | Puerto del Arduino/ESP32 (p. ej. `COM7`) |
| `--no-motor` | – | Solo pantalla |
| `--motor` | `simple` | `simple` (motor_bci.ino) o `motorinador` |
| `--rpm` | – | Velocidad para Motorinador (1–120) |
| `--cal` | `8` | Segundos por paso de calibración |
| `--alpha-ch` / `--emg-ch` | `0` (auto) | Forzar un canal (1–8) |
| `--alpha-cands` | `3,4,5,6,7,8` | Canales candidatos para alfa (se excluyen Fp1/Fp2 por los parpadeos) |

</details>

## Colocación de electrodos (sistema 10-20)

| Canal | Pin Cyton | Posición | Uso en la demo |
|---|---|---|---|
| 1, 2 | N1P, N2P | Fp1, Fp2 (frente) | parpadeos (para enseñar artefactos) |
| 3, 4 | N3P, N4P | C3, C4 | corteza motora |
| 5, 6 | N5P, N6P | T7, T8 (sienes) | **mandíbula (EMG)** |
| 7, 8 | N7P, N8P | O1, O2 (nuca) | **alfa** |
| Referencia | **SRB2** | lóbulo de una oreja | |
| Tierra | **BIAS** | lóbulo de la otra oreja | |

> ⚠️ En el Cyton, **N1P–N8P, SRB2 y BIAS son los pines de la fila de abajo**.
> La fila de arriba (N1N–N8N) solo se usa en montajes bipolares (ECG, EMG).

### Electrodos activos ThinkPulse

- Cada electrodo tiene **3 cables**: señal (a N*x*P) y alimentación (a la placa de alimentación ThinkPulse).
  Con el multímetro no hay continuidad entre la goma y el cable de señal: hay un amplificador dentro.
- Con la ganancia por defecto (x24) **todos los canales saturan** (`RAILED`) por el gran offset DC
  (~250 000 µV). Usa `--active` (ganancia x8) o, en el OpenBCI GUI, *Hardware Settings → Gain x4/x8*.
- La prueba de impedancia del GUI **no es fiable** con electrodos activos: usa `bci_motor.check`.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `BOARD_NOT_READY_ERROR` | Cyton apagado o el GUI tiene una sesión abierta | Interruptor en **PC**, cierra el GUI, interruptor del dongle en **GPIO6** |
| Muchas menos muestras de las esperadas | Pérdidas de radio | Cambia las pilas, acerca el dongle (alargador USB) |
| Todos los canales planos o `SATURADO` | Electrodos en la fila de arriba o sin alimentación | Pines de la fila de abajo; revisa la placa ThinkPulse |
| Ruido de 50 Hz enorme en **todos** los canales | Referencia (SRB2) mal conectada | Clip de oreja bien puesto y húmedo; conecta BIAS y usa `--bias`; desenchufa el portátil |
| "Poca diferencia de alfa" | Mal contacto en la nuca o poco alfa natural | Aparta el pelo bajo O1/O2; prueba con otra persona |
| No llegan datos durante la calibración | Corte de radio | Batería del Cyton; la demo lo detecta y avisa |

## Cómo funciona

1. **Alfa**: en ventanas de 2 s se calcula la potencia en 8–12 Hz dividida por la de 3–30 Hz.
   Al ser un cociente no depende de la amplitud de cada electrodo.
2. **EMG**: en ventanas de 0,5 s, log10 de la potencia en 25–45 Hz + 65–95 Hz (se esquivan 50 y 60 Hz).
3. **Umbrales**: media geométrica entre ojos abiertos y cerrados (alfa) y punto medio entre reposo y
   mandíbula apretada (EMG).
4. **Decisión**: el motor arranca si el alfa suavizado supera el umbral durante 0,5 s;
   la mandíbula invierte el sentido con un periodo refractario de 1 s.

## Estructura

```
bci_motor/          paquete de Python
  cli.py            programa principal (python -m bci_motor)
  check.py          test de señal (python -m bci_motor.check)
  board.py          conexión y configuración del OpenBCI (BrainFlow)
  features.py       alfa, EMG y calidad de señal (solo numpy)
  calibration.py    calibración y selección automática de canales
  controller.py     lógica de decisión (alfa sostenido / pico de EMG)
  motor.py          protocolos serie (simple / Motorinador)
  display.py        panel en pantalla (matplotlib)
firmware/motor_bci/ sketch de Arduino/ESP32 para el protocolo simple
scripts/            lanzadores .bat para Windows
docs/               guía de la actividad para clase
tests/              tests (pytest), no necesitan hardware
```

## Tests

```bash
conda activate bci
python -m pytest
```

## Guía para clase

Guion de la actividad, mensajes clave y consejos: [`docs/guia-clase.md`](docs/guia-clase.md).

## Aviso

Proyecto educativo. **No es un dispositivo médico.** Mantén las manos lejos del motor mientras gira.

## Licencia

[MIT](LICENSE)
