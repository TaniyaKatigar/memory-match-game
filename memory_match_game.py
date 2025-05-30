import pygame
import sys
import random
import time
import os
import math
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Memory Match Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 123, 255)
LIGHT_BLUE = (173, 216, 230)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)

# Game constants
CARD_WIDTH = 80  # Reduced from 100
CARD_HEIGHT = 120  # Reduced from 140
CARD_MARGIN = 15  # Reduced from 20
GRID_OFFSET_X = 100  # Reduced from 150 to fit more cards horizontally
GRID_OFFSET_Y = 120
ANIMATION_SPEED = 5
FLIP_SPEED = 8
TRANSITION_SPEED = 15
FADE_SPEED = 10
SCROLL_SPEED = 15  # Speed of scrolling

# Scrolling variables
scroll_y = 0
max_scroll_y = 0  # Will be calculated based on card positions

# Create directories for assets if they don't exist
os.makedirs("assets/images", exist_ok=True)
os.makedirs("assets/sounds", exist_ok=True)

# Create placeholder card images
def create_card_images():
    # Create card back
    card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    card_back.fill(BLUE)
    # Add pattern to card back
    for i in range(0, CARD_WIDTH, 10):
        pygame.draw.line(card_back, LIGHT_BLUE, (i, 0), (i, CARD_HEIGHT), 2)
    for i in range(0, CARD_HEIGHT, 10):
        pygame.draw.line(card_back, LIGHT_BLUE, (0, i), (CARD_WIDTH, i), 2)
    pygame.draw.rect(card_back, WHITE, (5, 5, CARD_WIDTH-10, CARD_HEIGHT-10), 3)
    pygame.image.save(card_back, "assets/images/card_back.png")
    
    # Create card fronts with different symbols
    symbols = [
        (RED, "♥"), (GREEN, "♣"), (BLUE, "♠"), (PURPLE, "♦"),
        (YELLOW, "★"), (PINK, "●"), (WHITE, "♫"), (GREEN, "✿"),
        (RED, "♢"), (BLUE, "☂"), (PURPLE, "☯"), (YELLOW, "☀"),
        (PINK, "☁"), (WHITE, "☮"), (GREEN, "☘"), (RED, "❤")
    ]
    
    for i, (color, symbol) in enumerate(symbols):
        card_front = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        card_front.fill(WHITE)
        pygame.draw.rect(card_front, color, (5, 5, CARD_WIDTH-10, CARD_HEIGHT-10), 3)
        
        # Render symbol
        font = pygame.font.SysFont("Arial", 60, bold=True)
        text = font.render(symbol, True, color)
        text_rect = text.get_rect(center=(CARD_WIDTH//2, CARD_HEIGHT//2))
        card_front.blit(text, text_rect)
        
        # Add small symbols in corners
        small_font = pygame.font.SysFont("Arial", 20, bold=True)
        small_text = small_font.render(symbol, True, color)
        card_front.blit(small_text, (10, 10))
        card_front.blit(small_text, (CARD_WIDTH-25, CARD_HEIGHT-25))
        
        pygame.image.save(card_front, f"assets/images/card_{i+1}.png")

# Create sound effects
def create_sound_files():
    # This is just a placeholder - in a real game, you'd include actual sound files
    # For this example, we'll just create empty files to demonstrate the structure
    placeholder_sounds = ["flip", "match", "nomatch", "win", "background"]
    for sound in placeholder_sounds:
        with open(f"assets/sounds/{sound}.txt", "w") as f:
            f.write(f"Placeholder for {sound} sound effect")

# Create assets if they don't exist
if not os.path.exists("assets/images/card_back.png"):
    create_card_images()
    create_sound_files()

# Load images
card_back_img = pygame.image.load("assets/images/card_back.png")
card_images = [pygame.image.load(f"assets/images/card_{i+1}.png") for i in range(16)]  # Increased from 8 to 16 for more card types

# Load sounds (in a real game, you'd load actual sound files)
try:
    flip_sound = mixer.Sound("assets/sounds/flip.wav")
    match_sound = mixer.Sound("assets/sounds/match.wav")
    nomatch_sound = mixer.Sound("assets/sounds/nomatch.wav")
    win_sound = mixer.Sound("assets/sounds/win.wav")
    # Background music would be loaded and played here
except:
    # If sound files don't exist, create dummy sound objects
    class DummySound:
        def play(self): pass
    flip_sound = DummySound()
    match_sound = DummySound()
    nomatch_sound = DummySound()
    win_sound = DummySound()

# Fonts
title_font = pygame.font.SysFont("Arial", 48, bold=True)
button_font = pygame.font.SysFont("Arial", 32, bold=True)
info_font = pygame.font.SysFont("Arial", 24)

# Game states
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# Transition class for smooth screen transitions
class Transition:
    def __init__(self):
        self.is_active = False
        self.alpha = 0  # 0: transparent, 255: opaque
        self.fade_in = False
        self.fade_out = False
        self.next_state = None
        self.callback = None
        
    def start_fade_out(self, next_state=None, callback=None):
        self.is_active = True
        self.fade_in = False
        self.fade_out = True
        self.alpha = 0
        self.next_state = next_state
        self.callback = callback
        
    def start_fade_in(self):
        self.is_active = True
        self.fade_in = True
        self.fade_out = False
        self.alpha = 255
        
    def update(self):
        if not self.is_active:
            return False
            
        if self.fade_out:
            self.alpha += FADE_SPEED
            if self.alpha >= 255:
                self.alpha = 255
                self.fade_out = False
                # Transition to next state if specified
                if self.next_state is not None:
                    return True
                if self.callback:
                    self.callback()
                self.start_fade_in()
                
        elif self.fade_in:
            self.alpha -= FADE_SPEED
            if self.alpha <= 0:
                self.alpha = 0
                self.fade_in = False
                self.is_active = False
                
        return False
        
    def draw(self, screen):
        if self.is_active:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, self.alpha))
            screen.blit(fade_surface, (0, 0))

