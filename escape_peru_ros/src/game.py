#!/usr/bin/env python3
import rospy
import pygame
import random
import sys
import math
import os
from escape_peru_ros.msg import user_msg
from std_msgs.msg import Int64, String

# ---------------------------
# UTILIDADES ROS
# ---------------------------
def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, filename)

# ---------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------
BASE_W, BASE_H = 900, 320
FPS = 60
GRAVITY = 0.8

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
SCALE_X = WIDTH / BASE_W
SCALE_Y = HEIGHT / BASE_H
SCALE = min(SCALE_X, SCALE_Y)

# Fuentes y Colores
font_big = pygame.font.SysFont("arial", int(42 * SCALE), bold=True)
font = pygame.font.SysFont("arial", int(22 * SCALE), bold=True)
font_mid = pygame.font.SysFont("georgia", int(50 * SCALE), bold=True)

PURPLE = (148, 0, 211)
SAND = (235, 214, 164)
DARK_BROWN = (95, 60, 20)
GOLD = (218, 165, 32)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

GROUND_Y = int(HEIGHT - 60 * SCALE)
clock = pygame.time.Clock()

# Carga de Assets
def load_scaled(path):
    full_path = get_asset_path(path)
    try:
        img = pygame.image.load(full_path).convert()
        return pygame.transform.scale(img, (WIDTH, HEIGHT))
    except Exception as e:
        rospy.logwarn(f"Error cargando {path}: {e}")
        return pygame.Surface((WIDTH, HEIGHT))

def load_image(path, w, h):
    full_path = get_asset_path(path)
    try:
        img = pygame.image.load(full_path).convert_alpha()
        return pygame.transform.smoothscale(img, (int(w), int(h)))
    except:
        return None

BG_IMAGE = load_scaled("fondo.png")
START_BG = load_scaled("start.png")
DEATH_BG = load_scaled("death.png")
GAMEOVER_BG = load_scaled("gameover.png")
WIN_BG = load_scaled("win.png")
RULES_BG = load_scaled("rules.png")

# ---------------------------
# ENTIDADES
# ---------------------------
def draw_background(scroll_x):
    screen.blit(BG_IMAGE, (0, 0))
    bg_x = -int((scroll_x * 0.1) % WIDTH)
    screen.blit(BG_IMAGE, (bg_x, 0))
    screen.blit(BG_IMAGE, (bg_x + WIDTH, 0))
    pygame.draw.rect(screen, SAND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.line(screen, DARK_BROWN, (0, GROUND_Y), (WIDTH, GROUND_Y), int(3 * SCALE))

class Player:
    def __init__(self):
        self.w = int(36 * SCALE)
        self.h = int(48 * SCALE)
        self.x = int(80 * SCALE)
        self.y = GROUND_Y - self.h
        self.vy = 0
        self.on_ground = True
        self.dead = False
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def jump(self):
        if self.on_ground and not self.dead:
            self.vy = -13 * SCALE
            self.on_ground = False

    def duck(self, is_down):
        if self.dead: return
        if is_down and self.on_ground:
            self.h = int(32 * SCALE)
        else:
            self.h = int(48 * SCALE)

    def update(self):
        self.vy += GRAVITY * SCALE
        self.y += self.vy
        if self.y >= GROUND_Y - self.h:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, surf):
        cx = self.rect.centerx
        stick_color = PURPLE
        head_radius = int(self.h * 0.18)
        pygame.draw.circle(surf, stick_color, (cx, self.rect.y + head_radius + int(self.h * 0.05)), head_radius)
        body_top = self.rect.y + int(self.h * 0.3)
        body_bottom = self.rect.y + int(self.h * 0.8)
        pygame.draw.line(surf, stick_color, (cx, body_top), (cx, body_bottom), int(3 * SCALE))
        arm_y = self.rect.y + int(self.h * 0.45)
        arm_len = int(self.w * 0.7)
        pygame.draw.line(surf, stick_color, (cx - arm_len, arm_y), (cx + arm_len, arm_y), int(3 * SCALE))
        leg_len = int(self.h * 0.35)
        leg_y = body_bottom
        pygame.draw.line(surf, stick_color, (cx, leg_y), (cx - int(leg_len * 0.6), leg_y + leg_len), int(3 * SCALE))
        pygame.draw.line(surf, stick_color, (cx, leg_y), (cx + int(leg_len * 0.6), leg_y + leg_len), int(3 * SCALE))

