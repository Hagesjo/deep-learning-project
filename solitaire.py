#!/usr/bin/env python2
import pygame
from os import path
from random import shuffle
from pygame.locals import *
from collections import defaultdict
from bot import Bot
from time import sleep

CARDWIDTH = 73
CARDHEIGHT = 97
OFFSET = 16
MARGIN = 4
WIDTH = (MARGIN + CARDWIDTH) * 7 - MARGIN
HEIGHT = (7 + 14) * OFFSET + 2 * (MARGIN + CARDHEIGHT) - 3
CURSOR_COLOR = pygame.Color(0, 0, 255)
CURSOR_SELECTED_COLOR = pygame.Color(255, 0, 255)

class Card:
    def __init__(self, suit, value, hidden=True):
        self.suit = suit
        self.value = value
        self.hidden = hidden

    def __repr__(self):
        return "Card(Suit: %s, Value: %s, Hidden: %s)" % (self.suit, self.value, self.hidden)

class Deck:
    def __init__(self):
        cards = []
        for suit in range(4):
            for value in range(1, 14):
                cards.append(Card(suit, value))
        shuffle(cards)

        self.bottom_row = []
        self.goals = []
        for i in range(7):
            self.bottom_row.append(TableauPile([]))

        for i in range(7):
            for j in range(i, 7):
                self.bottom_row[j].cards.append(cards.pop(0))

        for i in range(4):
            self.goals.append(FoundationPile([]))

        for i in self.bottom_row:
            i.cards[-1].hidden = False

        self.deck = Pile(cards)
        self.choosepile = Pile([])

        self.showed = []

        self.top_row = [self.deck, self.choosepile, []] + self.goals

        self.rows = [self.top_row, self.bottom_row]

    def deal(self):
        self.showed += self.choosepile.cards
        if not self.deck.cards:
            self.deck.cards = self.showed
            self.showed = []
            self.choosepile.cards = []
        else:
            cards = self.deck.cards[:3]
            del self.deck.cards[:3]
            for card in cards:
                card.hidden = False
            self.choosepile.cards = cards

    def cards_in_stack(self, stack):
        return self.bottom_row[stack].cards

class Cursor:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.nCards = 1

    @property
    def position(self):
        return self.x, self.y

class Selecter:
    def __init__(self):
        self.from_stack = None
        self.nCards = 0
        self.selected = False

class Pile(object):
    def __init__(self, cards):
        self.cards = cards

    def add(self, cards):
        return False

class FoundationPile(Pile):
    def valid_addition(self, cards): #cards is always a list of cards, even if it is only one
        if len(cards) == 1:
            if self.cards:
                return self.suit == cards[0].suit and cards[0].value - self.cards[-1].value == 1
            else:
                return cards[0].value == 1
        else:
            return False

    def add(self, card):
        if self.valid_addition(card):
            if not self.cards:
                self.suit = card[0].suit
            self.cards += card
            return True
        else:
            return False

class TableauPile(Pile):
    def valid_addition(self, cards):
        if cards:
            return ((not self.cards and cards[0].value == 13) or
                    self.cards and
                    (not(self.cards[-1].hidden) and
                    self.cards[-1].suit % 2 != cards[0].suit % 2 and
                    self.cards[-1].value - cards[0].value == 1))

    def add(self, cards):
        if self.valid_addition(cards):
            self.cards += cards
            return True
        else:
            return False

