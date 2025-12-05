#!/usr/bin/env python3
import rospy
import pygame
import random
import sys
import math
import os
from escape_peru_ros.msg import user_msg
from std_msgs.msg import Int64, String

# --- IMPORTAMOS LOS SERVICIOS (PARTE 2) ---
from escape_peru_ros.srv import GetUserScore, GetUserScoreResponse, SetGameDifficulty, SetGameDifficultyResponse

# --- UTILIDADES ROS ---
def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_dir, filename)

# --- CONFIGURACIÓN ---
BASE_W, BASE_H = 900, 320
FPS = 60
GRAVITY = 0.8

pygame.init()
# Ventana normal (no full screen) para ver otras terminales
screen = pygame.display.set_mode((1000, 360)) 
pygame.display.set_caption("ESCAPE FROM PERU - ROS NODE")

WIDTH, HEIGHT = screen.get_size()
SCALE_X = WIDTH / BASE_W
SCALE_Y = HEIGHT / BASE_H
SCALE = min(SCALE_X, SCALE_Y)

# Fuentes y Colores
font_big = pygame.font.SysFont("arial", int(42 * SCALE), bold=True)
font = pygame.font.SysFont("arial", int(22 * SCALE), bold=True)
font_mid = pygame.font.SysFont("georgia", int(50 * SCALE), bold=True)

# Colores definidos en el PDF [cite: 39-41]
PURPLE = (148, 0, 211) # Color 2 (Default)
RED = (200, 30, 30)    # Color 1
BLUE = (0, 0, 255)     # Color 3

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
    except: return None

BG_IMAGE = load_scaled("fondo.png")
START_BG = load_scaled("start.png")
DEATH_BG = load_scaled("death.png")
GAMEOVER_BG = load_scaled("gameover.png")
WIN_BG = load_scaled("win.png")
RULES_BG = load_scaled("rules.png")

# --- ENTIDADES ---
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
        if is_down and self.on_ground: self.h = int(32 * SCALE)
        else: self.h = int(48 * SCALE)

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
        
        # --- PARAMS (PARTE 2) ---
        # Leemos el parámetro 'change_player_color' cada frame para actualizar en tiempo real
        # 1: Rojo, 2: Morado (Default), 3: Azul 
        color_param = rospy.get_param('/change_player_color', 2)
        
        if color_param == 1:
            stick_color = RED
        elif color_param == 3:
            stick_color = BLUE
        else:
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

