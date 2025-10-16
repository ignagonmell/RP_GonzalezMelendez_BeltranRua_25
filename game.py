# game.py
# Escape From Peru — pantalla completa con proporciones adaptadas automáticamente

import pygame
import random
import sys
import math

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

# --- cargar imagen de inicio y escalar a pantalla ---
def load_scaled(path):
    img = pygame.image.load(path).convert()
    return pygame.transform.scale(img, (WIDTH, HEIGHT))

# --- cargar y escalar imagen de fondo ---
def load_scaled_bg(path):
    img = pygame.image.load(path).convert()
    return pygame.transform.scale(img, (WIDTH, HEIGHT))

BG_IMAGE = load_scaled_bg("fondo.png")


START_BG = load_scaled("start.png")   # usa el nombre que guardaste
DEATH_BG = load_scaled("death.png")
GAMEOVER_BG = load_scaled("gameover.png")
WIN_BG = load_scaled("win.png")   # imagen de victoria a pantalla completa
RULES_BG = load_scaled("rules.png")


GROUND_Y = int(HEIGHT - 60 * SCALE)
pygame.display.set_caption("Escape From Peru")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("arial", int(42 * SCALE), bold=True)
font = pygame.font.SysFont("arial", int(22 * SCALE), bold=True)

# Colores
PURPLE = (148, 0, 211)
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


# ---------------------------
# UTILIDADES DE DIBUJO
# ---------------------------
def draw_background(scroll_x):
    # Fondo como imagen (ya la tienes cargada en BG_IMAGE)
    screen.blit(BG_IMAGE, (0, 0))

    # (opcional) parallax muy suave:
    bg_x = -int((scroll_x * 0.1) % WIDTH)
    screen.blit(BG_IMAGE, (bg_x, 0))
    screen.blit(BG_IMAGE, (bg_x + WIDTH, 0))

    # Degradado para contraste sobre el fondo, justo antes del suelo

    # Suelo y líneas (tal como tienes)
    pygame.draw.rect(screen, SAND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    for i in range(0, WIDTH, int(120 * SCALE)):
        pygame.draw.line(
            screen,
            (220, 200, 150),
            (i + int(scroll_x % (120 * SCALE)), GROUND_Y + int(20 * SCALE)),
            (i + int(40 * SCALE) + int(scroll_x % (120 * SCALE)), GROUND_Y + int(45 * SCALE)),
            int(2 * SCALE)
        )


# --- util para cargar y escalar imágenes con alfa ---
def load_image(path, w, h):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, (int(w), int(h)))


def draw_peru_flag(x, y, w=48, h=30, t=0.0):
    w, h = int(w * SCALE), int(h * SCALE)
    band_w = w // 3
    offset = int(3 * SCALE * math.sin(t * 6 + x * 0.05))
    pygame.draw.rect(screen, RED, (x, y, band_w, h))
    pygame.draw.rect(screen, WHITE, (x + band_w, y, band_w, h))
    pygame.draw.rect(screen, RED, (x + 2 * band_w, y, band_w, h + offset), border_radius=int(2 * SCALE))

# ---------------------------
# CLASES DE ENTIDADES
# ---------------------------
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
        if self.dead:
            return
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
        """Dibuja al personaje como un stickman morado proporcional al tamaño y escala."""
        # Centro del cuerpo
        cx = self.rect.centerx
        cy = self.rect.y + int(self.h * 0.45)

        # Color morado del personaje
        stick_color = (148, 0, 211)

        # Cabeza
        head_radius = int(self.h * 0.18)
        pygame.draw.circle(surf, stick_color, (cx, self.rect.y + head_radius + int(self.h * 0.05)), head_radius)

        # Cuerpo
        body_top = self.rect.y + int(self.h * 0.3)
        body_bottom = self.rect.y + int(self.h * 0.8)
        pygame.draw.line(surf, stick_color, (cx, body_top), (cx, body_bottom), int(3 * SCALE))

        # Brazos
        arm_y = self.rect.y + int(self.h * 0.45)
        arm_len = int(self.w * 0.7)
        pygame.draw.line(surf, stick_color, (cx - arm_len, arm_y), (cx + arm_len, arm_y), int(3 * SCALE))

        # Piernas
        leg_len = int(self.h * 0.35)
        leg_y = body_bottom
        pygame.draw.line(surf, stick_color, (cx, leg_y),
                        (cx - int(leg_len * 0.6), leg_y + leg_len), int(3 * SCALE))
        pygame.draw.line(surf, stick_color, (cx, leg_y),
                        (cx + int(leg_len * 0.6), leg_y + leg_len), int(3 * SCALE))