class Solitaire:
    _POINT_DICT = {
            "PileStackpile" : 5,
            "PileGoalpile" : 10,
            "StackpileGoalpile" : 5,
            "GoalpileStackpile" : -15
    }

    POINT_MOVES = defaultdict(int, **_POINT_DICT)

    def __init__(self, screen, cards, backside, bottom):
        self.screen = screen
        self.cards = cards
        self.backside = backside
        self.bottom = bottom
        self.cursor = Cursor(0, 1)
        self.selector = Selecter()
        self.points = 0
        self.reset()

    def cards_in_stack(self):
        return self.deck.cards_in_stack(self.cursor.x)

    def draw(self):
        self.screen.blit(self.backside, (0, 0))
        x = 0
        for c in self.deck.choosepile.cards:
            self.screen.blit(self.cards[c.suit][c.value - 1], ((MARGIN + CARDWIDTH) + x, 0))
            x += OFFSET


        for i, r in enumerate(self.deck.bottom_row):
            y = 0
            for c in r.cards:
                card = self.backside if c.hidden else self.cards[c.suit][c.value - 1]
                self.screen.blit(card, ((MARGIN + CARDWIDTH) * i, (2 * MARGIN + CARDHEIGHT) + y))
                y += OFFSET

        for i, g in enumerate(self.deck.goals):
            if g.cards:
                self.screen.blit(self.cards[g.cards[-1].suit][g.cards[-1].value-1], ((MARGIN+CARDWIDTH) * (i + 3), 0))
            else:
                self.screen.blit(self.bottom, ((MARGIN + CARDWIDTH) * (i + 3), 0))

        self.draw_cursor()

    def move_right(self):
        # if self.cursor.position == (1, 0) or (self.cursor.position == (0, 0) and not self.deck.choosepile.cards):
            # self.cursor.x = 3
        # else:
        self.cursor.x = min(self.cursor.x + 1, 6)
        self.cursor.nCards = 1

    def move_left(self):
        # if self.cursor.position == (3, 0):
            # if self.deck.choosepile.cards:
                # self.cursor.x = 1
            # else:
                # self.cursor.x = 0
        # else:
        self.cursor.x = max(self.cursor.x - 1, 0)
        self.cursor.nCards = 1

    def move_down(self):
        if self.cursor.y == 1:
            self.cursor.nCards = max(self.cursor.nCards - 1, 1)
        self.cursor.y = 1

    def move_up(self):
        if (not self.selector.selected and
            self.cursor.nCards < len(self.cards_in_stack()) and
            self.cursor.y == 1 and
            not self.cards_in_stack()[-(self.cursor.nCards + 1)].hidden):
            self.cursor.nCards += 1
        else:
            if not self.deck.choosepile.cards and 1 <= self.cursor.x <= 2:
                self.cursor.x = 0
            elif self.cursor.x == 2: # The gap between the main deck and the four goal piles
                self.cursor.x = 1
            self.cursor.y = 0
            self.cursor.nCards = 1

    def select(self):
        if self.selector.selected:
            selected_cards = self.selector.from_stack.cards[-self.selector.nCards:]

            to_stack = self.deck.rows[self.cursor.y][self.cursor.x]

            if to_stack.add(selected_cards):
                point_key = type(self.selector.from_stack).__name__ + type(to_stack).__name__
                self.points += Solitaire.POINT_MOVES[point_key]
                del self.selector.from_stack.cards[-self.selector.nCards:]
                if self.selector.from_stack.cards and self.selector.from_stack.cards[-1].hidden:
                    self.selector.from_stack.cards[-1].hidden = False
                    self.points += 5
        else:
            if self.cursor.position == (0, 0):
                self.deck.deal()
                return
            current_stack = self.deck.rows[self.cursor.y][self.cursor.x]

            if not current_stack.cards:
                return

            self.selector.from_stack = current_stack
            self.selector.nCards = self.cursor.nCards

        self.selector.selected = not self.selector.selected

    def reset(self):
        self.deck = Deck()

    def draw_cursor(self):
        y = self.cursor.y * (2 * MARGIN + CARDHEIGHT)
        if self.cursor.y == 1:
            y += OFFSET * max(len(self.cards_in_stack()) - self.cursor.nCards, 0)

        x = self.cursor.x * (MARGIN + CARDWIDTH)
        if self.cursor.y == 0 and self.cursor.x == 1:
            x += max(0, OFFSET * (len(self.deck.rows[self.cursor.y][self.cursor.x].cards) - 1))

        pygame.draw.rect(self.screen,
                         CURSOR_SELECTED_COLOR if self.selector.selected else CURSOR_COLOR,
                         pygame.Rect(x,
                                     y,
                                     CARDWIDTH,
                                     CARDHEIGHT + OFFSET * (self.cursor.nCards - 1)),
                         2)

def init_game():
    cards = [[pygame.image.load(path.join('cards', '{0:02d}'.format(value) + suit + ".gif"))
            for value in range(1, 14)]
            for suit in ['d', 'c', 'h', 's']]
    backside = pygame.image.load(path.join('cards', 'back192.gif'))
    bottom = pygame.image.load(path.join('cards', 'bottom01-n.gif'))
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 130, 0))

    solitaire = Solitaire(background, cards, backside, bottom)
    solitaire.draw()
    bot = Bot()

    screen.blit(background, (0, 0))
    pygame.display.update()
    while 1:
        # event = pygame.event.wait()
        # if event.type == pygame.KEYDOWN:
            # if event.key == pygame.K_LEFT:
                # solitaire.move_left()
            # elif event.key == pygame.K_RIGHT:
                # solitaire.move_right()
            # elif event.key == pygame.K_UP:
                # solitaire.move_up()
            # elif event.key == pygame.K_DOWN:
                # solitaire.move_down()
            # elif event.key == pygame.K_SPACE:
                # solitaire.select()
        # background.fill((0, 130, 0))
        # solitaire.draw()
        # screen.blit(background, (0, 0))
        # pygame.display.update()


        event = pygame.event.get()
        bot.update_state(solitaire.deck.rows, solitaire.cursor)
        moves = bot.make_move()
        for move in moves:
            background.fill((0, 130, 0))
            if move == 'r':
                solitaire.move_right()
            elif move == 'l':
                solitaire.move_left()
            elif move == 'u':
                solitaire.move_up()
            elif move == 'd':
                solitaire.move_down()
            elif move == 's':
                solitaire.select()
            solitaire.draw()

            screen.blit(background, (0, 0))
            pygame.display.update()
            sleep(0.1)

def main():
    init_game()

if __name__ == '__main__':
    main()
