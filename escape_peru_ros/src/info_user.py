#!/usr/bin/env python3
import rospy
from escape_peru_ros.msg import user_msg  # Importamos nuestro mensaje personalizado

class InfoUser:
    def __init__(self):
        # Inicializamos el nodo
        rospy.init_node('info_user', anonymous=True)
        
        # Creamos el Publisher
        # Topic: user_information [cite: 88]
        # Tipo de mensaje: user_msg [cite: 88]
        self.publisher = rospy.Publisher('user_information', user_msg, queue_size=10)
        
        self.rate = rospy.Rate(1) # Publicaremos a 1Hz (1 vez por segundo)

    def get_input(self):
        """Pide la información al usuario por terminal [cite: 86]"""
        print("\n--- BIENVENIDO A ESCAPE FROM PERU (ROS EDITION) ---")
        print("Por favor, introduce tus datos para comenzar:")
        
        name = input("Nombre real: ")
        username = input("Username: ")
        while True:
            try:
                age = int(input("Edad: "))
                break
            except ValueError:
                print("Por favor, introduce un número válido para la edad.")

        # Llenamos el mensaje personalizado [cite: 89]
        msg = user_msg()
        msg.name = name
        msg.username = username
        msg.age = age
        
        return msg

    def run(self):
        # 1. Obtener datos (solo una vez al principio)
        user_data_msg = self.get_input()
        
        rospy.loginfo(f"Datos recibidos. Publicando usuario: {user_data_msg.username}")
        
        # 2. Publicar en bucle mientras el nodo siga vivo
        # Esto asegura que el Game Node reciba el dato cuando se conecte.
        while not rospy.is_shutdown():
            self.publisher.publish(user_data_msg)
            self.rate.sleep()

if __name__ == '__main__':
    try:
        node = InfoUser()
        node.run()
    except rospy.ROSInterruptException:
        pass