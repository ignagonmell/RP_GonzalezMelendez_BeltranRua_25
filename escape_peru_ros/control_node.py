#!/usr/bin/env python3
import rospy
import pygame
import sys
from std_msgs.msg import String

def run():
    rospy.init_node('control_node', anonymous=True)
    # Publicamos en el topic 'keyboard_control'
    pub = rospy.Publisher('keyboard_control', String, queue_size=10)
    rate = rospy.Rate(30) 

    pygame.init()
    # Ventana pequeña para capturar el foco
    screen = pygame.display.set_mode((400, 150)) 
    pygame.display.set_caption("MANDO ROS (Haz click aquí)")
    font = pygame.font.SysFont("arial", 24)
    
    rospy.loginfo("Mando listo. Teclas: Flechas, Espacio, R, ESC.")

    while not rospy.is_shutdown():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        
        keys = pygame.key.get_pressed()
        msg = String()
        status_text = "Esperando comando..."

        # --- Mapeo de teclas a Mensajes ROS ---
        # Movimiento
        if keys[pygame.K_UP]:       msg.data = "UP"
        elif keys[pygame.K_DOWN]:   msg.data = "DOWN"
        elif keys[pygame.K_LEFT]:   msg.data = "LEFT"
        elif keys[pygame.K_RIGHT]:  msg.data = "RIGHT"
        # Nuevas teclas de control
        elif keys[pygame.K_SPACE]:  msg.data = "SPACE"
        elif keys[pygame.K_r]:      msg.data = "R"
        elif keys[pygame.K_ESCAPE]: msg.data = "ESC"

        # Publicar si hay tecla pulsada
        if msg.data:
            pub.publish(msg)
            status_text = f"ENVIANDO: {msg.data}"

        # Dibujar interfaz
        screen.fill((50, 50, 50))
        text = font.render(status_text, True, (0, 255, 0) if msg.data else (200, 200, 200))
        text2 = font.render("[Espacio=Start] [R=Restart] [ESC=Salir]", True, (150, 150, 150))
        screen.blit(text, (20, 40))
        pygame.transform.scale(text2, (300, 20)) # Ajuste rápido visual
        screen.blit(pygame.font.SysFont("arial", 16).render("[Espacio=Start] [R=Restart] [ESC=Quit]", True, (150,150,150)), (20, 80))
        
        pygame.display.flip()
        rate.sleep()

if __name__ == '__main__':
    try:
        run()
    except rospy.ROSInterruptException:
        pass