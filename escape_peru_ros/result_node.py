#!/usr/bin/env python3
import rospy
from escape_peru_ros.msg import user_msg
from std_msgs.msg import Int64

class ResultNode:
    def __init__(self):
        rospy.init_node('result_node', anonymous=True)
        
        # Suscriptores
        rospy.Subscriber('user_information', user_msg, self.user_callback)
        rospy.Subscriber('result_information', Int64, self.result_callback)
        
        self.username = "Desconocido"
        self.score_received = False
        
        rospy.loginfo("Result Node Esperando resultados...")
        rospy.spin()

    def user_callback(self, msg):
        # Guardamos el nombre del usuario cuando llega
        self.username = msg.username
        # No imprimimos nada aún, esperamos al score

    def result_callback(self, msg):
        # Cuando llega el score, mostramos el mensaje final como pide el PDF
        score = msg.data
        print("\n" + "="*30)
        print("      RESULTADOS DEL JUEGO      ")
        print("="*30)
        print(f"JUGADOR: {self.username}")
        print(f"PUNTUACIÓN FINAL: {score}")
        
        if score > 50: # Ejemplo simple
            print("MENSAJE: ¡Excelente trabajo!")
        else:
            print("MENSAJE: ¡Suerte la próxima vez!")
        print("="*30 + "\n")

if __name__ == '__main__':
    try:
        ResultNode()
    except rospy.ROSInterruptException:
        pass