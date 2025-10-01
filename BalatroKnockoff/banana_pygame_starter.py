# Banana (Balatro‑like) — Pygame Enhanced
# One‑file prototype with Jokers, Upgrades, Shop, and High Score (JSON).
# --- What’s new ---
# ✓ Joker system (Strategy pattern)  ✓ Upgrades (hand size, redraws, joker slots)
# ✓ Simple Shop UI (press S at any time; auto‑opens after clearing goal)  ✓ Coins from scoring
# ✓ High Score save/load (banana_highscores.json)
#
# Controls:
#   Use on-screen buttons: New Run, Deal, Play, Redraw, Quit
#
# Notes:
# - Keep it simple/robust for classroom demos; feel free to tweak numbers easily.
#
# Data Structures Demonstrated (for Data Structure course):
# - Queue (Deque): Deck for FIFO draw operations (O(n) popleft using list shift)
# - Stack (list): Discard pile for LIFO toss operations
# - Hash Table (Counter): Hand evaluation for O(1) average counting of ranks/suits
# - Set: Uniqueness checks in poker hand detection (e.g., straight, royal flush)

"""
Data Structures Summary for Course Submission:

This program implements a Balatro-inspired card game to demonstrate data structures.
All DS are custom-built from Python primitives (lists/dicts) to show internal mechanics.

- Deque (Custom Class):
  - Purpose: FIFO queue for card deck.
  - Implementation: Uses a list; append() is O(1), popleft() is O(n) due to element shifting.
  - Why Custom: Demonstrates queue internals; real deque would be O(1) with linked list.
  - Usage: Deck.draw()

- Counter (Custom Class):
  - Purpose: Hash table for counting card ranks/suits in hand evaluation.
  - Implementation: Inherits from dict; manual increment for O(1) average access.
  - Why Custom: Shows hash table behavior without library dependency.
  - Usage: eval_hand() for poker hand detection.

- DefaultDict (Custom Class):
  - Purpose: Dictionary with automatic default values for grouping.
  - Implementation: Subclasses dict with __missing__ for auto-creation.
  - Why Custom: Avoids KeyError in grouping operations.
  - Usage: Deck view for sorting cards by suit.

- List (Built-in):
  - Purpose: Stack for discard pile (LIFO) and undo system.
  - Why: Simple, efficient for small stacks; demonstrates LIFO without custom class.
  - Usage: Deck.toss().

- Set (Built-in):
  - Purpose: Uniqueness checks in straight/royal flush detection.
  - Why: Fast membership testing (O(1) average).
  - Usage: _is_straight(), _is_royal().

Overall: Code emphasizes DS efficiency, trade-offs (e.g., O(n) vs. O(1)), and practical application.
Run with: python banana_pygame_starter.py
"""

import pygame
import sys
import random
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from copy import deepcopy

# Custom Data Structures (implemented from scratch for DS course demonstration)
class Deque:
    """Custom deque implementation using a list for FIFO operations.
    Uses a list for storage; popleft shifts elements for FIFO behavior (O(n) time)."""
    def __init__(self, iterable=None):
        self.items = list(iterable) if iterable else []
    
    def append(self, item):
        self.items.append(item)
    
    def popleft(self):
        if not self.items:
            raise IndexError("pop from empty deque")
        return self.items.pop(0)  # Shift elements (O(n))
    
    def __len__(self):
        return len(self.items)
    
    def __iter__(self):
        return iter(self.items)

class Counter(dict):
    """Custom counter implementation using a dict for counting.
    Inherits from dict; increments counts manually for hash table behavior."""
    def __init__(self, iterable=None):
        super().__init__()
        if iterable:
            for item in iterable:
                self[item] = self.get(item, 0) + 1
    
    def __missing__(self, key):
        return 0  # For safe access like Counter

class DefaultDict(dict):
    """Custom defaultdict implementation using a dict with factory.
    Auto-creates values using default_factory for missing keys."""
    def __init__(self, default_factory):
        super().__init__()
        self.default_factory = default_factory
    
    def __missing__(self, key):
        self[key] = self.default_factory()
        return self[key]
# Balatro-like blind goals per round
BLIND_GOALS = [
    300,   # Round 1: Small Blind Ante 1
    600,   # 2: Big Blind
    900,  # 3: Boss Blind
    500,   # 4: Small Ante 2
    1000,  # 5: Big
    1500,  # 6: Boss
    800,   # 7: Small Ante 3
    1600,  # 8: Big
    2400,  # 9: Boss
    1100,  # 10: Small Ante 4
    2200,  # 11: Big
    3300,  # 12: Boss
    1500,  # 13: Small Ante 5
    3000,  # 14: Big
    4500,  # 15: Boss
    2000,  # 16: Small Ante 6
    4000,  # 17: Big
    6000, # 18: Boss
    2500,  # 19: Small Ante 7
    5000,  # 20: Big
    7500, # 21: Boss
    3000,  # 22: Small Ante 8
    6000,  # 23: Big
    9000, # 24: Boss
]

