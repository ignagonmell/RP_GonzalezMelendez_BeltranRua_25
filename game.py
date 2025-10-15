# game.py
# Escape From Peru — runner estilo Dino con estética peruana
# Contiene: animación de inicio y de muerte, obstáculos (flechas arriba; cactus/llamas suelo),
# HUD con puntuación, dificultad creciente, jugador morado, tamaño fijo.

import pygame
import random
import sys
import math

# ---------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------
WIDTH, HEIGHT = 900, 320
FPS = 60
GROUND_Y = HEIGHT - 60
GRAVITY = 0.8

# Colores
PURPLE = (148, 0, 211)           # jugador
SAND = (235, 214, 164)
SKY = (140, 205, 240)
BROWN = (120, 72, 0)
DARK_BROWN = (95, 60, 20)
SUN = (252, 212, 64)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (218, 165, 32)
GREEN = (34, 139, 34)
RED = (200, 30, 30)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape From Peru")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("arial", 42, bold=True)
font = pygame.font.SysFont("arial", 22, bold=True)

# ---------------------------
# UTILIDADES DE DIBUJO
# ---------------------------
def draw_background(scroll_x):
    # Cielo
    screen.fill(SKY)

    # Sol (Inti) que vibra levemente
    pygame.draw.circle(screen, SUN, (80, 80), 30)

    # Montañas andinas (parallax)
    for i in range(-1, 4):
        base_x = i * 300 + (scroll_x * 0.2) % 300
        pygame.draw.polygon(screen, (160, 180, 200), [
            (base_x + 50, GROUND_Y), (base_x + 150, 140), (base_x + 250, GROUND_Y)
        ])
    for i in range(-1, 4):
        base_x = i * 350 + (scroll_x * 0.5) % 350
        pygame.draw.polygon(screen, (120, 150, 180), [
            (base_x + 80, GROUND_Y), (base_x + 190, 120), (base_x + 300, GROUND_Y)
        ])

    # Suelo (Líneas de Nazca)
    pygame.draw.rect(screen, SAND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    for i in range(0, WIDTH, 120):
        pygame.draw.line(screen, (220, 200, 150), (i + (scroll_x % 120), GROUND_Y + 20),
                         (i + 40 + (scroll_x % 120), GROUND_Y + 45), 2)

def draw_peru_flag(x, y, w=48, h=30, t=0.0):
    """Bandera de Perú con efecto de onda senoidal en el borde derecho."""
    # Tres franjas: rojo, blanco, rojo
    band_w = w // 3
    # Ondita en el borde derecho
    offset = int(3 * math.sin(t * 6 + x * 0.05))
    pygame.draw.rect(screen, RED,   (x,         y, band_w, h))
    pygame.draw.rect(screen, WHITE, (x+band_w,  y, band_w, h))
    pygame.draw.rect(screen, RED,   (x+2*band_w, y, band_w, h+offset), border_radius=2)

# ---------------------------
# CLASES DE ENTIDADES
# ---------------------------
class Player:
    def __init__(self):
        self.w = 36
        self.h = 48
        self.x = 80
        self.y = GROUND_Y - self.h
        self.vy = 0
        self.on_ground = True
        self.dead = False
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def jump(self):
        if self.on_ground and not self.dead:
            self.vy = -13
            self.on_ground = False

    def duck(self, is_down):
        if self.dead:
            return
        if is_down and self.on_ground:
            self.h = 32
        else:
            self.h = 48

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy
        if self.y >= GROUND_Y - self.h:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def draw(self, surf):
        # “Indio” morado con penacho
        pygame.draw.rect(surf, PURPLE, self.rect, border_radius=6)
        px = self.rect.x + self.w - 6
        py = self.rect.y - 6
        pygame.draw.polygon(surf, (200, 0, 0), [(px, py), (px + 8, py + 2), (px, py + 10)])
        pygame.draw.polygon(surf, (0, 180, 0), [(px - 6, py + 4), (px + 2, py + 6), (px - 6, py + 14)])
        pygame.draw.polygon(surf, (0, 120, 200), [(px - 12, py + 8), (px - 2, py + 10), (px - 12, py + 18)])

class Obstacle:
    # Tipos: 'llama' y 'cactus' (suelo), 'flecha' (aéreo)
    def __init__(self, speed):
        self.type = random.choice(["llama", "cactus", "cactus", "flecha"])
        self.speed = speed
        self.x = WIDTH + 20

        if self.type == "llama":
            self.w, self.h = 36, 34
            self.y = GROUND_Y - self.h
        elif self.type == "cactus":
            self.w, self.h = 22, random.choice([28, 40])
            self.y = GROUND_Y - self.h
        else:  # flecha en el aire
            self.w, self.h = 40, 10
            self.y = random.choice([GROUND_Y - 110, GROUND_Y - 85, GROUND_Y - 60])

        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x)

    def draw(self, surf):
        if self.type == "llama":
            pygame.draw.rect(surf, DARK_BROWN, self.rect, border_radius=6)
            pygame.draw.circle(surf, BROWN, (self.rect.centerx + 10, self.rect.y + 6), 6)
        elif self.type == "cactus":
            pygame.draw.rect(surf, GREEN, self.rect, border_radius=4)
        else:  # flecha
            # Vástago
            pygame.draw.rect(surf, (90, 60, 40), self.rect, border_radius=3)
            # Punta triangular
            tip = (self.rect.right + 8, self.rect.centery)
            tri = [(self.rect.right, self.rect.top-2),
                   (self.rect.right, self.rect.bottom+2),
                   tip]
            pygame.draw.polygon(surf, (160, 160, 160), tri)
            # Plumas
            pygame.draw.line(surf, RED,   (self.rect.left-6, self.rect.top),    (self.rect.left, self.rect.top+2), 3)
            pygame.draw.line(surf, WHITE, (self.rect.left-6, self.rect.bottom), (self.rect.left, self.rect.bottom-2), 3)

