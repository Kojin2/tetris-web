import pygame
import random
import sys
import time

pygame.init()

WIDTH, HEIGHT = 300, 600
BOARD_WIDTH, BOARD_HEIGHT = 10, 20
BLOCK_SIZE = WIDTH // BOARD_WIDTH
RIGHT_PANEL = 120
PANEL_HEIGHT = 120

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (60, 60, 60)
BLUE_BG = (20, 30, 70)
LIGHT_BLUE = (50, 150, 255)
GLOW_COLOR = (255, 255, 100)

COLORS = [
    (200, 50, 50), (50, 200, 50), (230, 230, 60),
    (180, 50, 180), (50, 180, 180), (180, 180, 50), (50, 180, 50)
]

buttons = {}
difficulty_buttons = {}
difficulty_speeds = {
    "Easy": 800,
    "Normal": 500,
    "Hard": 300,
    "Expert": 150
}
DIFFICULTY = 500  # デフォルトは Normal

screen = pygame.display.set_mode((WIDTH + RIGHT_PANEL, HEIGHT + PANEL_HEIGHT))
pygame.display.set_caption("Tetris Mobile")
font = pygame.font.SysFont("Arial", 20)
big_font = pygame.font.SysFont("Arial", 36)
clock = pygame.time.Clock()

tetrominoes = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 0], [0, 1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]]
]

def create_board():
    return [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]

def draw_text(text, pos, font_obj=None, color=WHITE):
    if not font_obj:
        font_obj = font
    screen.blit(font_obj.render(text, True, color), pos)

def draw_background():
    screen.fill(BLUE_BG)
    for x in range(BOARD_WIDTH + 1):
        pygame.draw.line(screen, GRAY, (x * BLOCK_SIZE, 0), (x * BLOCK_SIZE, HEIGHT))
    for y in range(BOARD_HEIGHT + 1):
        pygame.draw.line(screen, GRAY, (0, y * BLOCK_SIZE), (WIDTH, y * BLOCK_SIZE))
    pygame.draw.rect(screen, LIGHT_BLUE, (0, 0, WIDTH, HEIGHT), 4)