def get_blind_goal(round_no: int) -> int:
    if round_no <= len(BLIND_GOALS):
        return BLIND_GOALS[round_no - 1]
    else:
        # For rounds beyond, use the last goal multiplied by 1.5 or something
        return int(BLIND_GOALS[-1] * (1.5 ** (round_no - len(BLIND_GOALS))))

# -------------------------- Card System --------------------------
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
RANK_VALUE = {r: i for i, r in enumerate(["A","2","3","4","5","6","7","8","9","10","J","Q","K"], start=1)}
CARD_CHIPS = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}

@dataclass(frozen=True)
class Card:
    suit: str
    rank: str
    def show(self) -> str:
        return f"{self.rank}{self.suit}"
    def value(self) -> int:
        v = RANK_VALUE[self.rank]
        return 14 if self.rank == "A" else v

@dataclass
class Deck:
    # Using Deque as a queue for FIFO draw operations (O(n) popleft)
    # This demonstrates queue data structure usage in card drawing
    cards: Deque = field(default_factory=Deque)
    discard: List[Card] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    def build_standard(self):
        cards_list = []
        for s in SUITS:
            for r in RANKS:
                cards_list.append(Card(s, r))
        self.cards = Deque(cards_list)
        self.discard.clear()
        self.shuffle()

    def shuffle(self):
        # Convert to list for shuffling, then back to deque
        temp = list(self.cards)
        self.rng.shuffle(temp)
        self.cards = Deque(temp)

    def draw(self, n: int) -> List[Card]:
        out = []
        for _ in range(n):
            if not self.cards:
                break  # No recycling during round; discarded cards stay out
            out.append(self.cards.popleft())  # O(1) FIFO dequeue
        return out

    def toss(self, cards: List[Card]):
        # Using list as a stack (LIFO): append for push
        for c in cards:
            self.discard.append(c)

    def _recycle(self):
        if not self.discard:
            return
        # Add discarded cards back to deck
        while self.discard:
            self.cards.append(self.discard.pop())
        self.shuffle()

@dataclass
class Hand:
    cards: List[Card] = field(default_factory=list)
    max_size: int = 8

    def add(self, cs: List[Card]):
        space = self.max_size - len(self.cards)
        if space > 0:
            self.cards.extend(cs[:space])

    def remove_indices(self, idxs: List[int]) -> List[Card]:
        removed, keep = [], []
        idxs_set = set(idxs)
        for i, c in enumerate(self.cards):
            (removed if i in idxs_set else keep).append(c)
        self.cards = keep
        return removed

    def clear(self) -> List[Card]:
        out = self.cards
        self.cards = []
        return out

    def sort_by_rank(self):
        self.cards.sort(key=lambda c: c.value(), reverse=True)

    def sort_by_suit(self):
        self.cards.sort(key=lambda c: (SUITS.index(c.suit), c.value()), reverse=True)

# ---------------------- Poker Evaluation -------------------------
BASE_TABLE = {
    "High Card": (5, 1.0),
    "Pair": (10, 2.0),
    "Two Pair": (20, 2.0),
    "Three of a Kind": (30, 3.0),
    "Straight": (30, 4.0),
    "Flush": (35, 4.0),
    "Full House": (40, 4.0),
    "Four of a Kind": (60, 7.0),
    "Straight Flush": (100, 8.0),
    "Royal Flush": (100, 8.0),
}

def eval_hand(cards: List[Card]) -> Tuple[str, int, float]:
    n = len(cards)
    if n == 0:
        return ("Incomplete", 0, 0.0)

    vals = []
    for c in cards:
        vals.append(c.value())
    vals = sorted(vals)
    vals_ace_low = []
    for c in cards:
        if c.rank == "A":
            vals_ace_low.append(1)
        else:
            vals_ace_low.append(c.value())
    vals_ace_low = sorted(vals_ace_low)
    # Using Counter (hash table) for efficient counting operations
    rank_counts = Counter(c.rank for c in cards)
    suit_counts = Counter(c.suit for c in cards)

    counts = sorted(rank_counts.values(), reverse=True)

    # 5 ใบ: ตรวจครบทุกชนิด (รวม Straight/Flush)
    if n >= 5:
        is_flush = max(suit_counts.values(), default=0) == 5
        is_straight = _is_straight(vals) or _is_straight(vals_ace_low)
        if is_straight and is_flush and _is_royal(vals):
            kind = "Royal Flush"
        elif is_straight and is_flush:
            kind = "Straight Flush"
        elif counts[0] == 4:
            kind = "Four of a Kind"
        elif counts[0] == 3 and counts[1] == 2:
            kind = "Full House"
        elif is_flush:
            kind = "Flush"
        elif is_straight:
            kind = "Straight"
        elif counts[0] == 3:
            kind = "Three of a Kind"
        elif counts[0] == 2 and counts[1] == 2:
            kind = "Two Pair"
        elif counts[0] == 2:
            kind = "Pair"
        else:
            kind = "High Card"
    else:
        # 1–4 ใบ: เลือกชนิดที่เป็นไปได้สูงสุดตามจำนวนไพ่
        if counts[0] == 4:
            kind = "Four of a Kind"
        elif n == 4 and counts[0] == 3:
            kind = "Three of a Kind"
        elif n == 4 and counts[0] == 2 and counts[1] == 2:
            kind = "Two Pair"
        elif (n in (3,4)) and counts[0] == 3:
            kind = "Three of a Kind"
        elif (n in (2,3,4)) and counts[0] == 2 and (n == 3 or (n == 4 and counts[1] != 2)):
            kind = "Pair"
        elif n == 2 and counts[0] == 2:
            kind = "Pair"
        else:
            kind = "High Card"

    chips, mult = BASE_TABLE.get(kind, (0, 0.0))
    return (kind, chips, mult)

