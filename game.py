"""
Simple Pygame action-avoid/shooter game implementing requested features.
Save this file as game.py and run with Python 3.8+.
Requires: pygame (pip install pygame)

Features implemented:
1. Welcome screen that waits for key press to begin.
2. Player uses arrow keys to move; SPACE to shoot.
3. Enemies (red) spawn at right and move left automatically. Collectibles (green) spawn
   and give points when collected.
4. Collisions: hitting enemy reduces lives; if lives <= 0 the game ends. Bullets destroy enemies.
5. Score system: +10 for destroying enemy, +5 for collecting item, +1 for surviving time.
6. Current score & lives rendered on-screen.
7. End-game screen: shows final score and options to Play Again (R) or Quit (Q or ESC).
8. Increasing difficulty: as time passes enemies spawn faster and move faster.
9. FPS control via clock (default 60 FPS).
10. Player displayed as a purple circle.
11. Screen size configurable via SCREEN_WIDTH and SCREEN_HEIGHT variables.

Feel free to modify values at the top to tweak difficulty and sizes.
"""

import pygame
import random
import sys
import math
from dataclasses import dataclass

# === Configuration ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 10
PLAYER_SIZE = 28  # radius for circle
ENEMY_MIN_SPEED = 2
ENEMY_MAX_SPEED = 5
ENEMY_SPAWN_INTERVAL = 1500  # milliseconds (will decrease over time)
ITEM_SPAWN_INTERVAL = 4000
STARTING_LIVES = 3
SCORE_PER_ENEMY = 10
SCORE_PER_ITEM = 5
SURVIVAL_SCORE_INTERVAL = 1000  # every second +1 score

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (160, 32, 240)
RED = (220, 20, 60)
GREEN = (34, 177, 76)
YELLOW = (255, 215, 0)

# Pygame init
pygame.init()
font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 64)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Purple Runner: Avoid & Survive")
clock = pygame.time.Clock()

# Entities
@dataclass
class Player:
    x: float
    y: float
    speed: float
    radius: int
    lives: int

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

    def draw(self, surf):
        pygame.draw.circle(surf, PURPLE, (int(self.x), int(self.y)), self.radius)

@dataclass
class Enemy:
    x: float
    y: float
    vx: float
    size: int

    def rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

    def draw(self, surf):
        pygame.draw.rect(surf, RED, self.rect())

@dataclass
class Bullet:
    x: float
    y: float
    vx: float
    vy: float
    size: int = 6

    def rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, surf):
        pygame.draw.rect(surf, YELLOW, self.rect())

