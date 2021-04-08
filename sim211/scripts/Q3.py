#! /usr/bin/env python3
# -*- coding:utf-8 -*-

# Rodar com 
# roslaunch my_simulation rampa.launch

# Este código pode ser visto rodando em:  https://youtu.be/_XOmDGF49vM


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

import random 

from nav_msgs.msg import Odometry
from std_msgs.msg import Header


import visao_module


bridge = CvBridge()

cv_image = None
media = []
centro = []

area = 0.0 # Variavel com a area do maior contorno

resultados = [] # Criacao de uma variavel global para guardar os resultados vistos

x = 0
y = 0
z = 0 
id = 0

frame = "camera_link"
# frame = "head_camera"  # DESCOMENTE para usar com webcam USB via roslaunch tag_tracking usbcam


ponto_fuga = (320, 240)


def find_m_h(segmento):
    a = segmento[0]
    b = segmento[1]
    m = (b[1] - a[1])/(b[0] - a[0])
    h = a[1] - m*a[0]
    return m,h

def intersect_segs(seg1, seg2):
    m1,h1 = find_m_h(seg1)
    m2,h2 = find_m_h(seg2)
    x_i = (h2 - h1)/(m1-m2)
    y_i = m1*x_i + h1
    return x_i, y_i


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged


def morpho_limpa(mask):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    mask = cv2.morphologyEx( mask, cv2.MORPH_OPEN, kernel )
    mask = cv2.morphologyEx( mask, cv2.MORPH_CLOSE, kernel )    
    return mask


def crosshair(img, point, size, color):
    """ Desenha um crosshair centrado no point.
        point deve ser uma tupla (x,y)
        color é uma tupla R,G,B uint8
    """
    x,y = point
    cv2.line(img,(x - size,y),(x + size,y),color,5)
    cv2.line(img,(x,y - size),(x, y + size),color,5)


def encontra_pf(bgr_in):
    """
       Recebe imagem bgr e retorna
       tupla (x,y) com a posicao do ponto de fuga

    """
    bgr = bgr_in.copy()

    print()

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (50, 50, 50), (90, 255, 255 ))
    bordas = auto_canny(mask)


    print("Tamanho da tela", mask.shape) 


    lines = cv2.HoughLinesP(image = bordas, rho = 1, theta = math.pi/180.0, threshold = 40, lines= np.array([]), minLineLength = 30, maxLineGap = 5)


    if lines is None:
        return


    a,b,c = lines.shape

    


    # bordas = morpho_limpa(bordas)

    hough_img_rgb = cv2.cvtColor(bordas, cv2.COLOR_GRAY2BGR)


    neg = []
    pos = []

    for i in range(a):
        # Faz uma linha ligando o ponto inicial ao ponto final, com a cor vermelha (BGR)
        cv2.line(hough_img_rgb, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (80, 80, 80), 5, cv2.LINE_AA)
        x1, y1, x2, y2 = lines[i][0][0], lines[i][0][1], lines[i][0][2], lines[i][0][3]
        reta = ((x1, y1), (x2, y2))
        m = (y2 - y1)/ (x2 - x1)

        if m >= 0.1: 
            pos.append(reta) 
        elif m < -0.1:
            neg.append(reta)


    if len(neg) >=1 and len(pos)>=1:
        # Escolher algum para calcular ponto de fuga
        # Alternativas:
        # a. mais longa de cada lado
        # b. primeira
        # c. sortear
        rneg = random.choice(neg)
        rpos = random.choice(pos)

        cv2.line(hough_img_rgb, rneg[0], rneg[1], (0, 255, 0), 5, cv2.LINE_AA)
        cv2.line(hough_img_rgb, rpos[0], rpos[1], (255, 0, 0), 5, cv2.LINE_AA)


        pf = intersect_segs(rneg, rpos)

        # Tratamento apenas para caso em que intersecoes nao sao encontradas: 
        if not np.isnan(pf[0]) and not np.isnan(pf[1]) : 
            pfi = (int(pf[0]), int(pf[1]))
            crosshair(hough_img_rgb, pfi, 10, (255,255,255))
            global ponto_fuga 
            ponto_fuga = pfi

    cv2.imshow("Saida ", hough_img_rgb)






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

    try:
        temp_image = bridge.compressed_imgmsg_to_cv2(imagem, "bgr8")
        cv_image = temp_image.copy()
        cv2.imshow("cv_image", cv_image)
        pf = encontra_pf(cv_image)
        cv2.waitKey(1)
    except CvBridgeError as e:
        print('ex', e)
    
if __name__=="__main__":
    rospy.init_node("Q3")

    topico_imagem = "/camera/image/compressed"

    recebedor = rospy.Subscriber(topico_imagem, CompressedImage, roda_todo_frame, queue_size=4, buff_size = 2**24)

    print("Usando ", topico_imagem)

    velocidade_saida = rospy.Publisher("/cmd_vel", Twist, queue_size = 1)


    zero = Twist(Vector3(0,0,0), Vector3(0,0,0))
    esq = Twist(Vector3(0.1,0,0), Vector3(0,0,0.2))
    dire = Twist(Vector3(0.1,0,0), Vector3(0,0,-0.2))    
    frente = Twist(Vector3(0.3,0,0), Vector3(0,0,0))     


    tolerancia = 25


    centro  = 320
    margem = 12

    try:
        # Inicializando - por default gira no sentido anti-horário
        # vel = Twist(Vector3(0,0,0), Vector3(0,0,math.pi/10.0))
        
        while not rospy.is_shutdown():

            if ponto_fuga[0] <  centro - margem: 
                velocidade_saida.publish(esq)
                rospy.sleep(0.1)
                # velocidade_saida.publish(zero)
                #rospy.sleep(0.1)
            elif ponto_fuga[0] >  centro + margem: 
                velocidade_saida.publish(dire)
                rospy.sleep(0.1)
                #velocidade_saida.publish(zero)
                #rospy.sleep(0.1)
            else: 
                velocidade_saida.publish(frente)
                rospy.sleep(0.1)
                #velocidade_saida.publish(zero)
                #rospy.sleep(0.1)








            rospy.sleep(0.1)

    except rospy.ROSInterruptException:
        print("Ocorreu uma exceção com o rospy")