def _is_royal(vals: List[int]) -> bool:
    s = set(vals)
    return {10, 11, 12, 13, 14}.issubset(s)
def _is_straight(vals: List[int]) -> bool:
    uniq = sorted(set(vals))
    if len(uniq) < 5:
        return False
    for i in range(len(uniq) - 4):
        window = uniq[i:i+5]
        if all(window[j] + 1 == window[j+1] for j in range(4)):
            return True
    return False


# ----------------------- Joker / Upgrades ------------------------
@dataclass
class ScoreContext:
    base_chips: int
    base_mult: float
    hand_type: str
    cards: List[Card]
    coins: int = 0

class Joker:
    name: str = "Joker"
    desc: str = ""
    price: int = 10
    def apply(self, ctx: ScoreContext):
        pass

class BaseJoker(Joker):
    name = "Joker"
    desc = "+4 Mult"
    price = 10
    def apply(self, ctx: ScoreContext):
        ctx.base_mult += 4

class GreedyJoker(Joker):
    name = "Greedy Joker"
    desc = "+4 Mult when a Diamond is played"
    price = 15
    def apply(self, ctx: ScoreContext):
        if any(c.suit == "♦" for c in ctx.cards):
            ctx.base_mult += 4

class LustyJoker(Joker):
    name = "Lusty Joker"
    desc = "+4 Mult when a Heart is played"
    price = 15
    def apply(self, ctx: ScoreContext):
        if any(c.suit == "♥" for c in ctx.cards):
            ctx.base_mult += 4

class WrathfulJoker(Joker):
    name = "Wrathful Joker"
    desc = "+4 Mult when a Spade is played"
    price = 15
    def apply(self, ctx: ScoreContext):
        if any(c.suit == "♠" for c in ctx.cards):
            ctx.base_mult += 4

class GluttonousJoker(Joker):
    name = "Gluttonous Joker"
    desc = "+4 Mult when a Club is played"
    price = 15
    def apply(self, ctx: ScoreContext):
        if any(c.suit == "♣" for c in ctx.cards):
            ctx.base_mult += 4

class JollyJoker(Joker):
    name = "Jolly Joker"
    desc = "+8 Mult if the hand is a Pair"
    price = 20
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Pair":
            ctx.base_mult += 8

class ZanyJoker(Joker):
    name = "Zany Joker"
    desc = "+8 Mult if the hand is a Three of a Kind"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Three of a Kind":
            ctx.base_mult += 8

class MadJoker(Joker):
    name = "Mad Joker"
    desc = "+20 Mult if the hand is a Four of a Kind"
    price = 30
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Four of a Kind":
            ctx.base_mult += 20

class CrazyJoker(Joker):
    name = "Crazy Joker"
    desc = "+12 Mult if the hand is a Straight"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Straight":
            ctx.base_mult += 12

class DrollJoker(Joker):
    name = "Droll Joker"
    desc = "+10 Mult if the hand is a Flush"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Flush":
            ctx.base_mult += 10

class SlyJoker(Joker):
    name = "Sly Joker"
    desc = "+50 Chips if the hand is a Pair"
    price = 20
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Pair":
            ctx.base_chips += 50

class WilyJoker(Joker):
    name = "Wily Joker"
    desc = "+100 Chips if the hand is a Three of a Kind"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Three of a Kind":
            ctx.base_chips += 100

class CleverJoker(Joker):
    name = "Clever Joker"
    desc = "+150 Chips if the hand is a Four of a Kind"
    price = 30
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Four of a Kind":
            ctx.base_chips += 150

class DeviousJoker(Joker):
    name = "Devious Joker"
    desc = "+100 Chips if the hand is a Straight"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Straight":
            ctx.base_chips += 100

class CraftyJoker(Joker):
    name = "Crafty Joker"
    desc = "+80 Chips if the hand is a Flush"
    price = 25
    def apply(self, ctx: ScoreContext):
        if ctx.hand_type == "Flush":
            ctx.base_chips += 80

class TheMaskJoker(Joker):
    name = "The Mask"
    desc = "+5 Mult"
    price = 20
    def apply(self, ctx: ScoreContext):
        ctx.base_mult += 5

