#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Este NÃO é um programa ROS

# GABARITO feito na aula de 06/04


from __future__ import print_function, division 

import cv2
import os,sys, os.path
import numpy as np

print("Rodando Python versão ", sys.version)
print("OpenCV versão: ", cv2.__version__)
print("Diretório de trabalho: ", os.getcwd())

# Arquivos necessários
# Baixe o arquivo em:
# https://github.com/Insper/robot20/blob/master/media/dominoes.mp4
    
video = "dominoes.mp4"


def conta_regioes(gray):
    pass

def processa(gray_img):

    gray= gray_img.copy()

    # 1. Limiarizar
    limiar = 150
    gray[gray <=limiar] =  0
    gray[gray > limiar] = 255

    #cv2.imshow("Limiar", gray)

    # 2. Achar limites da area mais clara

    i_min = gray.shape[0] + 1
    j_min = gray.shape[1] + 1
    

    i_max = -1 
    j_max = -1 

    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            if gray[i][j] == 255: 
                if i < i_min:
                    i_min = i
                if i > i_max:
                    i_max = i 
                if j < j_min: 
                    j_min = j 
                if j > j_max: 
                    j_max = j
    
    bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    cv2.rectangle(bgr, (j_min, i_min), (j_max, i_max), (0,0,255), 4)

    cv2.imshow("Limites", bgr ) 


          




    # 3. recortar em 2 sub imagens

    # 4. Contar contornos em cada





if __name__ == "__main__":

    # Inicializa a aquisição da webcam
    cap = cv2.VideoCapture(video)


    print("Se a janela com a imagem não aparecer em primeiro plano dê Alt-Tab")

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        if ret == False:
            #print("Codigo de retorno FALSO - problema para capturar o frame")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            #sys.exit(0)

        # Our operations on the frame come here
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        processa(gray)


        # NOTE que em testes a OpenCV 4.0 requereu frames em BGR para o cv2.imshow
        cv2.imshow('imagem', frame)

        if cv2.waitKey(33) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()