@dataclass
class Item:
    x: float
    y: float
    size: int = 14

    def rect(self):
        return pygame.Rect(self.x - self.size//2, self.y - self.size//2, self.size, self.size)

    def draw(self, surf):
        pygame.draw.rect(surf, GREEN, self.rect())

# Helper collision test
def collide_rect_circle(rect: pygame.Rect, cx: float, cy: float, radius: float) -> bool:
    # find closest point
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = closest_x - cx
    dy = closest_y - cy
    return dx*dx + dy*dy <= radius*radius

# Screens

def draw_text_centered(surf, text, font_obj, color, y):
    txt = font_obj.render(text, True, color)
    r = txt.get_rect(center=(SCREEN_WIDTH//2, y))
    surf.blit(txt, r)


def welcome_screen():
    screen.fill(BLACK)
    draw_text_centered(screen, "WELCOME TO PURPLE RUNNER", big_font, PURPLE, SCREEN_HEIGHT//3)
    draw_text_centered(screen, "Use arrow keys to move. SPACE to shoot.", font, WHITE, SCREEN_HEIGHT//2)
    draw_text_centered(screen, "Avoid red enemies, collect green items. Press any key to start.", font, WHITE, SCREEN_HEIGHT//2 + 40)
    draw_text_centered(screen, "Press ESC at any time to quit.", font, WHITE, SCREEN_HEIGHT//2 + 80)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                waiting = False
        clock.tick(15)


def end_game_screen(score):
    screen.fill(BLACK)
    draw_text_centered(screen, "GAME OVER", big_font, RED, SCREEN_HEIGHT//3)
    draw_text_centered(screen, f"Final Score: {score}", font, WHITE, SCREEN_HEIGHT//2)
    draw_text_centered(screen, "Press R to play again or Q/ESC to quit.", font, WHITE, SCREEN_HEIGHT//2 + 40)
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()
                elif event.key == pygame.K_r:
                    waiting = False
        clock.tick(15)

# Main game loop

def run_game():
    # initialize game state
    player = Player(SCREEN_WIDTH*0.1, SCREEN_HEIGHT//2, PLAYER_SPEED, PLAYER_SIZE, STARTING_LIVES)
    enemies = []
    bullets = []
    items = []

    score = 0
    last_enemy_spawn = pygame.time.get_ticks()
    enemy_spawn_interval = ENEMY_SPAWN_INTERVAL
    last_item_spawn = pygame.time.get_ticks()
    last_survival_score = pygame.time.get_ticks()
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # Input state
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            player.y -= player.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            player.y += player.speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.x -= player.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.x += player.speed
        if keys[pygame.K_SPACE]:
            # simple rate limit: allow shot every 200ms
            if not hasattr(player, 'last_shot') or now - player.last_shot > 200:
                bullets.append(Bullet(player.x + player.radius + 5, player.y, BULLET_SPEED, 0))
                player.last_shot = now

        # Player bounds
        player.x = max(player.radius, min(SCREEN_WIDTH - player.radius, player.x))
        player.y = max(player.radius, min(SCREEN_HEIGHT - player.radius, player.y))

        # Difficulty ramp: every 10 seconds, slightly increase enemy speed and spawn frequency
        elapsed_seconds = (now - start_time) / 1000.0
        difficulty_multiplier = 1.0 + (elapsed_seconds // 10) * 0.12  # +12% every 10s
        enemy_spawn_interval = max(400, int(ENEMY_SPAWN_INTERVAL / difficulty_multiplier))

        # Spawn enemies
        if now - last_enemy_spawn > enemy_spawn_interval:
            last_enemy_spawn = now
            size = random.randint(20, 40)
            y = random.randint(0, SCREEN_HEIGHT - size)
            base_speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
            vx = -base_speed * difficulty_multiplier
            enemies.append(Enemy(SCREEN_WIDTH + size, y, vx, size))

        # Spawn items
        if now - last_item_spawn > ITEM_SPAWN_INTERVAL:
            last_item_spawn = now
            y = random.randint(20, SCREEN_HEIGHT - 20)
            items.append(Item(SCREEN_WIDTH + 20, y))

        # Update enemies
        for e in enemies[:]:
            e.x += e.vx
            # remove off-screen
            if e.x + e.size < 0:
                enemies.remove(e)

        # Update bullets
        for b in bullets[:]:
            b.x += b.vx
            b.y += b.vy
            if b.x > SCREEN_WIDTH + 50 or b.x < -50:
                bullets.remove(b)

        # Update items (move left slowly)
        for it in items[:]:
            it.x -= 2 * difficulty_multiplier
            if it.x < -50:
                items.remove(it)

        # Bullet-enemy collisions
        for b in bullets[:]:
            for e in enemies[:]:
                if b.rect().colliderect(e.rect()):
                    try:
                        bullets.remove(b)
                    except ValueError:
                        pass
                    try:
                        enemies.remove(e)
                    except ValueError:
                        pass
                    score += SCORE_PER_ENEMY
                    break

        # Player-enemy collisions
        for e in enemies[:]:
            if collide_rect_circle(e.rect(), player.x, player.y, player.radius):
                try:
                    enemies.remove(e)
                except ValueError:
                    pass
                player.lives -= 1
                # brief flash or knockback could be added
                if player.lives <= 0:
                    return score

        # Player-item collisions
        for it in items[:]:
            if collide_rect_circle(it.rect(), player.x, player.y, player.radius):
                try:
                    items.remove(it)
                except ValueError:
                    pass
                score += SCORE_PER_ITEM

        # Survival score
        if now - last_survival_score > SURVIVAL_SCORE_INTERVAL:
            last_survival_score = now
            score += 1

        # Draw
        screen.fill((30, 30, 30))

        # Draw player
        player.draw(screen)

        # Draw enemies
        for e in enemies:
            e.draw(screen)

        # Draw bullets
        for b in bullets:
            b.draw(screen)

        # Draw items
        for it in items:
            it.draw(screen)

        # UI: score & lives
        score_surf = font.render(f"Score: {score}", True, WHITE)
        lives_surf = font.render(f"Lives: {player.lives}", True, WHITE)
        screen.blit(score_surf, (10, 10))
        screen.blit(lives_surf, (10, 36))

        # Difficulty indicator small bar
        diff_text = font.render(f"Difficulty x{difficulty_multiplier:.2f}", True, WHITE)
        screen.blit(diff_text, (SCREEN_WIDTH - 200, 10))

        pygame.display.flip()

    return score


if __name__ == '__main__':
    while True:
        welcome_screen()
        final_score = run_game()
        end_game_screen(final_score)
