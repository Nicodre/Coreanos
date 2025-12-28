#!/usr/bin/env pybricks-micropython

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Color
from pybricks.tools import wait
from pybricks.robotics import DriveBase
import time

bloque = EV3Brick()

motor_inferiorI = Motor(Port.B)
motor_inferiorD = Motor(Port.C)
motor_izquierdo = Motor(Port.A)
motor_derecho = Motor(Port.D)

sensor_izquierdo = ColorSensor(Port.S2)
sensor_derecho = ColorSensor(Port.S3)

robot = DriveBase(motor_izquierdo, motor_derecho, wheel_diameter=55, axle_track=120)

def sync_slaves():
    motor_inferiorD.run(motor_derecho.speed())
    motor_inferiorI.run(motor_izquierdo.speed())

#cambiamos sync slaves porque es mejor pare hacer los giros,pero podemos utilizarlo para seguir linea

def Mover(Izq, Der, Base):
    motor_izquierdo.run(Base + Izq)
    motor_inferiorI.run(Base + Izq)
    motor_derecho.run(Base + Der)
    motor_inferiorD.run(Base + Der)

def Parar():
    motor_izquierdo.run(0)
    motor_derecho.run(0)
    motor_inferiorD.run(0)
    motor_inferiorI.run(0)

# Configuración
VELOCIDAD = 120
GANANCIA_PROPORCIONAL = 7
CHECK = 0.3

# Necesarios para que el código funcione
ultimo_check = time.time()

color_der = sensor_derecho.color()
color_izq = sensor_izquierdo.color()

#  Guardar el color anterior (antes del verde)
color_anterior_der = sensor_derecho.color()
color_anterior_izq = sensor_izquierdo.color()

#seguidor de linea
while True:
    valor_izquierdo = sensor_izquierdo.reflection()
    valor_derecho = sensor_derecho.reflection()
    error = valor_izquierdo - valor_derecho
    velocidad_giro = GANANCIA_PROPORCIONAL * error
    Mover(velocidad_giro, -velocidad_giro, VELOCIDAD)
    #sync slaves()
    wait(30)

    # ahora ven color los dos a la vez para que cuando ambos vean verde no entren en la condición primero uno y después otro
   
    if time.time() - ultimo_check >= CHECK:
        color_izq = sensor_izquierdo.color()
        color_der = sensor_derecho.color()

        if color_izq == Color.RED and color_der == Color.RED:
            bloque.speaker.beep()
            bloque.screen.clear()
            bloque.screen.print("ROJO AMBOS")
            Parar()
            time.sleep(10)

        if (color_izq == Color.GREEN or color_der == Color.GREEN) and (color_anterior_izq == Color.BLACK or color_anterior_der == Color.BLACK) :  # si verde es inválido, reproduce un sonido
            bloque.speaker.beep()

        if (color_izq == Color.GREEN or color_der == Color.GREEN) and (color_anterior_izq != Color.BLACK or color_anterior_der != Color.BLACK): #si alguno ve verde, se fija que el color anterior no sea negro, para ver si es valido o no
            Parar()
            time.sleep(2) #cambiamos wait por time.sleep
            Mover(-20, -20, 0)
            time.sleep(1.3)
            Parar()
            time.sleep(2)
            color_izq = sensor_izquierdo.color()
            color_der = sensor_derecho.color()
            time.sleep(1)
        
            
            # Si los dos detectan verde, mostramos qué había antes
            if color_anterior_izq != Color.BLACK and color_anterior_der != Color.BLACK and color_izq == Color.GREEN and color_der == Color.GREEN :
                bloque.screen.clear()
                bloque.screen.print("Verde AMBOS")
                bloque.screen.print("IZQ antes:", color_anterior_izq)
                bloque.screen.print("DER antes:", color_anterior_der)
                ultimo_check = time.time()
                bloque.speaker.beep()
                Mover(100, -100, 0)  # Girar hacia atras
                time.sleep(2)
                while color_izq != Color.BLACK:
                    Mover(100, -100, 0)
                    color_izq = sensor_izquierdo.color()
                    color_der = sensor_derecho.color()
                Parar()
        
            if color_anterior_izq != Color.BLACK and color_izq == Color.GREEN and color_der != Color.GREEN:
                Parar()
                bloque.screen.clear()
                bloque.screen.print("Verde IZQ")
                bloque.screen.print("Antes:", color_anterior_izq)
                bloque.speaker.beep()
                Mover(95, 95, 0)
                time.sleep(2)
                Mover(-100,100, 0)
                time.sleep(2)
                while color_der != Color.BLACK:
                    Mover(-100, 100, 0)
                    color_der = sensor_derecho.color()
                Parar()   
        
            if color_anterior_der != Color.BLACK and color_der == Color.GREEN and color_izq != Color.GREEN:
                Parar()
                bloque.screen.clear()
                bloque.screen.print("Verde DER")
                bloque.screen.print("Antes:", color_anterior_der)
                bloque.speaker.beep()
                Mover(95, 95, 0) #Si avanza demasiado, bajar velocidad
                time.sleep(2)
                Mover(100, -100, 0)
                time.sleep(2) #Si se pasa de la línea, bajar este tiempo
                while color_izq != Color.BLACK:
                    Mover(100, -100, 0)
                    color_izq = sensor_izquierdo.color()
                Parar()
            

        if color_der != Color.GREEN: # Guardamos el color anterior mientras NO sea verde
            color_anterior_der = color_der

        if color_izq != Color.GREEN: # Guardamos el color anterior mientras NO sea verde
            color_anterior_izq = color_izq

        ultimo_check = time.time()
    