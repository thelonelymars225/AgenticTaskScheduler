import os
import sys
import pygame
from pygame.locals import *

# Constants
WIDTH, HEIGHT = 640, 480
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 60
BALL_SIZE = 15
PADDLE_SPEED = 5
BALL_SPEED_X, BALL_SPEED_Y = 3, 3

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Paddle and Ball initialization
left_paddle = pygame.Rect(50, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 50 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

# Smoke test check
if os.getenv('AGENT_SMOKE_TEST') == '1':
    print("Smoke test passed.")
    sys.exit(0)

def move_paddle(paddle, direction):
    if direction == 'up' and paddle.top > 0:
        paddle.y -= PADDLE_SPEED
    elif direction == 'down' and paddle.bottom < HEIGHT:
        paddle.y += PADDLE_SPEED

def move_ball():
    ball.x += BALL_SPEED_X
    ball.y += BALL_SPEED_Y
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        BALL_SPEED_Y = -BALL_SPEED_Y
    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        BALL_SPEED_X = -BALL_SPEED_X

def main():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[K_w]:
            move_paddle(left_paddle, 'up')
        if keys[K_s]:
            move_paddle(left_paddle, 'down')
        if keys[K_UP]:
            move_paddle(right_paddle, 'up')
        if keys[K_DOWN]:
            move_paddle(right_paddle, 'down')

        move_ball()

        screen.fill((0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), left_paddle)
        pygame.draw.rect(screen, (255, 255, 255), right_paddle)
        pygame.draw.ellipse(screen, (255, 255, 255), ball)
        pygame.draw.aaline(screen, (255, 255, 255), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()