# --- GAME NODE PRINCIPAL ---
class GameNode:
    def __init__(self):
        rospy.init_node('game_node', anonymous=True)
        
        # --- PARAMS INICIALES ---
        rospy.set_param('/change_player_color', 2) # Default Morado
        rospy.set_param('/screen_param', 'phase1') # Default Phase 1
        
        # Subscribers & Publishers
        rospy.Subscriber('user_information', user_msg, self.user_callback)
        rospy.Subscriber('keyboard_control', String, self.control_callback)
        self.result_pub = rospy.Publisher('result_information', Int64, queue_size=10)

        # --- SERVICIOS (PARTE 2) ---
        self.srv_score = rospy.Service('user_score', GetUserScore, self.handle_get_score)
        self.srv_diff = rospy.Service('difficulty', SetGameDifficulty, self.handle_set_difficulty)

        # Estado del juego
        self.player_name = None
        self.username = None
        self.data_received = False
        self.ros_command = None 
        self.last_score = 0
        
        # Dificultad
        self.difficulty_mult = 1.0 
        self.game_state_str = "phase1" # Para control interno de la fase

        rospy.loginfo("GAME NODE STARTING (Services Ready)...")

    # --- CALLBACKS DE SERVICIOS ---
    
    def handle_get_score(self, req):
        """Servicio 1: Retorna el último score """
        rospy.loginfo(f"Solicitud de score para: {req.username}")
        # Retornamos el último score conocido
        return GetUserScoreResponse(self.last_score)

    def handle_set_difficulty(self, req):
        """Servicio 2: Cambia dificultad SOLO en Phase 1 [cite: 16-25]"""
        rospy.loginfo(f"Solicitud cambio dificultad a: {req.change_difficulty}")
        
        # Check: Solo permitido en phase1 (Intro)
        if self.game_state_str != "phase1":
            rospy.logwarn("Rechazado: No estamos en Phase 1")
            return SetGameDifficultyResponse(False)
        
        # Aplicar lógica
        if req.change_difficulty == "easy":
            self.difficulty_mult = 0.8
            rospy.loginfo("Dificultad: EASY (0.8x)")
        elif req.change_difficulty == "medium":
            self.difficulty_mult = 1.0
            rospy.loginfo("Dificultad: MEDIUM (1.0x)")
        elif req.change_difficulty == "hard":
            self.difficulty_mult = 1.5
            rospy.loginfo("Dificultad: HARD (1.5x)")
        else:
            return SetGameDifficultyResponse(False) # Input inválido
            
        return SetGameDifficultyResponse(True)

    # --- CALLBACKS TOPICS ---
    def user_callback(self, msg):
        if not self.data_received:
            self.player_name = msg.name
            self.username = msg.username
            self.data_received = True
            # PARAM: Guardar user_name [cite: 30]
            rospy.set_param('/user_name', self.username)
            rospy.loginfo(f"Datos recibidos: {self.username}")

    def control_callback(self, msg):
        self.ros_command = msg.data

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
        # PARAM: Actualizar screen_param a phase1 [cite: 43]
        rospy.set_param('/screen_param', 'phase1')
        self.game_state_str = "phase1"
        rospy.loginfo("Phase 1: Welcome phase started.")
        
        while not rospy.is_shutdown():
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
            
            start_game = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]: start_game = True
            if self.ros_command == "SPACE": start_game = True
            
            if start_game:
                self.ros_command = None
                return

            screen.blit(START_BG, (0, 0))
            
            # Mostrar nombre y dificultad actual
            if self.username:
                welcome_txt = font_big.render(f"HOLA {self.username.upper()}!", True, PURPLE)
                diff_txt = font.render(f"Velocidad: {self.difficulty_mult}x", True, BLACK)
                screen.blit(welcome_txt, (WIDTH//2 - welcome_txt.get_width()//2, HEIGHT * 0.3))
                screen.blit(diff_txt, (10, 10))

            prompt = font.render("Pulsa ESPACIO en el MANDO para empezar", True, WHITE)
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT * 0.85))
            
            pygame.display.flip()
            clock.tick(FPS)

    def rules_screen(self):
        for i in range(120):
            screen.blit(RULES_BG, (0,0))
            pygame.display.flip()
            clock.tick(60)

    # --- PANTALLAS FINALES ---
    def final_screen_loop(self, bg_image, score, coins):
        # PARAM: Actualizar screen_param a phase3 [cite: 43]
        rospy.set_param('/screen_param', 'phase3')
        self.game_state_str = "phase3"
        
        while not rospy.is_shutdown():
            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r] or self.ros_command == "R":
                self.ros_command = None
                return "restart"
            if keys[pygame.K_ESCAPE] or self.ros_command == "ESC":
                self.ros_command = None
                return "exit"

            screen.blit(bg_image, (0,0))
            if bg_image == GAMEOVER_BG or bg_image == WIN_BG:
                txt = font_mid.render(f"SCORE: {score}", True, (200, 200, 200))
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))
                hint = font.render("[R] Reiniciar   [ESC] Salir", True, WHITE)
                screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 50))
            
            pygame.display.flip()
            clock.tick(30)

    def death_animation(self, player, scroll_x):
        for i in range(30):
            screen.blit(DEATH_BG, (0,0))
            pygame.display.flip()
            clock.tick(60)

    # --- GAME LOOP ---
    def game_loop(self):
        # PARAM: Actualizar screen_param a phase2 [cite: 43]
        rospy.set_param('/screen_param', 'phase2')
        self.game_state_str = "phase2"
        rospy.loginfo("Phase 2: Game phase started.")
        
        player = Player()
        obstacles, coins = [], []
        score, coin_count = 0, 0
        scroll_x, speed, time_alive = 0, 280, 0.0
        spawn_timer, coin_timer = 0, 0

        # Aplicamos el multiplicador de dificultad
        current_base_speed = 280 * self.difficulty_mult

        while not rospy.is_shutdown():
            dt = clock.tick(FPS) / 1000.0
            time_alive += dt
            scroll_x += speed * dt * SCALE
            speed = current_base_speed + int(time_alive * 10)

            keys = pygame.key.get_pressed()
            jump_cmd = False
            duck_cmd = False
            
            if self.ros_command == "UP": jump_cmd = True
            elif self.ros_command == "DOWN": duck_cmd = True
            elif self.ros_command == "ESC": return score, coin_count, False

            for e in pygame.event.get():
                if e.type == pygame.QUIT: sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_SPACE, pygame.K_UP): jump_cmd = True

            if keys[pygame.K_DOWN]: duck_cmd = True

            if jump_cmd: player.jump()
            player.duck(duck_cmd)
            self.ros_command = None

            spawn_timer += dt
            coin_timer += dt
            # Ajustamos spawn rate con dificultad también (más rápido si es hard)
            spawn_limit = max(0.9, 1.8 - time_alive * 0.05) / self.difficulty_mult
            
            if spawn_timer >= spawn_limit:
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
                    return score, coin_count, False 
            
            for c in coins[:]:
                c.update(dt)
                if c.rect.right < 0: coins.remove(c)
                if player.rect.colliderect(c.rect):
                    score += 10
                    coin_count += 1
                    coins.remove(c)
                    if coin_count >= 15:
                        rospy.loginfo("Final phase reached (Win).")
                        return score, coin_count, True 

            draw_background(scroll_x)
            for o in obstacles: o.draw(screen)
            for c in coins: c.draw(screen)
            player.draw(screen)
            
            hud = font.render(f"Score: {score}", True, BLACK)
            screen.blit(hud, (WIDTH - hud.get_width() - 10, 10))
            pygame.display.flip()

    def run(self):
        self.wait_for_user()
        while not rospy.is_shutdown():
            self.intro_animation()
            self.rules_screen()
            
            score, coins, won = self.game_loop()
            self.last_score = score # Guardamos para el servicio GetUserScore
            
            score_msg = Int64()
            score_msg.data = score
            self.result_pub.publish(score_msg) 
            rospy.loginfo(f"Puntuación publicada: {score}")

            if won:
                action = self.final_screen_loop(WIN_BG, score, coins)
            else: 
                self.death_animation(Player(), 0)
                action = self.final_screen_loop(GAMEOVER_BG, score, coins)
            
            if action == "exit":
                break

if __name__ == '__main__':
    try:
        GameNode().run()
    except rospy.ROSInterruptException:
        pass