class Obstacle:
    def __init__(self, speed):
        self.type = random.choice(["llama", "cactus", "cactus", "flecha", "flecha"])
        self.speed = speed * SCALE
        self.x = WIDTH + int(20 * SCALE)
        if self.type == "llama":
            self.w, self.h = int(48 * SCALE), int(44 * SCALE)
            self.y = GROUND_Y - self.h
        elif self.type == "cactus":
            self.w, self.h = int(30 * SCALE), random.choice([int(40*SCALE), int(55*SCALE)])
            self.y = GROUND_Y - self.h
        else:
            self.w, self.h = int(56 * SCALE), int(16 * SCALE)
            self.y = random.choice([GROUND_Y - int(110*SCALE), GROUND_Y - int(85*SCALE)])
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)
        try:
            if self.type == "llama": self.image = load_image("llama.png", self.w, self.h)
            elif self.type == "cactus": self.image = load_image("cactus.png", self.w, self.h)
            else: self.image = load_image("flecha.png", self.w, self.h)
        except: self.image = None

    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x)

    def draw(self, surf):
        if self.image: surf.blit(self.image, (self.rect.x, self.rect.y))
        else: pygame.draw.rect(surf, (200, 50, 50), self.rect)

class Coin:
    def __init__(self, speed):
        self.r = int(8 * SCALE)
        self.x = WIDTH + int(20 * SCALE)
        self.y = random.choice([GROUND_Y - int(100*SCALE), GROUND_Y - int(70*SCALE)])
        self.speed = speed * SCALE
        self.rect = pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)
    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x - self.r)
    def draw(self, surf):
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.r)