# ---- Upgrades (per run) ----
@dataclass
class Upgrades:
    hand_size_bonus: int = 0
    redraw_bonus: int = 0
    joker_slots_bonus: int = 0

# ------------------------- Game State ----------------------------
@dataclass
class Player:
    deck: Deck
    hand: Hand = field(default_factory=Hand)
    jokers: List[Joker] = field(default_factory=list)
    joker_slots: int = 5
    score: int = 0
    coins: int = 0
    upgrades: Upgrades = field(default_factory=Upgrades)

    def effective_hand_size(self) -> int:
        return 8 + self.upgrades.hand_size_bonus

    def effective_redraws(self) -> int:
        return 5 + self.upgrades.redraw_bonus

    def effective_joker_slots(self) -> int:
        return self.joker_slots + self.upgrades.joker_slots_bonus

@dataclass
class RoundRules:
    score_goal: int = 300
    hands_remaining: int = 5
    redraw_remaining: int = 10

    @classmethod
    def reset_round_values(cls):
        return {'hands_remaining': 5, 'redraw_remaining': 10}

@dataclass
class Game:
    player: Player
    rules: RoundRules = field(default_factory=RoundRules)
    round_no: int = 1
    mode: str = "PLAY"  # PLAY | SHOP | GAMEOVER | DECK

    def new_round(self):
        # Reset round score at the start of every new round
        self.player.score = 0
        reset_vals = RoundRules.reset_round_values()
        self.rules.hands_remaining = reset_vals['hands_remaining']
        self.rules.redraw_remaining = reset_vals['redraw_remaining']
        # Recycle discarded cards into deck for next round
        self.player.deck._recycle()
        # If no discarded cards, build standard deck
        if not self.player.deck.cards:
            self.player.deck.build_standard()
        # score_goal not changed here

# ------------------------ Pygame Frontend ------------------------
W, H = 1480, 720
CARD_W, CARD_H = 120, 170
SPACING = 30
TOP_Y = 360
BG = (18, 20, 24)
PANEL = (28, 32, 38)
CARD_BG = (44, 49, 58)
CARD_SEL = (90, 160, 255)
WHITE = (240, 244, 248)
MUTED = (170, 180, 190)
RED = (235, 95, 90)
BLACK = (34, 34, 34)
BLUE = (66, 135, 245)
GREEN = (74, 201, 133)
YELLOW = (240, 206, 88)
PURPLE = (180, 102, 255)


