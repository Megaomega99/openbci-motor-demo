# Guía de la actividad: «Mueve un motor con el cerebro»

Duración: **30–40 min**. Combina neurociencia, procesamiento de señales y electrónica.

## Antes de clase (15 min)

1. Coloca el casco a ti mismo y ejecuta `scripts/comprobar_senal.bat`: los canales 5–8 deberían salir **OK**.
2. Haz una calibración completa con `scripts/demo.bat` para comprobar que el alfa se ve bien.
3. Ten pilas de repuesto para el Cyton y el dongle cerca del casco.
4. Deja abierto el **OpenBCI GUI** solo para la parte 2 y ciérralo antes de lanzar la demo.

## Guion

### 1. Gancho (5 min)

Motor parado. El voluntario cierra los ojos → el motor gira. Aprieta los dientes → cambia de sentido.
Pregunta a la clase: *«¿Cómo lo hace?»*

### 2. ¿Qué estamos midiendo? (10 min), con el OpenBCI GUI

- **Parpadeos** en Fp1/Fp2: picos enormes. Son artefactos del ojo, no del cerebro.
  La señal cerebral es ~100 veces más pequeña (microvoltios).
- **Mandíbula** en T7/T8: ruido rápido de alta frecuencia → actividad muscular (EMG).
- **Ojos cerrados**: en el widget *FFT Plot* aparece un pico en ~10 Hz en O1/O2.
  Es el **ritmo alfa**, descrito por Hans Berger en 1929 en el primer EEG humano.

### 3. Del cerebro a una orden (5 min)

- La **FFT** descompone la señal en frecuencias, como un ecualizador de música.
- La **calibración** aprende los niveles de *esta* persona y pone el umbral en medio.
- Es el esquema de toda BCI: **medir → extraer una característica → clasificar → actuar**.

### 4. Del ordenador al motor (5 min)

El PC envía comandos de un carácter por USB al Arduino (`1` marcha, `0` paro, `f`/`b` sentido).
El Arduino genera los pulsos para el driver del motor paso a paso.

### 5. Turno de los estudiantes

- Varios voluntarios, cada uno con su calibración. **Cada cerebro es distinto**:
  algunos tienen mucho alfa y otros casi nada.
- Reto: *«¿Quién consigue que el motor gire con los ojos ABIERTOS?»*
  (relajarse mucho o desenfocar la mirada a veces lo consigue → neurofeedback, meditación).

## Mensajes clave para cerrar

- El EEG mide la actividad **sincronizada de millones de neuronas**, no pensamientos concretos:
  no se puede «leer la mente».
- Las BCI reales ayudan a personas con parálisis a mover sillas, prótesis o a escribir.
- Gran parte del trabajo es **separar el cerebro del ruido**: ojos, músculos y la red eléctrica.

## Consejos prácticos

- Si con alguien no funciona el alfa (pelo grueso, poco alfa natural), cámbiale el papel:
  la mandíbula funciona con casi todo el mundo.
- Pide al voluntario que esté **quieto y sin hablar** durante la calibración.
- Los electrodos secos mejoran tras 2–3 minutos puestos.
- Recalibra con cada voluntario (cierra la demo y vuelve a lanzarla).
