from random import choice
from time import sleep

FOUNDATION_OFFSET = 3

class Bot:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.tableau = []
        self.foundation = []
        self.waste = []
        self.last_move = ()
        self.fails = 0

    def update_state(self, rows, cursor):
        self.tableau = rows[1]
        self.foundation = rows[0][-4:]
        self.waste = rows[0][1]
        self.cursor = cursor

    def make_move(self):
        for r in [self.try_add_to_foundation(), self.try_stack_or_add_to_tableau()]:
            if r:
                self.fails = 0
                return r

        self.fails += 1
        if self.fails == 20:
            print "can't solve more"
            if len(sum(map(lambda x: x.cards, self.foundation), [])) == 52:
                print "WIN"
                sleep(10)
                exit()
            else:
                exit()

        return self.generate_moves(Position(0,0), deal=True)

    def last_card_in_tableau(self):
        return [pile.cards[-1:] for pile in self.tableau]

    def try_stack_or_add_to_tableau(self):
        """Tries to stack piles within the tableau, as well as trying to put from waste to tableau"""
        waste_top = self.waste.cards[-1:]
        if waste_top:
            for pile_index, pile in enumerate(self.tableau):
                if pile.valid_addition(waste_top):
                    return self.generate_moves(
                            Position(1, 0),
                            Position(pile_index, 1))

        for i, from_pile in enumerate(self.tableau):
            for j, to_pile in enumerate(self.tableau):
                if i == j or (from_pile.cards and from_pile.cards[0].value == 13):
                    continue
                else:
                    vis_cards = filter(lambda x: not x.hidden, from_pile.cards)
                    if to_pile.valid_addition(vis_cards):
                        if self.last_move == (Position(i, 1), Position(j, 1)):
                            continue
                        return self.generate_moves(
                                Position(i, 1),
                                Position(j, 1),
                                len(vis_cards))


    def try_add_to_foundation(self):
        """Tries to add any card to foundation"""
        waste_top = self.waste.cards[-1:]
        if waste_top:
            for foundation_index, f in enumerate(self.foundation):
                if f.valid_addition(waste_top):
                    return self.generate_moves(
                            Position(1, 0),
                            Position(foundation_index + FOUNDATION_OFFSET, 0))

        for tableau_index, card in enumerate(self.last_card_in_tableau()):
            for foundation_index, f in enumerate(self.foundation):
                if f.valid_addition(card):
                    return self.generate_moves(
                            Position(tableau_index, 1),
                            Position(foundation_index + FOUNDATION_OFFSET, 0))

    def generate_moves(self, start, goal=None, height=0, deal=False):
        """Generate moves to output to the game.
        start is the position to the "from pile"
        goal is the position to the target pile
        height is the height of the "from pile" """


        cards_below_start_pile = len(filter(lambda x: not x.hidden, self.tableau[start.x].cards))
        cursor_to_start =   'd' * max(0, start.y - self.cursor.y) +\
                            'r' * max(0, start.x - self.cursor.x) +\
                            'l' * max(0, self.cursor.x - start.x) +\
                            'u' * max(0, (self.cursor.y - start.y) * max(1, cards_below_start_pile)) # xD. Move upwards inside a pile takes extra moves when having no selection

        if deal:
            return cursor_to_start + 's'

        cards_in_start =    'u' * max(height-1, 0)

        start_to_goal =     'd' * max(0, goal.y - start.y) +\
                            'r' * max(0, goal.x - start.x) +\
                            'l' * max(0, start.x - goal.x) +\
                            'u' * max(0, start.y - goal.y)

        if self.verbose:
            print "Generate moves from cursor %s to start %s to goal %s:\n %ss%ss" % (self.cursor.position, start.position, goal.position, cursor_to_start, start_to_goal)

        self.last_move = (goal, start) # Backwards on purpose
        return cursor_to_start + cards_in_start + 's' + start_to_goal + 's'

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @property
    def position(self):
        return self.x, self.y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