# Card class
class Card:
    def __init__(self, x, y, card_type):
        self.x = x
        self.y = y
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT
        self.card_type = card_type
        self.image = card_images[card_type - 1]
        self.is_flipped = False
        self.is_matched = False
        self.flip_progress = 0  # 0: showing back, 100: showing front
        self.is_flipping = False
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        
        # Animation properties
        self.original_x = x
        self.original_y = y
        self.target_x = x
        self.target_y = y
        self.scale = 1.0
        self.target_scale = 1.0
        self.rotation = 0
        self.entrance_delay = 0
        self.has_entered = False
        
    def set_entrance_delay(self, delay):
        self.entrance_delay = delay
        self.scale = 0.1
        self.rotation = random.randint(-30, 30)
        self.y = self.original_y - 100
        self.has_entered = False
        
    def draw(self):
        # Apply scale and rotation for entrance animation
        if not self.has_entered:
            card_surface = pygame.transform.rotozoom(
                card_back_img if self.flip_progress < 50 else self.image,
                self.rotation,
                self.scale
            )
            rect = card_surface.get_rect(center=(self.x + CARD_WIDTH//2, self.y + CARD_HEIGHT//2 - scroll_y))
            screen.blit(card_surface, rect.topleft)
            return
            
        # Calculate card width based on flip progress
        if self.is_flipping:
            flip_width = int(CARD_WIDTH * abs(50 - self.flip_progress) / 50)
            if flip_width < 5:
                flip_width = 5  # Minimum width during flip
        else:
            flip_width = CARD_WIDTH
            
        # Determine which image to show based on flip progress
        if self.flip_progress < 50:
            # Show back of card (flipping to front)
            card_surface = pygame.transform.scale(card_back_img, (flip_width, CARD_HEIGHT))
        else:
            # Show front of card (flipping to back)
            card_surface = pygame.transform.scale(self.image, (flip_width, CARD_HEIGHT))
            
        # Center the card at its position, adjusted for scrolling
        offset_x = (CARD_WIDTH - flip_width) // 2
        screen.blit(card_surface, (self.x + offset_x, self.y - scroll_y))
        
        # If card is matched, add a subtle highlight
        if self.is_matched:
            s = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            s.fill((255, 255, 255, 80))  # Semi-transparent white
            screen.blit(s, (self.x, self.y - scroll_y))
            
    def update(self):
        # Handle entrance animation
        if not self.has_entered:
            if self.entrance_delay > 0:
                self.entrance_delay -= 1
                return
                
            # Move toward original position
            self.y += (self.original_y - self.y) * 0.1
            self.scale += (1.0 - self.scale) * 0.1
            self.rotation *= 0.9
            
            if abs(self.y - self.original_y) < 1 and abs(self.scale - 1.0) < 0.01:
                self.y = self.original_y
                self.scale = 1.0
                self.rotation = 0
                self.has_entered = True
                
        # Handle flip animation
        if self.is_flipping:
            if not self.is_flipped:
                # Flipping from back to front
                self.flip_progress += FLIP_SPEED
                if self.flip_progress >= 100:
                    self.flip_progress = 100
                    self.is_flipping = False
                    self.is_flipped = True
            else:
                # Flipping from front to back
                self.flip_progress -= FLIP_SPEED
                if self.flip_progress <= 0:
                    self.flip_progress = 0
                    self.is_flipping = False
                    self.is_flipped = False
                    
    def flip(self):
        if not self.is_matched and not self.is_flipping:
            self.is_flipping = True
            flip_sound.play()
            
    def contains_point(self, point):
        return self.rect.collidepoint(point)

# Button class
class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=LIGHT_BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, self.rect, 3, border_radius=10)
        
        text_surf = button_font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def check_click(self, pos, click):
        return self.rect.collidepoint(pos) and click

# Particle effect for matches
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(5, 10)
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.lifetime = random.randint(30, 60)  # frames
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
        return self.lifetime > 0
        
    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

# Game class
class MemoryGame:
    def __init__(self):
        self.state = GameState.MENU
        self.grid_size = (4, 4)  # 4x4 grid = 16 cards = 8 pairs
        self.cards = []
        self.flipped_cards = []
        self.moves = 0
        self.matches = 0
        self.particles = []
        self.start_time = 0
        self.elapsed_time = 0
        self.is_checking = False
        self.check_timer = 0
        self.difficulty = "Medium"  # Easy, Medium, Hard
        self.transition = Transition()
        self.feedback_message = ""
        self.feedback_timer = 0
        
        # Create buttons
        self.start_button = Button(SCREEN_WIDTH//2 - 100, 300, 200, 60, "Start Game")
        self.easy_button = Button(SCREEN_WIDTH//2 - 220, 400, 120, 50, "Easy", GREEN)
        self.medium_button = Button(SCREEN_WIDTH//2 - 60, 400, 120, 50, "Medium", BLUE)
        self.hard_button = Button(SCREEN_WIDTH//2 + 100, 400, 120, 50, "Hard", RED)
        self.menu_button = Button(SCREEN_WIDTH//2 - 100, 400, 200, 60, "Main Menu")
        self.restart_button = Button(SCREEN_WIDTH//2 - 100, 480, 200, 60, "Play Again")
        
        # Set active difficulty button
        self.easy_button.is_hovered = False
        self.medium_button.is_hovered = True
        self.hard_button.is_hovered = False
        
    def setup_game(self):
        # Set grid size based on difficulty
        if self.difficulty == "Easy":
            self.grid_size = (3, 2)  # 6 cards = 3 pairs
        elif self.difficulty == "Medium":
            self.grid_size = (4, 3)  # 12 cards = 6 pairs
        else:  # Hard
            self.grid_size = (6, 3)  # 18 cards = 9 pairs (rearranged to fit better on screen)
            
        # Reset game state
        self.cards = []
        self.flipped_cards = []
        self.moves = 0
        self.matches = 0
        self.particles = []
        self.start_time = time.time()
        self.elapsed_time = 0
        self.is_checking = False
        
        # Reset scroll position
        global scroll_y, max_scroll_y
        scroll_y = 0
        
        # Create card pairs
        pairs_needed = (self.grid_size[0] * self.grid_size[1]) // 2
        card_types = list(range(1, pairs_needed + 1))
        card_types = card_types + card_types  # Duplicate to create pairs
        random.shuffle(card_types)
        
        # Create and position cards
        card_index = 0
        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                x = GRID_OFFSET_X + col * (CARD_WIDTH + CARD_MARGIN)
                y = GRID_OFFSET_Y + row * (CARD_HEIGHT + CARD_MARGIN)
                
                if card_index < len(card_types):
                    card = Card(x, y, card_types[card_index])
                    card.set_entrance_delay(card_index * 5)  # Stagger the entrance of cards
                    self.cards.append(card)
                    card_index += 1
        
        # Calculate max scroll value based on the bottom-most card
        if self.cards:
            bottom_card = max(self.cards, key=lambda card: card.y + card.height)
            max_card_bottom = bottom_card.y + bottom_card.height + 50  # Add some padding
            max_scroll_y = max(0, max_card_bottom - SCREEN_HEIGHT)
        
    def handle_events(self):
        # Only handle events if not in transition
        if self.transition.is_active:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        global scroll_y, max_scroll_y
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_clicked = True
                elif event.button == 4:  # Mouse wheel up
                    scroll_y = max(0, scroll_y - SCROLL_SPEED)
                elif event.button == 5:  # Mouse wheel down
                    scroll_y = min(max_scroll_y, scroll_y + SCROLL_SPEED)
                    
        if self.state == GameState.MENU:
            # Check button interactions
            self.start_button.check_hover(mouse_pos)
            self.easy_button.check_hover(mouse_pos)
            self.medium_button.check_hover(mouse_pos)
            self.hard_button.check_hover(mouse_pos)
            
            if self.start_button.check_click(mouse_pos, mouse_clicked):
                def start_game():
                    self.state = GameState.PLAYING
                    self.setup_game()
                self.transition.start_fade_out(callback=start_game)
                
            if self.easy_button.check_click(mouse_pos, mouse_clicked):
                self.difficulty = "Easy"
                self.easy_button.is_hovered = True
                self.medium_button.is_hovered = False
                self.hard_button.is_hovered = False
                # Visual feedback for selection
                self.easy_button.color = (0, 200, 0)  # Brighter green
                self.medium_button.color = BLUE
                self.hard_button.color = RED
                # Sound feedback
                flip_sound.play()
                # Text feedback
                self.feedback_message = "Easy mode selected!"
                self.feedback_timer = 90  # Show for 1.5 seconds
                
            if self.medium_button.check_click(mouse_pos, mouse_clicked):
                self.difficulty = "Medium"
                self.easy_button.is_hovered = False
                self.medium_button.is_hovered = True
                self.hard_button.is_hovered = False
                # Visual feedback for selection
                self.easy_button.color = GREEN
                self.medium_button.color = (0, 80, 200)  # Brighter blue
                self.hard_button.color = RED
                # Sound feedback
                flip_sound.play()
                # Text feedback
                self.feedback_message = "Medium mode selected!"
                self.feedback_timer = 90  # Show for 1.5 seconds
                
            if self.hard_button.check_click(mouse_pos, mouse_clicked):
                self.difficulty = "Hard"
                self.easy_button.is_hovered = False
                self.medium_button.is_hovered = False
                self.hard_button.is_hovered = True
                # Visual feedback for selection
                self.easy_button.color = GREEN
                self.medium_button.color = BLUE
                self.hard_button.color = (200, 0, 0)  # Brighter red
                # Sound feedback
                flip_sound.play()
                # Text feedback
                self.feedback_message = "Hard mode selected!"
                self.feedback_timer = 90  # Show for 1.5 seconds
                
        elif self.state == GameState.PLAYING:
            # Only allow card clicks if not currently checking a pair
            if not self.is_checking and mouse_clicked:
                # Adjust mouse position for scrolling
                adjusted_mouse_pos = (mouse_pos[0], mouse_pos[1] + scroll_y)
                for card in self.cards:
                    # Create a rect that accounts for scrolling
                    card_rect = pygame.Rect(card.x, card.y, card.width, card.height)
                    if card_rect.collidepoint(adjusted_mouse_pos) and not card.is_flipped and not card.is_matched:
                        if len(self.flipped_cards) < 2:
                            card.flip()
                            self.flipped_cards.append(card)
                            
                            if len(self.flipped_cards) == 2:
                                self.moves += 1
                                self.is_checking = True
                                self.check_timer = 60  # Wait 1 second before checking
                        break
                        
        elif self.state == GameState.GAME_OVER:
            # Check button interactions
            self.menu_button.check_hover(mouse_pos)
            self.restart_button.check_hover(mouse_pos)
            
            if self.menu_button.check_click(mouse_pos, mouse_clicked):
                def go_to_menu():
                    self.state = GameState.MENU
                self.transition.start_fade_out(callback=go_to_menu)
                
            if self.restart_button.check_click(mouse_pos, mouse_clicked):
                def restart_game():
                    self.state = GameState.PLAYING
                    self.setup_game()
                self.transition.start_fade_out(callback=restart_game)
                
    def update(self):
        # Update transition first
        state_changed = self.transition.update()
        
        # Update feedback message timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
            if self.feedback_timer <= 0:
                self.feedback_message = ""
        
        if self.state == GameState.PLAYING:
            # Update elapsed time
            self.elapsed_time = time.time() - self.start_time
            
            # Update cards
            for card in self.cards:
                card.update()
                
            # Check for matches after delay
            if self.is_checking:
                self.check_timer -= 1
                if self.check_timer <= 0:
                    self.check_for_match()
                    
            # Update particles
            self.particles = [p for p in self.particles if p.update()]
            
            # Check if game is over
            if self.matches == len(self.cards) // 2 and not self.transition.is_active:
                def end_game():
                    self.state = GameState.GAME_OVER
                    win_sound.play()
                self.transition.start_fade_out(callback=end_game)
                
    def check_for_match(self):
        if len(self.flipped_cards) == 2:
            card1, card2 = self.flipped_cards
            
            if card1.card_type == card2.card_type:
                # Match found
                card1.is_matched = True
                card2.is_matched = True
                self.matches += 1
                match_sound.play()
                
                # Create particles at both matched cards
                for _ in range(20):
                    self.particles.append(Particle(card1.x + CARD_WIDTH//2, card1.y + CARD_HEIGHT//2, YELLOW))
                    self.particles.append(Particle(card2.x + CARD_WIDTH//2, card2.y + CARD_HEIGHT//2, YELLOW))
            else:
                # No match
                card1.flip()
                card2.flip()
                nomatch_sound.play()
                
            self.flipped_cards = []
            self.is_checking = False
                
    def draw(self):
        if self.state == GameState.MENU:
            # Draw menu screen
            screen.fill(DARK_GRAY)
            
            # Draw background pattern
            for i in range(0, SCREEN_WIDTH, 40):
                for j in range(0, SCREEN_HEIGHT, 40):
                    pygame.draw.rect(screen, (60, 60, 60), (i, j, 20, 20))
            
            # Title
            title_text = title_font.render("Memory Match Game", True, YELLOW)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
            
            # Instructions
            instructions = [
                "Match pairs of cards by flipping them two at a time.",
                "Remember card positions to find all matches quickly!",
                "Select difficulty level:"
            ]
            
            for i, instruction in enumerate(instructions):
                text = info_font.render(instruction, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 180 + i*30))
            
            # Draw buttons
            self.start_button.draw()
            self.easy_button.draw()
            self.medium_button.draw()
            self.hard_button.draw()
            
            # Draw feedback message if active
            if self.feedback_message:
                feedback_text = button_font.render(self.feedback_message, True, YELLOW)
                feedback_bg = pygame.Rect(
                    SCREEN_WIDTH//2 - feedback_text.get_width()//2 - 10,
                    470,
                    feedback_text.get_width() + 20,
                    40
                )
                pygame.draw.rect(screen, DARK_GRAY, feedback_bg)
                pygame.draw.rect(screen, YELLOW, feedback_bg, 2, border_radius=5)
                screen.blit(feedback_text, (SCREEN_WIDTH//2 - feedback_text.get_width()//2, 475))
            
        elif self.state == GameState.PLAYING:
            # Draw game screen
            screen.fill(DARK_GRAY)
            
            # Draw background pattern
            for i in range(0, SCREEN_WIDTH, 40):
                for j in range(0, SCREEN_HEIGHT, 40):
                    pygame.draw.rect(screen, (60, 60, 60), (i, j, 20, 20))
            
            # Draw cards
            for card in self.cards:
                card.draw()
                
            # Draw particles
            for particle in self.particles:
                particle.draw()
                
            # Draw game info (fixed position, not affected by scrolling)
            info_bg = pygame.Surface((SCREEN_WIDTH, 110))
            info_bg.fill(DARK_GRAY)
            info_bg.set_alpha(220)
            screen.blit(info_bg, (0, 0))
            
            moves_text = info_font.render(f"Moves: {self.moves}", True, WHITE)
            screen.blit(moves_text, (20, 20))
            
            matches_text = info_font.render(f"Matches: {self.matches}/{len(self.cards)//2}", True, WHITE)
            screen.blit(matches_text, (20, 50))
            
            time_text = info_font.render(f"Time: {int(self.elapsed_time)}s", True, WHITE)
            screen.blit(time_text, (20, 80))
            
            difficulty_text = info_font.render(f"Difficulty: {self.difficulty}", True, WHITE)
            screen.blit(difficulty_text, (SCREEN_WIDTH - 200, 20))
            
# Draw scrollbar if needed
            if max_scroll_y > 0:
                # Calculate scrollbar dimensions
                scrollbar_height = max(30, SCREEN_HEIGHT * SCREEN_HEIGHT / (SCREEN_HEIGHT + max_scroll_y))
                scrollbar_pos = (scroll_y / max_scroll_y) * (SCREEN_HEIGHT - scrollbar_height)
                
                # Draw scrollbar track
                pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH - 15, 0, 10, SCREEN_HEIGHT))
                
                # Draw scrollbar thumb
                pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 15, scrollbar_pos, 10, scrollbar_height), border_radius=5)
                
            # Draw scroll indicator if scrolling is available
            if max_scroll_y > 0:
                scroll_text = info_font.render("Use mouse wheel to scroll", True, YELLOW)
                screen.blit(scroll_text, (SCREEN_WIDTH//2 - scroll_text.get_width()//2, 80))
            
        elif self.state == GameState.GAME_OVER:
            # Draw game over screen
            screen.fill(DARK_GRAY)
            
            # Draw background pattern
            for i in range(0, SCREEN_WIDTH, 40):
                for j in range(0, SCREEN_HEIGHT, 40):
                    pygame.draw.rect(screen, (60, 60, 60), (i, j, 20, 20))
            
            # Victory message
            victory_text = title_font.render("Congratulations!", True, YELLOW)
            screen.blit(victory_text, (SCREEN_WIDTH//2 - victory_text.get_width()//2, 100))
            
            # Game stats
            stats = [
                f"Difficulty: {self.difficulty}",
                f"Moves: {self.moves}",
                f"Time: {int(self.elapsed_time)} seconds"
            ]
            
            for i, stat in enumerate(stats):
                text = info_font.render(stat, True, WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 180 + i*30))
            
            # Draw buttons
            self.menu_button.draw()
            self.restart_button.draw()
            
            # Draw decorative elements
            for i in range(20):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                size = random.randint(3, 8)
                color = random.choice([YELLOW, WHITE, PINK])
                pygame.draw.circle(screen, color, (x, y), size)
                
        # Draw transition effect on top
        self.transition.draw(screen)

# Main game loop
def main():
    game = MemoryGame()
    clock = pygame.time.Clock()
    
    while True:
        game.handle_events()
        game.update()
        game.draw()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