HS_FILE = "banana_highscores.json"

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Banana — Pygame Enhanced")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 24)
        self.big = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.small = pygame.font.SysFont("Segoe UI", 18)

        self.rng = random.Random()
        self.rng = random.Random()
        self.full_joker_pool = [
            (BaseJoker, {}, 10, "Joker", "+4 Mult"),
            (GreedyJoker, {}, 15, "Greedy Joker", "+4 Mult when a Diamond is played"),
            (LustyJoker, {}, 15, "Lusty Joker", "+4 Mult when a Heart is played"),
            (WrathfulJoker, {}, 15, "Wrathful Joker", "+4 Mult when a Spade is played"),
            (GluttonousJoker, {}, 15, "Gluttonous Joker", "+4 Mult when a Club is played"),
            (JollyJoker, {}, 20, "Jolly Joker", "+8 Mult if the hand is a Pair"),
            (ZanyJoker, {}, 25, "Zany Joker", "+8 Mult if the hand is a Three of a Kind"),
            (MadJoker, {}, 30, "Mad Joker", "+20 Mult if the hand is a Four of a Kind"),
            (TheMaskJoker, {}, 20, "The Mask", "+5 Mult"),
            (CrazyJoker, {}, 25, "Crazy Joker", "+12 Mult if the hand is a Straight"),
            (DrollJoker, {}, 25, "Droll Joker", "+10 Mult if the hand is a Flush"),
            (SlyJoker, {}, 20, "Sly Joker", "+50 Chips if the hand is a Pair"),
            (WilyJoker, {}, 25, "Wily Joker", "+100 Chips if the hand is a Three of a Kind"),
            (CleverJoker, {}, 30, "Clever Joker", "+150 Chips if the hand is a Four of a Kind"),
            (DeviousJoker, {}, 25, "Devious Joker", "+100 Chips if the hand is a Straight"),
            (CraftyJoker, {}, 25, "Crafty Joker", "+80 Chips if the hand is a Flush"),
        ]
        self.joker_deck = self.full_joker_pool.copy()
        self.deck = Deck(rng=self.rng)
        self.deck.build_standard()
        self.player = Player(deck=self.deck)
        self.player.hand.max_size = self.player.effective_hand_size()
        self.game = Game(player=self.player)

        self.selected: List[int] = []
        self.message = "Use buttons: New Run, Deal, Play, Redraw."
        self.sort_mode = "rank"  # "rank" or "suit"
        self.shop_items = []  # list of ShopItem
        self.shop_rects: List[pygame.Rect] = []
        self.shop_available = False
        self.close_button_rect = pygame.Rect(W//2 - 100, H - 60, 200, 40)
        self.close_deck_button_rect = pygame.Rect(W//2 - 100, H - 60, 200, 40)
        self.load_highscores()
        self.setup_buttons()

    def setup_buttons(self):
        # Define on-screen buttons for main actions
        button_y = 280
        button_w, button_h = 120, 40
        gap = 10
        self.buttons = [
            {"text": "New Run", "rect": pygame.Rect(40, button_y, button_w, button_h), "action": self.new_run},
            {"text": "Deal", "rect": pygame.Rect(40 + (button_w + gap), button_y, button_w, button_h), "action": self.deal_up_to_full},
            {"text": "Play", "rect": pygame.Rect(40 + 2*(button_w + gap), button_y, button_w, button_h), "action": lambda: (self.deal_up_to_full(), self.play_hand())},
            {"text": "Redraw", "rect": pygame.Rect(40 + 3*(button_w + gap), button_y, button_w, button_h), "action": self.redraw},
            {"text": "Sort", "rect": pygame.Rect(40 + 4*(button_w + gap), button_y, button_w, button_h), "action": self.toggle_sort},
            {"text": "Deck", "rect": pygame.Rect(40 + 5*(button_w + gap), button_y, button_w, button_h), "action": lambda: self.open_deck() if self.game.mode == "PLAY" else self.close_deck()},
            {"text": "Quit", "rect": pygame.Rect(40 + 6*(button_w + gap), button_y, button_w, button_h), "action": lambda: (pygame.quit(), sys.exit(0))},
        ]



    def toggle_sort(self):
        self.sort_mode = "suit" if self.sort_mode == "rank" else "rank"
        self.sort_hand()
        self.message = f"Sorted by {self.sort_mode}"

    # ---------------------- High Score ----------------------
    def load_highscores(self):
        self.highscores = []
        if os.path.exists(HS_FILE):
            try:
                with open(HS_FILE, "r", encoding="utf-8") as f:
                    self.highscores = json.load(f)
            except Exception:
                self.highscores = []

    def save_highscore(self):
        entry = {"score": self.player.score, "round": self.game.round_no}
        self.highscores.append(entry)
        self.highscores = sorted(self.highscores, key=lambda e: (-e["score"], -e["round"]))[:10]
        try:
            with open(HS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.highscores, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


    # ---------------------- Layout/Helpers -------------------
    def layout_hand(self) -> List[pygame.Rect]:
        rects = []
        n = len(self.player.hand.cards)
        start_x = (W - (n * CARD_W + (n - 1) * SPACING)) // 2
        for i in range(n):
            x = start_x + i * (CARD_W + SPACING)
            rects.append(pygame.Rect(x, TOP_Y, CARD_W, CARD_H))
        return rects

    def toggle_select(self, i: int):
        if i in self.selected:
            self.selected.remove(i)
        else:
            self.selected.append(i)

    def sort_hand(self):
        if self.sort_mode == "rank":
            self.player.hand.sort_by_rank()
        elif self.sort_mode == "suit":
            self.player.hand.sort_by_suit()
        # "none" does nothing - keeps original order



    # ---------------------- Shop System ---------------------
    @dataclass
    class ShopItem:
        kind: str  # "joker" | "upgrade"
        name: str
        desc: str
        price: int
        factory: Optional[callable] = None  # for joker creation
        apply_upgrade: Optional[callable] = None
        cls: Optional[type] = None  # for joker class
    def open_shop(self):
        if not self.shop_available:
            self.message = "Shop only available after completing a round"
            return
        self.shop_items = self.roll_shop()
        self.build_shop_layout()
        self.game.mode = "SHOP"
        self.message = "Shop: click item to buy, or use Close Shop button"


    def close_shop(self):
        self.game.mode = "PLAY"
        self.shop_available = False
        self.game.round_no += 1
        self.game.rules.score_goal = get_blind_goal(self.game.round_no)
        self.game.new_round()
        self.player.hand.max_size = self.player.effective_hand_size()
        self.deal_up_to_full()  # แจกใหม่ตาถัดไป
        self.message = "Exited shop"
    
    def open_deck(self):
        self.game.mode = "DECK"
        self.message = "Viewing deck. Click Close Deck to exit."
    
    def close_deck(self):
        self.game.mode = "PLAY"
        self.message = "Closed deck view."
    
    def roll_shop(self):
        items = []
        # Jokers pool - unique, from current joker_deck
        joker_pool = self.joker_deck.copy()
        # Upgrades pool
        upgrade_pool = [
            ("Hand +1", "+1 card hand size (permanent this run)", 40, lambda: setattr(self.player.upgrades, "hand_size_bonus", self.player.upgrades.hand_size_bonus+1)),
            ("Redraw +1", "+1 redraw each round", 30, lambda: setattr(self.player.upgrades, "redraw_bonus", self.player.upgrades.redraw_bonus+1)),
            ("Joker Slot +1", "+1 joker slot", 50, lambda: setattr(self.player.upgrades, "joker_slots_bonus", self.player.upgrades.joker_slots_bonus+1)),
        ]
        # Shuffle the joker pool like a deck of cards
        self.rng.shuffle(joker_pool)
        # Draw the top jokers (up to 2)
        chosen_jokers = joker_pool[:min(2, len(joker_pool))]
        for cls, kwargs, price, n, d in chosen_jokers:
            items.append(self.ShopItem("joker", n, d, price, factory=lambda c=cls, kw=kwargs: c(**kw), cls=cls))
        upgrade = self.rng.choice(upgrade_pool)
        items.append(self.ShopItem("upgrade", upgrade[0], upgrade[1], upgrade[2], apply_upgrade=upgrade[3]))
        return items

    def build_shop_layout(self):
        w = 300; h = 120
        gap = 24
        num_items = len(self.shop_items)
        start_x = (W - (num_items*w + (num_items-1)*gap))//2
        y = 140
        self.shop_rects = []
        for i in range(num_items):
            x = start_x + i*(w+gap)
            self.shop_rects.append(pygame.Rect(x, y, w, h))

    def click_shop(self, pos):
        if self.close_button_rect.collidepoint(pos):
            self.close_shop()
            return
        for i, r in enumerate(self.shop_rects):
            if r.collidepoint(pos):
                it = self.shop_items[i]
                if self.player.coins < it.price:
                    self.message = "Not enough coins"
                    return
                if it.kind == "joker":
                    if len(self.player.jokers) >= self.player.effective_joker_slots():
                        self.message = "No joker slot available"
                        return
                    self.player.coins -= it.price
                    self.player.jokers.append(it.factory())
                    # Remove the bought joker from the deck
                    new_joker_deck = []
                    for t in self.joker_deck:
                        if t[0].__name__ != it.cls.__name__:
                            new_joker_deck.append(t)
                    self.joker_deck = new_joker_deck
                    self.message = f"Bought Joker: {it.name}"
                    # Remove the bought joker from the shop display
                    self.shop_items.remove(it)
                    self.build_shop_layout()
                else:
                    self.player.coins -= it.price
                    it.apply_upgrade()
                    # apply immediate effects to runtime values
                    self.player.hand.max_size = self.player.effective_hand_size()
                    self.game.rules.redraw_remaining = self.player.effective_redraws()
                    self.message = f"Bought Upgrade: {it.name}"
                break
    def click_deck(self, pos):
        if self.close_deck_button_rect.collidepoint(pos):
            self.close_deck()

    # ---------------------- Actions -------------------------
    def new_run(self):
        self.deck.build_standard()
        self.player.hand = Hand()
        self.player.jokers.clear()
        self.joker_deck = self.full_joker_pool.copy()  # Reset joker deck
        self.player.upgrades = Upgrades()
        self.player.joker_slots = 5 
        self.player.hand.max_size = self.player.effective_hand_size()
        self.player.score = 0
        self.player.coins = 0
        self.game.round_no = 1
        self.game.rules = RoundRules(score_goal=get_blind_goal(1))
        self.shop_available = False
        self.selected.clear()
        self.message = "New run! Use Deal button to deal."
        self.game.mode = "PLAY"

    def deal_up_to_full(self):
        need = self.player.hand.max_size - len(self.player.hand.cards)
        if need > 0:
            self.player.hand.add(self.deck.draw(need))
            self.sort_hand()
            self.message = "Dealt cards. Click to select, use Redraw and Play buttons."
            # Check if deck is empty and goal not reached
            if not self.deck.cards and self.player.score < self.game.rules.score_goal:
                self.game.mode = "GAMEOVER"
                self.message = "Deck empty and goal not reached. You lose."
                self.save_highscore()
        else:
            self.message = "Hand already full."

    def redraw(self):
        if self.game.mode != "PLAY": return
        if self.game.rules.redraw_remaining <= 0:
            self.message = "No redraws left."
            return
        if not self.selected:
            self.message = "Select cards to discard (click)."
            return
        rects = self.layout_hand()
        removed = self.player.hand.remove_indices(sorted(self.selected))
        self.deck.toss(removed)
        draw_n = len(removed)
        self.player.hand.add(self.deck.draw(draw_n))
        self.sort_hand()
        self.selected.clear()
        self.game.rules.redraw_remaining -= 1
        self.message = f"Redrew {draw_n}."

    def play_hand(self):
        if self.game.mode != "PLAY": return
        if self.game.rules.hands_remaining <= 0:
            self.message = "No hands left this round."
            return
        if len(self.player.hand.cards) < 1:
            self.message = "Need at least 1 card to play. Press D to draw."
            return


        # เล่น 1–5 ใบ
        if not self.selected:
            self.message = "Select cards to play."
            return
        if not (1 <= len(self.selected) <= 5):
            self.message = "Select 1–5 cards to play."
            return
        play_idxs = sorted(self.selected)


        # ประเมินชุดไพ่เฉพาะที่เล่น
        played_cards = [self.player.hand.cards[i] for i in play_idxs]
        kind, base_chips, mult = eval_hand(played_cards)
        card_chips = sum(CARD_CHIPS[c.rank] for c in played_cards)
        total_chips = base_chips + card_chips
        ctx = ScoreContext(total_chips, mult, kind, played_cards[:])
        for j in self.player.jokers:
            j.apply(ctx)

        points = int(ctx.base_chips * ctx.base_mult)
        self.player.score += points

        # ปรับอัตรา coins: อย่างน้อย 1 + 1 ต่อ 10 คะแนน + โบนัสโจ๊กเกอร์
        gained_coins = max(1, points // 10) + ctx.coins
        self.player.coins += gained_coins



        # ทิ้งเฉพาะใบที่เล่น ไปที่ discard
        self.player.hand.remove_indices(play_idxs)
        self.deck.toss(played_cards)
        self.deal_up_to_full()
        self.game.rules.hands_remaining -= 1
        self.selected.clear()
        self.message = f"Played: {kind} → +{points} pts (+{gained_coins} coins)"

        # เช็กเป้าหมาย
        if self.player.score >= self.game.rules.score_goal:
            self.message += "  | Goal reached!"
            # ไพ่ทั้งหมดในHand ไปที่ discard
            self.deck.toss(self.player.hand.clear())
            self.player.score = 0
            self.shop_available = True
            self.open_shop()
        elif self.game.rules.hands_remaining == 0:
            self.message += "  | Out of hands! You failed the goal. Use New Run button to restart."
            self.game.mode = "GAMEOVER"
            self.save_highscore()


    # ---------------------- Render --------------------------
    def draw_card(self, rect: pygame.Rect, card: Card, selected: bool):
        bg = CARD_SEL if selected else CARD_BG
        pygame.draw.rect(self.screen, bg, rect, border_radius=16)
        pygame.draw.rect(self.screen, (0,0,0), rect, width=2, border_radius=16)
        if card.suit in ("♥"):
            col = RED
        elif card.suit in ("♦"):
            col = YELLOW
        elif card.suit in ("♣"):
            col = BLUE
        else:
            col = PURPLE
        rank_surf = self.big.render(card.rank, True, col)
        suit_surf = self.big.render(card.suit, True, col)
        self.screen.blit(rank_surf, (rect.x + 12, rect.y + 12))
        self.screen.blit(suit_surf, (rect.x + 12, rect.y + 56))


    def draw_hud(self):
        
        panel = pygame.Rect(40, 24, W-80, 220)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=18)
        t1 = self.big.render(f"Score: {self.player.score}", True, WHITE)
        t2 = self.big.render(f"Goal: {self.game.rules.score_goal}", True, GREEN if self.player.score>=self.game.rules.score_goal else WHITE)
        t3 = self.font.render(f"Round: {self.game.round_no}", True, WHITE)
        t4 = self.font.render(f"Hands: {self.game.rules.hands_remaining}", True, WHITE)
        t5 = self.font.render(f"Redraws: {self.game.rules.redraw_remaining}", True, WHITE)
        t6 = self.big.render(f"Coins: {self.player.coins}", True, YELLOW)
        t7 = self.font.render(f"Deck: {len(self.deck.cards)}", True, WHITE)
        t8 = self.font.render(f"Jokers Slots: {len(self.player.jokers)}/{self.player.effective_joker_slots()}", True, WHITE)
        self.screen.blit(t1, (panel.x+20, panel.y+16))
        self.screen.blit(t2, (panel.x+20, panel.y+60))
        self.screen.blit(t3, (panel.x+20, panel.y+104))
        self.screen.blit(t4, (panel.x+240, panel.y+104))
        self.screen.blit(t5, (panel.x+420, panel.y+104))
        self.screen.blit(t6, (panel.x+20, panel.y+148))
        self.screen.blit(t7, (panel.x+420, panel.y+148))
        self.screen.blit(t8, (panel.x+240, panel.y+148))
        msg = self.small.render(self.message, True, MUTED)
        self.screen.blit(msg, (panel.x+20, panel.bottom - 28))
        # jokers list
        jx, jy = panel.right - 360, panel.y + 16
        self.screen.blit(self.font.render("Jokers:", True, WHITE), (jx, jy))
        for i, j in enumerate(self.player.jokers[:5]):
            line = f"• {j.name}"
            self.screen.blit(self.small.render(line, True, WHITE), (jx, jy + 28 + i*22))

        # highscores preview
        hsx = panel.right - 220
        self.screen.blit(self.font.render("High Score:", True, WHITE), (hsx, jy))
        for i, e in enumerate(self.highscores[:5]):
            line = f"{i+1}. {e['score']} (R{e['round']})"
            self.screen.blit(self.small.render(line, True, MUTED), (hsx, jy + 28 + i*20))

        # help
        help_line = "Click select cards, use buttons for actions"
        s = self.small.render(help_line, True, MUTED)
        self.screen.blit(s, (40, H - 36))

        # draw buttons
        for btn in self.buttons:
            pygame.draw.rect(self.screen, PANEL, btn["rect"], border_radius=8)
            pygame.draw.rect(self.screen, WHITE, btn["rect"], width=2, border_radius=8)
            text = "Close Shop" if btn["text"] == "Shop" and self.game.mode == "SHOP" else ("Close Deck" if btn["text"] == "Deck" and self.game.mode == "DECK" else (f"Sort ({self.sort_mode})" if btn["text"] == "Sort" else btn["text"]))
            text_surf = self.font.render(text, True, WHITE)
            self.screen.blit(text_surf, (btn["rect"].centerx - text_surf.get_width()//2, btn["rect"].centery - text_surf.get_height()//2))

    def draw_shop(self):
        # backdrop
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))
        title = self.big.render("SHOP", True, WHITE)
        self.screen.blit(title, (W//2 - title.get_width()//2, 80))
        for i, r in enumerate(self.shop_rects):
            pygame.draw.rect(self.screen, PANEL, r, border_radius=14)
            pygame.draw.rect(self.screen, (0,0,0), r, width=2, border_radius=14)
            it = self.shop_items[i]
            name = self.font.render(it.name, True, WHITE)
            desc = self.small.render(it.desc, True, MUTED)
            price = self.font.render(f"${it.price}", True, YELLOW)
            self.screen.blit(name, (r.x+12, r.y+12))
            self.screen.blit(desc, (r.x+12, r.y+48))
            self.screen.blit(price, (r.right-12-price.get_width(), r.bottom-12-price.get_height()))
        # Close Shop button
        pygame.draw.rect(self.screen, PANEL, self.close_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.close_button_rect, width=2, border_radius=8)
        close_text = self.font.render("Close Shop", True, WHITE)
        self.screen.blit(close_text, (self.close_button_rect.centerx - close_text.get_width()//2, self.close_button_rect.centery - close_text.get_height()//2))

    def draw_gameover(self):
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))
        title = self.big.render("GAME OVER", True, RED)
        info = self.font.render("Use New Run button to start a new run", True, WHITE)
        self.screen.blit(title, (W//2 - title.get_width()//2, H//2 - 40))
        self.screen.blit(info, (W//2 - info.get_width()//2, H//2 + 8))
    def draw_deck(self):
        # backdrop
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))
        title = self.big.render("DECK VIEW", True, WHITE)
        self.screen.blit(title, (W//2 - title.get_width()//2, 80))

        # Show deck count
        deck_count = len(self.deck.cards)
        discard_count = len(self.deck.discard)
        deck_text = self.font.render(f"Cards in Deck: {deck_count}", True, WHITE)
        discard_text = self.font.render(f"Cards in Discard: {discard_count}", True, WHITE)
        self.screen.blit(deck_text, (100, 140))
        self.screen.blit(discard_text, (100, 180))

        # Group cards by suit and sort each group by rank descending
        all_cards = list(self.deck.cards)
        suit_groups = DefaultDict(list)
        for card in all_cards:
            suit_groups[card.suit].append(card)
        y = 220
        for suit in SUITS:
            if suit in suit_groups:
                cards = sorted(suit_groups[suit], key=lambda c: c.value(), reverse=True)
                line = " ".join(c.show() for c in cards)
                card_text = self.small.render(f"{suit}: {line}", True, MUTED)
                self.screen.blit(card_text, (100, y))
                y += 20
                if y > H - 100:  # limit to screen
                    break

        # Close Deck button
        pygame.draw.rect(self.screen, PANEL, self.close_deck_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.close_deck_button_rect, width=2, border_radius=8)
        close_text = self.font.render("Close Deck", True, WHITE)
        self.screen.blit(close_text, (self.close_deck_button_rect.centerx - close_text.get_width()//2, self.close_deck_button_rect.centery - close_text.get_height()//2))



    # ---------------------- Main Loop ------------------------
    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit(0)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    # Check buttons first (always available)
                    for btn in self.buttons:
                        if btn["rect"].collidepoint(e.pos):
                            btn["action"]()
                            break
                    else:
                        # If not button, check mode-specific clicks
                        if self.game.mode == "PLAY":
                            rects = self.layout_hand()
                            for i, r in enumerate(rects):
                                if r.collidepoint(e.pos):
                                    self.toggle_select(i)
                                    break
                        elif self.game.mode == "SHOP":
                            self.click_shop(e.pos)
                        elif self.game.mode == "DECK":
                            self.click_deck(e.pos)


            # draw
            self.screen.fill(BG)
            self.draw_hud()

            rects = self.layout_hand()
            for i, c in enumerate(self.player.hand.cards):
                self.draw_card(rects[i], c, i in self.selected)


            if self.game.mode == "SHOP":
                self.draw_shop()
            elif self.game.mode == "GAMEOVER":
                self.draw_gameover()
            elif self.game.mode == "DECK":
                self.draw_deck()

            pygame.display.flip()
if __name__ == "__main__":
    App().run()
