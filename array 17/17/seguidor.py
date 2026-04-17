#!/usr/bin/env pybricks-micropython

# pyright: ignore[reportMissingImports]

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Port, Button
from pybricks.tools import wait

# ─── Hardware ───────────────────────────────────────────────────────────────

ev3 = EV3Brick()

motor_izquierdo  = Motor(Port.A)
motor_derecho    = Motor(Port.D)
motor_inferiorI  = Motor(Port.B)
motor_inferiorD  = Motor(Port.C)

sensor = I2CDevice(Port.S4, 0x11)

# ─── Parámetros ajustables ──────────────────────────────────────────────────

Vel           = 80       # velocidad base (deg/s)
Kp            = 3.0      # proporcional
Kd            = 1.2      # derivativo (amortigua oscilaciones)
ALPHA         = 0.35     # EMA: 0=muy suave, 1=sin filtro
UMBRAL_LINEA  = 40       # 0–100: por debajo = sobre la línea
GAP_MS        = 500      # ms de tolerancia antes de declarar línea perdida
VEL_BUSQUEDA  = 40       # velocidad de giro al buscar línea

# ─── Estado global ──────────────────────────────────────────────────────────

cal_negro    = [0,   0,   0,   0,   0  ]
cal_blanco   = [255, 255, 255, 255, 255]
suavizado    = [128.0, 128.0, 128.0, 128.0, 128.0]
ultimo_raw   = [128, 128, 128, 128, 128]
error_ant    = 0.0
ultimo_lado  = 1          # -1 = izquierda, 1 = derecha
ms_sin_linea = 0

# ─── Funciones de lectura ────────────────────────────────────────────────────

def leer_raw():
    """Lee 5 bytes crudos del sensor. Devuelve lista o None si falla."""
    try:
        return list(sensor.read(0, 5))
    except:
        return None


def leer_suavizado():
    """Aplica EMA sobre la última lectura válida. Devuelve lista de 5 floats."""
    global suavizado, ultimo_raw
    raw = leer_raw()
    if raw is not None:
        for i in range(5):
            suavizado[i] = ALPHA * raw[i] + (1 - ALPHA) * suavizado[i]
        ultimo_raw = raw
    return suavizado


def normalizar(valores):
    """Convierte valores crudos a escala 0–100 usando calibración.
    0 = negro (sobre la línea), 100 = blanco (fuera de la línea).
    """
    result = []
    for i in range(5):
        rango = cal_blanco[i] - cal_negro[i]
        if rango == 0:
            result.append(50)
            continue
        n = int(100 * (valores[i] - cal_negro[i]) / rango)
        result.append(max(0, min(100, n)))
    return result

# ─── Calibración ─────────────────────────────────────────────────────────────

def _promediar_muestras(n=20, delay_ms=30):
    muestras = []
    for _ in range(n):
        r = leer_raw()
        if r is not None:
            muestras.append(r)
        wait(delay_ms)
    if not muestras:
        return None
    return [sum(m[i] for m in muestras) // len(muestras) for i in range(5)]


def calibrar():
    global cal_negro, cal_blanco

    # --- Negro ---
    ev3.screen.clear()
    ev3.screen.draw_text(5, 10, "CALIBRACION")
    ev3.screen.draw_text(5, 30, "Pon en NEGRO")
    ev3.screen.draw_text(5, 50, "Presiona OK")
    while Button.CENTER not in ev3.buttons.pressed():
        wait(50)
    wait(300)

    res = _promediar_muestras()
    if res:
        cal_negro = res

    # --- Blanco ---
    ev3.screen.clear()
    ev3.screen.draw_text(5, 10, "CALIBRACION")
    ev3.screen.draw_text(5, 30, "Pon en BLANCO")
    ev3.screen.draw_text(5, 50, "Presiona OK")
    while Button.CENTER not in ev3.buttons.pressed():
        wait(50)
    wait(300)

    res = _promediar_muestras()
    if res:
        cal_blanco = res

    # --- Confirmación ---
    ev3.screen.clear()
    ev3.screen.draw_text(5, 10, "Listo!")
    ev3.screen.draw_text(5, 25, "N:" + str(cal_negro))
    ev3.screen.draw_text(5, 40, "B:" + str(cal_blanco))
    ev3.screen.draw_text(5, 60, "OK para arrancar")
    while Button.CENTER not in ev3.buttons.pressed():
        wait(50)
    wait(300)

# ─── Control de motores ──────────────────────────────────────────────────────

def mover(vel_izq, vel_der):
    motor_izquierdo.run(vel_izq)
    motor_inferiorI.run(vel_izq)
    motor_derecho.run(vel_der)
    motor_inferiorD.run(vel_der)

# ─── Main ────────────────────────────────────────────────────────────────────

calibrar()

# Inicializar EMA con lecturas reales antes de arrancar
for _ in range(15):
    leer_suavizado()
    wait(30)

while True:

    # 1. Leer y normalizar
    raw       = leer_suavizado()
    valores   = normalizar(raw)   # 0=negro(línea), 100=blanco

    # 2. Detectar sensores sobre la línea
    en_linea  = [1 if v < UMBRAL_LINEA else 0 for v in valores]
    n_activos = sum(en_linea)

    if n_activos > 0:
        # ── Línea detectada ──────────────────────────────────────────────────
        ms_sin_linea = 0

        # Error ponderado por intensidad: posiciones -2,-1,0,1,2
        # Sensor más oscuro → más peso
        pesos      = [-2, -1, 0, 1, 2]
        peso_linea = [100 - valores[i] for i in range(5)]  # oscuridad = peso
        total_peso = sum(peso_linea)

        if total_peso == 0:
            error = 0.0
        else:
            error = sum(peso_linea[i] * pesos[i] for i in range(5)) / total_peso

        # Recordar último lado
        if error < -0.15:
            ultimo_lado = -1
        elif error > 0.15:
            ultimo_lado = 1

        # Control PD
        derivada   = error - error_ant
        correccion = Kp * error + Kd * derivada
        error_ant  = error

        mover(Vel - correccion, Vel + correccion)

        ev3.screen.clear()
        ev3.screen.draw_text(5, 10, str(valores))
        ev3.screen.draw_text(5, 30, "E:" + str(round(error, 2)))
        ev3.screen.draw_text(5, 50, "C:" + str(round(correccion, 1)))

    else:
        # ── Línea perdida ────────────────────────────────────────────────────
        ms_sin_linea += 80

        if ms_sin_linea < GAP_MS:
            # Gap corto: seguir recto despacio
            mover(int(Vel * 0.6), int(Vel * 0.6))
        else:
            # Gap largo: girar hacia el último lado conocido
            giro     = VEL_BUSQUEDA * ultimo_lado
            vel_base = int(Vel * 0.5)
            mover(vel_base - giro, vel_base + giro)

        ev3.screen.clear()
        ev3.screen.draw_text(5, 10, "LINEA PERDIDA")
        ev3.screen.draw_text(5, 30, "t=" + str(ms_sin_linea) + "ms")
        lado_txt = "IZQ" if ultimo_lado == -1 else "DER"
        ev3.screen.draw_text(5, 50, "Buscando: " + lado_txt)

    wait(80)