class Obstacle:
    # Tipos: 'llama' y 'cactus' (suelo), 'flecha' (aéreo)
    def __init__(self, speed):
        self.type = random.choice(["llama", "cactus", "cactus", "flecha", "flecha"])
        self.speed = speed * SCALE              # respetar escalado de movimiento
        self.x = WIDTH + int(20 * SCALE)

        # Tamaños base escalados y posición vertical
        if self.type == "llama":
            self.w, self.h = int(48 * SCALE), int(44 * SCALE)     # un poco más grande
            self.y = GROUND_Y - self.h
        elif self.type == "cactus":
            self.w = int(30 * SCALE)
            self.h = random.choice([int(40 * SCALE), int(55 * SCALE), int(68 * SCALE)])
            self.y = GROUND_Y - self.h
        else:  # flecha aérea
            self.w, self.h = int(56 * SCALE), int(16 * SCALE)
            self.y = random.choice([GROUND_Y - int(110 * SCALE),
                                     GROUND_Y - int(85 * SCALE),
                                     GROUND_Y - int(60 * SCALE)])

        # Rect y sprite
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Cargar sprite según tipo (si falta, caeremos a forma geométrica)
        try:
            if self.type == "llama":
                self.image = load_image("llama.png", self.w, self.h)
            elif self.type == "cactus":
                self.image = load_image("cactus.png", self.w, self.h)
            else:
                self.image = load_image("flecha.png", self.w, self.h)
        except Exception:
            self.image = None  # fallback gráfico

    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x)

    def draw(self, surf):
        if self.image:
            surf.blit(self.image, (self.rect.x, self.rect.y))
        else:
            # Fallback si no se encontraron imágenes (mantener jugable)
            if self.type == "llama":
                pygame.draw.rect(surf, DARK_BROWN, self.rect, border_radius=int(6 * SCALE))
                pygame.draw.circle(surf, BROWN, (self.rect.centerx + int(10 * SCALE),
                                                 self.rect.y + int(6 * SCALE)), int(6 * SCALE))
            elif self.type == "cactus":
                pygame.draw.rect(surf, GREEN, self.rect, border_radius=int(4 * SCALE))
            else:
                pygame.draw.rect(surf, (90, 60, 40), self.rect, border_radius=int(3 * SCALE))
                tip = (self.rect.right + int(8 * SCALE), self.rect.centery)
                tri = [(self.rect.right, self.rect.top - int(2 * SCALE)),
                       (self.rect.right, self.rect.bottom + int(2 * SCALE)),
                       tip]
                pygame.draw.polygon(surf, (160, 160, 160), tri)

class Coin:
    def __init__(self, speed):
        self.r = int(8 * SCALE)
        self.x = WIDTH + int(20 * SCALE)
        self.y = random.choice([GROUND_Y - int(100 * SCALE), GROUND_Y - int(70 * SCALE), GROUND_Y - int(40 * SCALE)])
        self.speed = speed * SCALE
        self.rect = pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def update(self, dt):
        self.x -= self.speed * dt
        self.rect.x = int(self.x - self.r)

    def draw(self, surf):
        pygame.draw.circle(surf, GOLD, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), self.r, int(2 * SCALE))

# ---------------------------
# PANTALLAS Y ANIMACIONES
# ---------------------------
def intro_animation():
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                # Empieza con ESPACIO (o cualquier tecla si prefieres)
                if e.key == pygame.K_SPACE:
                    return
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # Dibuja la imagen a pantalla completa
        screen.blit(START_BG, (0, 0))

        # Texto de “Press SPACE to start” centrado abajo
        prompt = font_big.render("", True, (240, 220, 150))
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, int(HEIGHT*0.82)))

        pygame.display.flip()
        clock.tick(FPS)

def rules_screen():
    """Pantalla intermedia: reglas (15 coins = win) con fade-in, 3 s visible y fade-out suave."""
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))

    # --- Fade in (aparece poco a poco) ---
    for alpha in range(0, 256, 5):  # pasos pequeños = transición más suave
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        img = RULES_BG.copy()
        img.set_alpha(alpha)
        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # --- Mantener visible 3 segundos ---
    t = 0.0
    while t < 3.0:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.blit(RULES_BG, (0, 0))
        pygame.display.flip()
        t += clock.tick(60) / 1000.0

    # --- Fade out (desaparece poco a poco) ---
    for alpha in range(255, -1, -4):  # pasos pequeños = desvanecimiento suave
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        img = RULES_BG.copy()
        img.set_alpha(alpha)
        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock.tick(60)




