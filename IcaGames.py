import pygame
import random
import time
import math

# int
pygame.init()
pygame.mixer.init()

# constants
TILE_SIZE = 40
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
MENU, PLAYING, GAME_OVER = 0, 1, 2

# difficulty settings
difficulty_settings = {
    "easy":   {"time": 420, "rows": 13, "cols": 13}, # 7 minute timer
    "medium": {"time": 300, "rows": 19, "cols": 19}, # 5 minute timer
    "hard":   {"time": 150,  "rows": 21, "cols": 21} # 2.5 minute timer
}

# default screen
ROWS, COLS = 20, 20
WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE + 100

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ica Hunger Games")

# different fonts
font = pygame.font.Font("assets/PressStart2P.ttf", 18)
big_font = pygame.font.Font("assets/PressStart2P.ttf", 28)
small_font = pygame.font.Font("assets/PressStart2P.ttf", 12)

# asset images 
player_img = pygame.image.load("assets/ica.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (TILE_SIZE, TILE_SIZE))

foods = [
    pygame.transform.scale(
        pygame.image.load("assets/cake.png").convert_alpha(), (28, 28)
    ),
    pygame.transform.scale(
        pygame.image.load("assets/fries.png").convert_alpha(), (28, 28)
    ),
    pygame.transform.scale(
        pygame.image.load("assets/pizza.png").convert_alpha(), (28, 28)
    )
]

menu_bg_original = pygame.image.load("assets/icabackground.PNG").convert()
menu_bg = pygame.transform.scale(menu_bg_original, (WIDTH, HEIGHT))

# background music and sound effects
def play_menu_music():
    pygame.mixer.music.load("assets/menu.wav")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

def play_game_music():
    pygame.mixer.music.load("assets/gameplay.wav")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)

death_sound = pygame.mixer.Sound("assets/death.wav")
death_sound.set_volume(0.6)

# ghost/player classes
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self):
        screen.blit(player_img, (self.y * TILE_SIZE, self.x * TILE_SIZE))