def draw_board(board, glow_rows=None):
    for y, row in enumerate(board):
        for x, cell in enumerate(row):
            if cell:
                color = GLOW_COLOR if glow_rows and y in glow_rows else COLORS[cell - 1]
                pygame.draw.rect(screen, color, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, BLACK, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_tetromino(shape, pos, color_idx):
    x_off, y_off = pos
    color = COLORS[color_idx]
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                rect = ((x + x_off) * BLOCK_SIZE, (y + y_off) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

def draw_next(piece, idx):
    offset_x, offset_y = WIDTH + 10, 80
    for y, row in enumerate(piece):
        for x, cell in enumerate(row):
            if cell:
                rect = (offset_x + x * BLOCK_SIZE, offset_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, COLORS[idx], rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

def rotate(shape):
    return [[shape[y][x] for y in reversed(range(len(shape)))] for x in range(len(shape[0]))]

def check_collision(board, shape, offset):
    off_x, off_y = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                nx, ny = x + off_x, y + off_y
                if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT or (ny >= 0 and board[ny][nx]):
                    return True
    return False

def merge_shape(board, shape, offset, color_idx):
    off_x, off_y = offset
    overflow = False
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                ny, nx = y + off_y, x + off_x
                if ny < 0:
                    overflow = True
                if 0 <= ny < BOARD_HEIGHT and 0 <= nx < BOARD_WIDTH:
                    board[ny][nx] = color_idx + 1
    return overflow

def clear_rows(board):
    full = [i for i, row in enumerate(board) if all(cell for cell in row)]
    for blink in range(3):
        draw_board(board, glow_rows=full)
        pygame.display.flip()
        pygame.time.wait(100)
        draw_board(board)
        pygame.display.flip()
        pygame.time.wait(100)
    for i in full:
        board.pop(i)
        board.insert(0, [0] * BOARD_WIDTH)
    return len(full)

def draw_virtual_pad():
    global buttons
    button_w = 60
    button_h = 40
    start_y = HEIGHT + 20
    btn_defs = [("Left", 10), ("Right", 80), ("Rotate", 150), ("Down", 220), ("Drop", 290)]
    buttons.clear()
    for name, x in btn_defs:
        rect = pygame.Rect(x, start_y, button_w, button_h)
        buttons[name] = rect
        pygame.draw.rect(screen, LIGHT_BLUE, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        draw_text(name, (x + 5, start_y + 10))

def handle_touch(pos, board, current, x, y):
    moved = False
    dropped = False
    for name, rect in buttons.items():
        if rect.collidepoint(pos):
            if name == "Left" and not check_collision(board, current, (x - 1, y)):
                x -= 1
            elif name == "Right" and not check_collision(board, current, (x + 1, y)):
                x += 1
            elif name == "Down" and not check_collision(board, current, (x, y + 1)):
                y += 1
            elif name == "Rotate":
                rot = rotate(current)
                if not check_collision(board, rot, (x, y)):
                    current[:] = rot
            elif name == "Drop":
                while not check_collision(board, current, (x, y + 1)):
                    y += 1
                dropped = True
    return x, y, moved, dropped

def show_start_screen():
    global DIFFICULTY
    running = True
    while running:
        screen.fill(BLUE_BG)
        draw_text("Select Difficulty", (WIDTH // 2 - 80, 100), big_font)

        x_start = 30
        for idx, (label, speed) in enumerate(difficulty_speeds.items()):
            rect = pygame.Rect(x_start + idx * 90, 200, 80, 40)
            difficulty_buttons[label] = rect
            pygame.draw.rect(screen, LIGHT_BLUE, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)
            draw_text(label, (rect.x + 10, rect.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for label, rect in difficulty_buttons.items():
                    if rect.collidepoint(event.pos):
                        DIFFICULTY = difficulty_speeds[label]
                        running = False

def main():
    show_start_screen()
    board = create_board()
    score = 0
    current_idx = random.randint(0, len(tetrominoes) - 1)
    current = tetrominoes[current_idx]
    next_idx = random.randint(0, len(tetrominoes) - 1)
    next_piece = tetrominoes[next_idx]
    x, y = BOARD_WIDTH // 2 - len(current[0]) // 2, -2
    game_over = False
    fall_timer = 0

    while True:
        dt = clock.tick(60)
        fall_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_LEFT and not check_collision(board, current, (x - 1, y)):
                    x -= 1
                elif event.key == pygame.K_RIGHT and not check_collision(board, current, (x + 1, y)):
                    x += 1
                elif event.key == pygame.K_DOWN and not check_collision(board, current, (x, y + 1)):
                    y += 1
                elif event.key == pygame.K_UP:
                    rot = rotate(current)
                    if not check_collision(board, rot, (x, y)):
                        current = rot
                elif event.key == pygame.K_SPACE:
                    while not check_collision(board, current, (x, y + 1)):
                        y += 1
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                x, y, _, dropped = handle_touch(event.pos, board, current, x, y)
                if dropped:
                    fall_timer = DIFFICULTY + 1

        if not game_over and fall_timer > DIFFICULTY:
            fall_timer = 0
            if not check_collision(board, current, (x, y + 1)):
                y += 1
            else:
                if merge_shape(board, current, (x, y), current_idx):
                    game_over = True
                score += clear_rows(board) * 100
                current_idx = next_idx
                current = tetrominoes[current_idx]
                next_idx = random.randint(0, len(tetrominoes) - 1)
                next_piece = tetrominoes[next_idx]
                x, y = BOARD_WIDTH // 2 - len(current[0]) // 2, -2

        draw_background()
        draw_board(board)
        if not game_over:
            draw_tetromino(current, (x, y), current_idx)
        draw_text(f"Score: {score}", (WIDTH + 10, 10))
        draw_text("Next:", (WIDTH + 10, 50))
        draw_next(next_piece, next_idx)
        draw_virtual_pad()
        if game_over:
            draw_text("Game Over", (WIDTH // 2 - 60, HEIGHT // 2), big_font, (255, 50, 50))
        pygame.display.flip()

if __name__ == "__main__":
    main()