def death_animation(player, scroll_x, hold_seconds=3.0):
    """Fundido al negro, fundido de
       Después vuelve al flujo normal para mostrar la end_screen."""
    # 1) fade out desde el juego
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(0, 221, 10):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        draw_background(scroll_x)
        pygame.draw.line(screen, DARK_BROWN, (0, GROUND_Y), (WIDTH, GROUND_Y), int(3 * SCALE))
        player.draw(screen)
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # 2) fade in de la imagen de muerte (DEATH_BG)
    for alpha in range(0, 256, 8):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        img = DEATH_BG.copy()
        img.set_alpha(alpha)
        screen.blit(img, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # 3) mantener la imagen unos segundos y salir
    t = 0.0
    while t < hold_seconds:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.blit(DEATH_BG, (0, 0))
        pygame.display.flip()
        t += clock.tick(60) / 1000.0

    # al terminar, simplemente return: el bucle del juego hará return de score
    # y en main() aparecerá end_screen(score, best)
    return



def end_screen(score, best, coins):
    """Pantalla final con transición suave + texto centrado (Score/Coins)."""
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))

    # 1) Fade a negro desde el juego
    for alpha in range(0, 255, 10):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # 2) Fade in de la imagen de Game Over
    for alpha in range(0, 256, 8):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        img = GAMEOVER_BG.copy()
        img.set_alpha(alpha)
        screen.blit(img, (0, 0))

        # Texto centrado (estilo que ya venías usando)
        gold = (215, 202, 169)  # #d7caa9
        font_mid = pygame.font.SysFont("georgia", int(50 * SCALE), bold=True)
        text = font_mid.render(f"SCORE: {score}    COINS: {coins}", True, gold)
        screen.blit(text,
                    (WIDTH // 2 - text.get_width() // 2,
                     HEIGHT // 2 - text.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)

    # 3) Espera interacción: R para reiniciar, ESC para salir
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    return "restart"
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        screen.blit(GAMEOVER_BG, (0, 0))
        gold = (215, 202, 169)
        font_mid = pygame.font.SysFont("georgia", int(50 * SCALE), bold=True)
        text = font_mid.render(f"SCORE: {score}    COINS: {coins}", True, gold)
        screen.blit(text,
                    (WIDTH // 2 - text.get_width() // 2,
                     HEIGHT // 2 - text.get_height() // 2))
        pygame.display.flip()
        clock.tick(30)


def win_screen(score, best, coins):
    """Pantalla de victoria con fade-in y HUD centrado."""
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))

    # fundido a negro
    for alpha in range(0, 255, 10):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        fade.set_alpha(alpha)
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        clock.tick(60)

    # fundido de la imagen de victoria
    for alpha in range(0, 256, 8):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        img = WIN_BG.copy()
        img.set_alpha(alpha)
        screen.blit(img, (0, 0))

        # Texto centrado (SCORE y COINS) con el mismo estilo que game over
        
        pygame.display.flip()
        clock.tick(60)

    # esperar interacción (R / ESC), mostrando la imagen y el HUD centrado
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    return "restart"
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        screen.blit(WIN_BG, (0, 0))

        pygame.display.flip()
        clock.tick(30)



# ---------------------------
# BUCLE PRINCIPAL
# ---------------------------
def game_loop():
    player = Player()
    obstacles, coins = [], []
    score, spawn_timer, coin_timer, scroll_x = 0, 0, 0, 0
    coin_count = 0
    base_speed, speed, time_alive = 280, 280, 0.0

    while True:
        dt = clock.tick(FPS) / 1000.0
        time_alive += dt
        scroll_x += speed * dt * SCALE
        speed = base_speed + int(time_alive * 10)
        spawn_interval = max(0.9, 1.8 - time_alive * 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_UP):
                    player.jump()
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        keys = pygame.key.get_pressed()
        player.duck(keys[pygame.K_DOWN])
        spawn_timer += dt
        coin_timer += dt
        if spawn_timer >= spawn_interval:
            obstacles.append(Obstacle(speed))
            spawn_timer = 0
        if coin_timer >= random.uniform(1.8, 3.2):
            coins.append(Coin(speed))
            coin_timer = 0
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
        for o in obstacles:
            if player.rect.colliderect(o.rect):
                player.dead = True
                death_animation(player, scroll_x)
                return score, score, coin_count, False
        for c in coins[:]:
            if player.rect.colliderect(c.rect):
                score += 10
                coin_count += 1
                coins.remove(c)

            if coin_count >=10:
                    # no mostramos aquí la pantalla; solo avisamos al main
                    return score, score, coin_count, True
        draw_background(scroll_x)
        pygame.draw.line(screen, DARK_BROWN, (0, GROUND_Y), (WIDTH, GROUND_Y), int(3 * SCALE))
        for o in obstacles:
            o.draw(screen)
        for c in coins:
            c.draw(screen)
        player.draw(screen)
        # HUD (arriba derecha): Score y Coins
        hud_score = font.render(f"Score: {score}", True, BLACK)
        hud_coins = font.render(f"Coins: {coin_count}", True, BLACK)

        right = WIDTH - int(10 * SCALE)         # mismo margen que usas para Score
        top   = int(10 * SCALE)
        gap   = int(6 * SCALE)                   # separación entre líneas

        screen.blit(hud_score, (right - hud_score.get_width(), top))
        screen.blit(
            hud_coins,
            (right - hud_coins.get_width(), top + hud_score.get_height() + gap)
        )

        pygame.display.flip()

def main():
    intro_animation()   # pantalla de inicio
    rules_screen()      # pantalla intermedia (3 segundos con fade in/out)
    best = 0
    while True:
        score, best_candidate, coins, won = game_loop()
        best = max(best, best_candidate, score)
        if won:
            if win_screen(score, best, coins) == "restart":
                continue
        else:
            if end_screen(score, best, coins) == "restart":
                continue



if __name__ == "__main__":
    main()
