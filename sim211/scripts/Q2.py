#! /usr/bin/env python3
# -*- coding:utf-8 -*-

# Rodar com
# roslaunch my_simulation pista_s.launch

from __future__ import print_function, division
import rospy
import numpy as np
import numpy
import tf
import math
import cv2
import time
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, CompressedImage, LaserScan
from cv_bridge import CvBridge, CvBridgeError
from numpy import linalg
from tf import transformations
from tf import TransformerROS
import tf2_ros
from geometry_msgs.msg import Twist, Vector3, Pose, Vector3Stamped

from nav_msgs.msg import Odometry
from std_msgs.msg import Header


import visao_module


bridge = CvBridge()

cv_image = None
media = []
centro = []
atraso = 1.5E9 # 1 segundo e meio. Em nanossegundos


area = 0.0 # Variavel com a area do maior contorno

# Só usar se os relógios ROS da Raspberry e do Linux desktop estiverem sincronizados. 
# Descarta imagens que chegam atrasadas demais
check_delay = False 

resultados = [] # Criacao de uma variavel global para guardar os resultados vistos

x = 0
y = 0
z = 0 
id = 0

frame = "camera_link"
# frame = "head_camera"  # DESCOMENTE para usar com webcam USB via roslaunch tag_tracking usbcam

tfl = 0

tf_buffer = tf2_ros.Buffer()

dists = None

min_laser = 1000
max_laser = 0

def scaneou(dado):
    print("Faixa valida: ", dado.range_min , " - ", dado.range_max )
    print("Leituras:")
    global dists
    dists = np.array(dado.ranges).round(decimals=2)
    print(dists)
    global min_laser
    global max_laser 
    min_laser = dado.range_min 
    max_laser = dado.range_max
    #print("Intensities")
    #print(np.array(dado.intensities).round(decimals=2))


# A função a seguir é chamada sempre que chega um novo frame
def roda_todo_frame(imagem):
    print("frame")
    global cv_image
    global media
    global centro
    global resultados

    now = rospy.get_rostime()
    imgtime = imagem.header.stamp
    lag = now-imgtime # calcula o lag
    delay = lag.nsecs
    # print("delay ", "{:.3f}".format(delay/1.0E9))
    if delay > atraso and check_delay==True:
        print("Descartando por causa do delay do frame:", delay)
        return 
    try:
        temp_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        # Note que os resultados já são guardados automaticamente na variável
        # chamada resultados
        centro, saida_net, resultados =  visao_module.processa(temp_image)        
        for r in resultados:
            # print(r) - print feito para documentar e entender
            # o resultado            
            pass

        # Desnecessário - Hough e MobileNet já abrem janelas
        cv_image = saida_net.copy()
        cv2.imshow("cv_image", cv_image)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)


def valido(leitura):
    return min_laser <= leitura <= max_laser


def esta_proximo(laser):
    if valido(laser[5]) and valido(laser[355]):
        media = (laser[355] + laser[5])/2
        if media <= 0.8:
            return True
    return False
    


if __name__=="__main__":
    rospy.init_node("Q2")

    topico_imagem = "/camera/image/compressed"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)
    recebe_scan = rospy.Subscriber("/scan", LaserScan, scaneou)

    print("Usando ", topico_imagem)

    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)

    tolerancia = 25

    AVANCAR = 1
    CENTRALIZAR = 2
    FINAL = 3

    estado = AVANCAR 


    v = 0.2
    w = 0.3

    c = 320 # centro da tela - SEMPRE CHECAr RESOLUCAO


    # 
    zero = Twist(Vector3(0,0,0), Vector3(0,0,0.0))
    # 
    frente = Twist(Vector3(v,0,0), Vector3(0,0,0.0))
    # 
    direita = Twist(Vector3(0,0,0), Vector3(0,0, -w ))

    esquerda = Twist(Vector3(0,0,0), Vector3(0,0,w))

    proximo = False

    mg_centro = 10 # tolerancia de centralizar

    # Exemplo de categoria de resultados
    # [('chair', 86.965459585189819, (90, 141), (177, 265))]

    try:
        # Inicializando - por default gira no sentido anti-horário
        # vel = Twist(Vector3(0,0,0), Vector3(0,0,math.pi/10.0))
        
        while not rospy.is_shutdown():


            ### Gabarito: Avancar em frente ate ficar a 0.8m da parede 
            ## Risco - creeper atrapalhar 
            if estado == AVANCAR: 
                # avancar
                velocidade_saida.publish(frente)

                # checar se os lasers detectam parede
                # a 0.8 ou mais proximo
                if dists is not None:  
                    proximo = esta_proximo(dists)                    
                if proximo: 
                    estado = CENTRALIZAR
                    velocidade_saida.publish(zero)
                    rospy.sleep(0.5)
                    velocidade_saida.publish(esquerda)


            if estado == CENTRALIZAR:
                ### Gabarito: Girar ate ver o gato centralizado
                ### Risco: gato nao detectado
                for r in resultados:
                    mc = mg_centro
                    mx = 100
                    
                    if r[0] == "cat":
                        mx = (r[2][0] + r[3][0])/ 2
                        mx = int(mx)
                    
                    if c - mc < mx < c + mc:
                        estado = FINAL
                        velocidade_saida.publish(zero)
                    elif mx < c - mc:
                        # virar esq 
                        velocidade_saida.publish(esquerda)
                    elif  mx > c + mc:
                        # dirar direita  
                        velocidade_saida.publish(direita)
            if estado == FINAL:
                velocidade_saida.publish(zero)
                rospy.sleep(4.0)
                break
            rospy.sleep(0.1)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")


