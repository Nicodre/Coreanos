#!/usr/bin/env pybricks-micropython
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port
from pybricks.tools import wait
from pybricks.robotics import DriveBase

motor_inferiorI = Motor(Port.B)
motor_inferiorD = Motor(Port.C)
motor_izquierdo = Motor(Port.A)
motor_derecho = Motor(Port.D)
sensor_izquierdo = ColorSensor(Port.S2)
sensor_derecho = ColorSensor(Port.S3)
robot = DriveBase(motor_izquierdo, motor_derecho, wheel_diameter=55, axle_track=120)
def sync_slaves():
    motor_inferiorI.run(motor_derecho.speed())
    motor_inferiorD.run(motor_izquierdo.speed())

VELOCIDAD = 50
GANANCIA_PROPORCIONAL = 8

while True:
    valor_izquierdo = sensor_izquierdo.reflection()
    valor_derecho = sensor_derecho.reflection()
    error = valor_izquierdo - valor_derecho
    velocidad_giro = GANANCIA_PROPORCIONAL * error
    robot.drive(VELOCIDAD, velocidad_giro)
    sync_slaves()
    wait(30)

if color_izq == Color.GREEN:
        if color_izq_anterior == Color.WHITE:
            bloque.screen.print("IZQ: VERDE VALIDO")
            bloque.speaker.beep()
            robot.stop()
            wait(500)
        elif color_izq_anterior == Color.BLACK:
            bloque.screen.print("IZQ: VERDE INVALIDO")
            bloque.speaker.beep()
            robot.stop()
            wait(500)


    # DERECHO: Verde después de blanco → válido
    if color_der == Color.GREEN:
        if color_der_anterior == Color.WHITE:
            bloque.screen.print("DER: VERDE VALIDO")
            bloque.speaker.beep()
            robot.stop()
            wait(500)
        elif color_der_anterior == Color.BLACK:
            bloque.screen.print("DER: VERDE INVALIDO")
            bloque.speaker.beep()
            robot.stop()
            wait(500)