class Coin:
    def __init__(self, speed):
        self.r = 8
        self.x = WIDTH + 20
        self.y = random.choice([GROUND_Y - 100, GROUND_Y - 70, GROUND_Y - 40])
        self.speed = speed
        self.rect = pygame.Rect(self.x - self.r, self.y - self.r, self.r*2, self.r*2)

    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x - self.r)

    def draw(self, surf):
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), self.r, 2)

# ---------------------------
# PANTALLAS Y ANIMACIONES
# ---------------------------
def intro_animation():
    t = 0.0
    llama_x = -60
    while t < 2.5:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN: return  # permitir saltar intro

        dt = clock.tick(FPS) / 1000.0
        t += dt
        llama_x += 160 * dt

        draw_background(scroll_x=t*120)
        # banderas ondeando
        for i in range(3):
            draw_peru_flag(560 + i*60, 30 + 10*i, t=t)
        # llama desfilando
        rect_llama = pygame.Rect(int(llama_x), GROUND_Y-34, 36, 34)
        pygame.draw.rect(screen, DARK_BROWN, rect_llama, border_radius=6)
        pygame.draw.circle(screen, BROWN, (rect_llama.centerx + 10, rect_llama.y + 6), 6)

        # título
        title = font_big.render("Escape From Peru", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 90))
        tip = font.render("Pulsa cualquier tecla para empezar", True, BLACK)
        screen.blit(tip, (WIDTH//2 - tip.get_width()//2, 150))
        pygame.display.flip()

def death_animation(player, scroll_x):
    # El jugador tropieza y cae mientras se tiñe la pantalla de rojo
    fall_vy = -6
    alpha = 0
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(alpha)
    overlay.fill((180, 0, 0))
    t = 0.0
    while t < 1.2:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()

        dt = clock.tick(FPS) / 1000.0
        t += dt
        fall_vy += GRAVITY * 1.5
        player.y += fall_vy
        if player.y > GROUND_Y - player.h: player.y = GROUND_Y - player.h
        player.rect = pygame.Rect(player.x, player.y, player.w, player.h)

        draw_background(scroll_x)
        pygame.draw.line(screen, DARK_BROWN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        player.draw(screen)

        alpha = min(220, alpha + 8)
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        text = font.render("¡Ay, caramba!", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, 40))
        pygame.display.flip()

def end_screen(score, best):
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: return "restart"
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        screen.fill(SKY)
        msg = font_big.render("Fin del juego", True, BLACK)
        sc = font.render(f"Puntuación: {score}   Mejor: {best}", True, BLACK)
        opt = font.render("Pulsa R para jugar de nuevo • ESC para salir", True, BLACK)
        screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 100))
        screen.blit(sc, (WIDTH//2 - sc.get_width()//2, 150))
        screen.blit(opt, (WIDTH//2 - opt.get_width()//2, 190))
        pygame.display.flip()
        clock.tick(FPS)

# ---------------------------
# BUCLE PRINCIPAL DEL JUEGO
# ---------------------------
def game_loop():
    player = Player()
    obstacles = []
    coins = []
    score = 0
    spawn_timer = 0
    coin_timer = 0
    scroll_x = 0
    best = 0

    base_speed = 280
    speed = base_speed
    time_alive = 0.0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        time_alive += dt
        scroll_x += speed * dt

        # Dificultad creciente
        speed = base_speed + int(time_alive * 10)
        spawn_interval = max(0.9, 1.8 - time_alive * 0.05)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_UP): player.jump()
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

        # Agacharse
        keys = pygame.key.get_pressed()
        player.duck(keys[pygame.K_DOWN])

        # Spawns
        spawn_timer += dt
        coin_timer += dt
        if spawn_timer >= spawn_interval:
            obstacles.append(Obstacle(speed))
            spawn_timer = 0
        if coin_timer >= random.uniform(1.8, 3.2):
            coins.append(Coin(speed * 0.95))
            coin_timer = 0

        # Update
        player.update()
        for o in obstacles[:]:
            o.update(dt)
            if o.rect.right < 0:
                obstacles.remove(o)
                score += 5
        for c in coins[:]:
            c.update(dt)
            if c.rect.right < 0:
                coins.remove(c)

        # Colisiones
        for o in obstacles:
            if player.rect.colliderect(o.rect):
                player.dead = True
                death_animation(player, scroll_x)  # ← animación de muerte
                best = max(best, score)
                return score, best

        for c in coins[:]:
            if player.rect.colliderect(c.rect):
                score += 10
                coins.remove(c)

        # Dibujo
        draw_background(scroll_x)
        pygame.draw.line(screen, DARK_BROWN, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        for o in obstacles: o.draw(screen)
        for c in coins: c.draw(screen)
        player.draw(screen)

        # HUD
        hud = font.render(f"Score: {score}", True, BLACK)
        screen.blit(hud, (WIDTH - 10 - hud.get_width(), 10))
        pygame.display.flip()

def main():
    intro_animation()             # ← animación peruana al inicio
    best = 0
    while True:
        score, best_candidate = game_loop()
        best = max(best, best_candidate, score)
        action = end_screen(score, best)
        if action == "restart":
            continue

if __name__ == "__main__":
    main()