class Ghost:
    def __init__(self, x, y, ghost_type, difficulty):
        self.x = x
        self.y = y
        self.type = ghost_type
        self.timer = 0
        self.difficulty = difficulty

        if difficulty == "easy":
            self.move_delay = random.randint(14, 18)

        elif difficulty == "medium":
            self.move_delay = random.randint(8, 12)

        else: 
            self.move_delay = random.randint(4, 7)

    def move(self, game_map, player):
        self.timer += 1

        if self.timer < self.move_delay:
            return

        self.timer = 0

        # easy mode: sometimes make mistakes
        if self.difficulty == "easy" and random.random() < 0.35:
            self.random_move(game_map)
            return

        # medium mode: occasional mistakes
        if self.difficulty == "medium" and random.random() < 0.15:
            self.random_move(game_map)
            return

        # normal behavior
        if self.type == "chaser":
            self.greedy_move(player.x, player.y, game_map)

        elif self.type == "ambush":
            tx = player.x + (player.x - self.x)
            ty = player.y + (player.y - self.y)
            self.greedy_move(tx, ty, game_map)

        elif self.type == "random":
            if self.difficulty == "hard" and random.random() < 0.5:
                self.greedy_move(player.x, player.y, game_map)
            else:
                self.random_move(game_map)

    def greedy_move(self, tx, ty, game_map):
        best = None
        best_dist = 9999

        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx = self.x + dx
            ny = self.y + dy

            if 0 <= nx < len(game_map) and 0 <= ny < len(game_map[0]):
                if game_map[nx][ny] != "#":
                    d = abs(tx - nx) + abs(ty - ny)
                    if d < best_dist:
                        best_dist = d
                        best = (nx, ny)

        if best:
            self.x, self.y = best

    def random_move(self, game_map):
        moves = [(1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(moves)

        for dx, dy in moves:
            nx = self.x + dx
            ny = self.y + dy

            if 0 <= nx < len(game_map) and 0 <= ny < len(game_map[0]):
                if game_map[nx][ny] != "#":
                    self.x, self.y = nx, ny
                    return

    def draw(self):
        color = RED if self.type == "chaser" else PINK if self.type == "ambush" else CYAN

        pygame.draw.circle(
            screen,
            color,
            (
                self.y * TILE_SIZE + TILE_SIZE // 2,
                self.x * TILE_SIZE + TILE_SIZE // 2
            ),
            15
        )

# generate the maps
def generate_maze(rows, cols):
    # force odd sizes internally
    if rows % 2 == 0:
        rows -= 1
    if cols % 2 == 0:
        cols -= 1

    grid = [["#" for _ in range(cols)] for _ in range(rows)]

    # carve perfect maze first
    stack = [(1, 1)]
    grid[1][1] = "."

    directions = [(2,0), (-2,0), (0,2), (0,-2)]

    while stack:
        x, y = stack[-1]
        neighbors = []

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 1 <= nx < rows - 1 and 1 <= ny < cols - 1:
                if grid[nx][ny] == "#":
                    neighbors.append((nx, ny, dx, dy))

        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)

            grid[x + dx // 2][y + dy // 2] = "."
            grid[nx][ny] = "."

            stack.append((nx, ny))
        else:
            stack.pop()

    # add extra loops/paths to ensure the map is not a single path
    extra_openings = (rows * cols) // 18

    for _ in range(extra_openings):
        x = random.randint(1, rows - 2)
        y = random.randint(1, cols - 2)

        if grid[x][y] == "#":
            # only break useful walls
            open_neighbors = 0

            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx = x + dx
                ny = y + dy

                if 0 <= nx < rows and 0 <= ny < cols:
                    if grid[nx][ny] == ".":
                        open_neighbors += 1

            if open_neighbors >= 2:
                grid[x][y] = "."

    # player spawn zone
    grid[1][1] = "P"
    grid[1][2] = "."
    grid[2][1] = "."
    grid[2][2] = "."

    return grid

def load_map(rows, cols):
    grid = generate_maze(rows, cols)

    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == "P":
                player = Player(i, j)
                grid[i][j] = " "
                return grid, player

def fill_food(game_map):
    for i in range(len(game_map)):
        for j in range(len(game_map[i])):
            if game_map[i][j] == "." or game_map[i][j] == " ":
                game_map[i][j] = random.randint(0, len(foods) - 1)

def draw_map(game_map):
    for i in range(len(game_map)):
        for j in range(len(game_map[i])):
            x = j * TILE_SIZE
            y = i * TILE_SIZE

            if game_map[i][j] == "#":
                pygame.draw.rect(screen, BLUE, (x, y, TILE_SIZE, TILE_SIZE))

            elif isinstance(game_map[i][j], int):
                img = foods[game_map[i][j]]
                screen.blit(img, (x + 6, y + 6))

# player movement
def move_player(game_map, player, dx, dy):
    nx = player.x + dx
    ny = player.y + dy

    if nx < 0 or ny < 0:
        return 0

    if nx >= len(game_map) or ny >= len(game_map[0]):
        return 0

    if game_map[nx][ny] == "#":
        return 0

    score = 0

    if isinstance(game_map[nx][ny], int):
        score = 10

    game_map[player.x][player.y] = " "
    player.x = nx
    player.y = ny
    game_map[nx][ny] = " "

    return score

# main menu
def draw_menu():
    screen.blit(menu_bg, (0, 0))

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title = big_font.render("ICA HUNGER GAMES", True, YELLOW)
    subtitle = small_font.render("RETRO FOOD CHAOS", True, CYAN)

    screen.blit(title, title.get_rect(center=(WIDTH // 2, 120)))
    screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 165)))

    button_width = 360
    button_height = 55
    start_y = 260
    gap = 80

    buttons = [
        ("PRESS 1 EASY", start_y),
        ("PRESS 2 MEDIUM", start_y + gap),
        ("PRESS 3 HARD", start_y + gap * 2)
    ]

    flash = YELLOW if pygame.time.get_ticks() % 1000 < 500 else WHITE

    for text, y in buttons:
        rect = pygame.Rect(
            WIDTH // 2 - button_width // 2,
            y,
            button_width,
            button_height
        )

        pygame.draw.rect(screen, flash, rect, 3)

        label = font.render(text, True, flash)
        screen.blit(label, label.get_rect(center=rect.center))

    controls = small_font.render("MOVE WITH WASD", True, PINK)
    warning = small_font.render("AVOID THE GHOSTS", True, RED)

    screen.blit(controls, controls.get_rect(center=(WIDTH // 2, HEIGHT - 60)))
    screen.blit(warning, warning.get_rect(center=(WIDTH // 2, HEIGHT - 30)))

# main function
def main():
    global ROWS, COLS, WIDTH, HEIGHT, screen, menu_bg

    state = MENU
    play_menu_music()

    clock = pygame.time.Clock()

    game_map = None
    player = None
    ghosts = []

    score = 0
    time_limit = 120
    start_time = 0
    current_difficulty = "easy"

    running = True

    while running:
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # -------- MENU --------
            if state == MENU:
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_1:
                        settings = difficulty_settings["easy"]
                        current_difficulty = "easy"

                    elif event.key == pygame.K_2:
                        settings = difficulty_settings["medium"]
                        current_difficulty = "medium"


                    elif event.key == pygame.K_3:
                        settings = difficulty_settings["hard"]
                        current_difficulty = "hard"

                    else:
                        settings = None

                    if settings:
                        ROWS = settings["rows"]
                        COLS = settings["cols"]
                        time_limit = settings["time"]

                        WIDTH = COLS * TILE_SIZE
                        HEIGHT = ROWS * TILE_SIZE + 100

                        screen = pygame.display.set_mode((WIDTH, HEIGHT))
                        menu_bg = pygame.transform.scale(
                            menu_bg_original, (WIDTH, HEIGHT)
                        )

                        game_map, player = load_map(ROWS, COLS)
                        fill_food(game_map)

                        ghosts = [
                                 Ghost(ROWS - 2, COLS - 2, "chaser", current_difficulty),
                                 Ghost(ROWS - 2, 1, "ambush", current_difficulty),
                                 Ghost(ROWS // 2, COLS // 2, "random", current_difficulty)
                        ]

                        score = 0
                        start_time = time.time()

                        play_game_music()
                        state = PLAYING

            # -------- PLAYING --------
            elif state == PLAYING:
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_w:
                        score += move_player(game_map, player, -1, 0)

                    elif event.key == pygame.K_s:
                        score += move_player(game_map, player, 1, 0)

                    elif event.key == pygame.K_a:
                        score += move_player(game_map, player, 0, -1)

                    elif event.key == pygame.K_d:
                        score += move_player(game_map, player, 0, 1)

            # -------- GAME OVER --------
            elif state == GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    play_menu_music()
                    state = MENU

        # ---------------- DRAW STATES ----------------
        if state == MENU:
            draw_menu()

        elif state == PLAYING:
            screen.fill(BLACK)

            elapsed = time.time() - start_time
            time_left = int(time_limit - elapsed)

            if time_left <= 0:
                state = GAME_OVER

            draw_map(game_map)
            player.draw()

            for ghost in ghosts:
                ghost.move(game_map, player)
                ghost.draw()

                if ghost.x == player.x and ghost.y == player.y:
                    death_sound.play()
                    pygame.mixer.music.stop()
                    state = GAME_OVER

            screen.blit(
                font.render(f"SCORE {score}", True, WHITE),
                (10, HEIGHT - 80)
            )

            screen.blit(
                font.render(f"TIME {time_left}", True, WHITE),
                (220, HEIGHT - 80)
            )

        elif state == GAME_OVER:
            screen.fill(BLACK)

            over = big_font.render("GAME OVER", True, RED)
            pts = font.render(f"SCORE {score}", True, WHITE)
            again = small_font.render("PRESS ANY KEY", True, WHITE)

            screen.blit(over, over.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
            screen.blit(pts, pts.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
            screen.blit(again, again.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