# ---------------------------
# GAME NODE (PRINCIPAL)
# ---------------------------
class GameNode:
    def __init__(self):
        rospy.init_node('game_node', anonymous=True)
        
        # --- SUSCRIPTORES ---
        rospy.Subscriber('user_information', user_msg, self.user_callback)
        rospy.Subscriber('keyboard_control', String, self.control_callback) # ### NUEVO
        
        # --- PUBLICADORES ---
        self.result_pub = rospy.Publisher('result_information', Int64, queue_size=10) # ### NUEVO

        self.player_name = None
        self.username = None
        self.data_received = False
        
        self.ros_command = None # ### NUEVO: Variable para guardar el comando del control_node

        rospy.loginfo("GAME NODE STARTING...")

    def user_callback(self, msg):
        if not self.data_received:
            self.player_name = msg.name
            self.username = msg.username
            self.data_received = True
            rospy.loginfo(f"Datos recibidos: {self.username}")

    def control_callback(self, msg):
        """Callback para recibir movimientos del control_node"""
        self.ros_command = msg.data # Guardamos "UP", "DOWN", etc.

    def wait_for_user(self):
        while not self.data_received and not rospy.is_shutdown():
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
            screen.fill((0, 0, 0))
            txt = font.render("ESPERANDO INFO_USER...", True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))
            pygame.display.flip()
            clock.tick(10)

    def intro_animation(self):
        rospy.loginfo("Phase 1: Welcome phase started.")
        while not rospy.is_shutdown():
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE: return
            
            screen.blit(START_BG, (0, 0))
            if self.username:
                welcome_txt = font_big.render(f"HOLA {self.username.upper()}!", True, PURPLE)
                screen.blit(welcome_txt, (WIDTH//2 - welcome_txt.get_width()//2, HEIGHT * 0.3))
            pygame.display.flip()

    def rules_screen(self):
        # Muestra reglas (simplificado para ahorrar espacio, funcionalidad completa visual)
        for i in range(60): # Pequeño bucle de espera simulando fade
            screen.blit(RULES_BG, (0,0))
            pygame.display.flip()
            clock.tick(60)

    # --- PANTALLAS FINALES ---
    def death_animation(self, player, scroll_x):
        # Simplemente esperamos un poco mostrando muerte
        for i in range(60):
            screen.blit(DEATH_BG, (0,0))
            pygame.display.flip()
            clock.tick(60)

    def end_screen(self, score, coins):
        screen.blit(GAMEOVER_BG, (0,0))
        txt = font_mid.render(f"SCORE: {score}", True, (200, 200, 200))
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        rospy.sleep(2) # Pausa breve antes de poder salir

    def win_screen(self, score, coins):
        screen.blit(WIN_BG, (0,0))
        pygame.display.flip()
        rospy.sleep(2)

    # --- GAME LOOP ---
    def game_loop(self):
        rospy.loginfo("Phase 2: Game phase started.")
        player = Player()
        obstacles, coins = [], []
        score, coin_count = 0, 0
        scroll_x, speed, time_alive = 0, 280, 0.0
        spawn_timer, coin_timer = 0, 0

        while not rospy.is_shutdown():
            dt = clock.tick(FPS) / 1000.0
            time_alive += dt
            scroll_x += speed * dt * SCALE
            speed = 280 + int(time_alive * 10)

            # --- INPUTS (Teclado Local + ROS) ---
            keys = pygame.key.get_pressed()
            jump_cmd = False
            duck_cmd = False

            # Input Local
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_SPACE, pygame.K_UP): jump_cmd = True
                    if e.key == pygame.K_ESCAPE: sys.exit()
            
            if keys[pygame.K_DOWN]: duck_cmd = True

            # Input ROS (Aquí procesamos el mensaje del control_node)
            if self.ros_command == "UP":
                jump_cmd = True
                self.ros_command = None # Limpiamos el comando tras usarlo
            elif self.ros_command == "DOWN":
                duck_cmd = True
                # No limpiamos DOWN inmediatamente para permitir mantener agachado 
                # (aunque en string es un pulso, mejor limpiarlo para evitar agachado eterno)
                self.ros_command = None 

            # Ejecutar acciones
            if jump_cmd: player.jump()
            player.duck(duck_cmd)

            # Logica juego (Spawns, Updates, Collisions)
            spawn_timer += dt
            coin_timer += dt
            if spawn_timer >= max(0.9, 1.8 - time_alive * 0.05):
                obstacles.append(Obstacle(speed))
                spawn_timer = 0
            if coin_timer >= random.uniform(1.8, 3.2):
                coins.append(Coin(speed))
                coin_timer = 0

            player.update()
            for o in obstacles[:]:
                o.update(dt)
                if o.rect.right < 0: obstacles.remove(o); score += 5
                if player.rect.colliderect(o.rect):
                    rospy.loginfo("Final phase reached (Collision).")
                    return score, coin_count, False # PERDIÓ
            
            for c in coins[:]:
                c.update(dt)
                if c.rect.right < 0: coins.remove(c)
                if player.rect.colliderect(c.rect):
                    score += 10
                    coin_count += 1
                    coins.remove(c)
                    if coin_count >= 15:
                        rospy.loginfo("Final phase reached (Win).")
                        return score, coin_count, True # GANÓ

            # Dibujar
            draw_background(scroll_x)
            for o in obstacles: o.draw(screen)
            for c in coins: c.draw(screen)
            player.draw(screen)
            
            # HUD
            hud = font.render(f"Score: {score}", True, BLACK)
            screen.blit(hud, (WIDTH - hud.get_width() - 10, 10))
            pygame.display.flip()

    def run(self):
        self.wait_for_user()
        while not rospy.is_shutdown():
            self.intro_animation()
            self.rules_screen()
            
            score, coins, won = self.game_loop()
            
            # --- FASE 3: PUBLICAR RESULTADO (ROS) ---
            # Requisito: Publicar score al result_node
            score_msg = Int64()
            score_msg.data = score
            self.result_pub.publish(score_msg) # ### NUEVO
            rospy.loginfo(f"Puntuación publicada: {score}")

            if won: self.win_screen(score, coins)
            else: 
                self.death_animation(Player(), 0) # Animación rápida
                self.end_screen(score, coins)
            
            # Pausa para ver resultados y reiniciar
            rospy.sleep(3)

if __name__ == '__main__':
    try:
        GameNode().run()
    except rospy.ROSInterruptException:
        pass