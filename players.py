from top import *


class Player:
    def __init__(self,
                 debug_name,
                 team_id,
                 stats,
                 pieces):
        self.debug_name = debug_name
        self.team_id = team_id
        self.stats = stats
        self._pieces = list(pieces)
        self._abilities = None
        self.pass_binding = None
        self.environment = None
        self.n_lands_played_this_turn = 0
        # COMBAT #
        self.attacker_declaration = list([])
        self.blocker_declaration = list([])
        self.attacker_dao = list([])
        self.blocker_dao = list([])
        self.inverse_blocker_declaration = dict()
        # ZONE DATA #
        self._max_hand_size = 7
        # MANA POOL DATA #
        self.mana_pool = list([])


    def clear_combat_data(self):
        self.attacker_declaration = list([])
        self.blocker_declaration = list([])
        self.attacker_dao = list([])
        self.blocker_dao = list([])
        self.inverse_blocker_declaration = dict()

    def print_stats(self):
        print("{}\t{}".format(self.__repr__(), self.stats.__repr__()))


    @property
    def max_hand_size(self):
        # TODO # integrate this with effects which modify max hand size
        return self._max_hand_size

    @property
    def hand_size(self):
        # TODO #
        #return len([p for p in self.pieces if (p.zone == p.hand])
        return 7

    @property
    def n_to_discard(self):
        return max(0, self.hand_size - self.max_hand_size)

    @property
    def can_act(self):
        # NOTE #
        # approx. == @property def is_dead(self)
        # For now, this verifies that the actor has enough hp to act
        # but is a hook for verification when restrictions are put in place
        return self.stats.hp > 0

    @property
    def pieces(self):
        # TODO #
        if (self.environment is not None):
            return (piece for piece in self.environment.pieces if (piece.owner is self))
        raise ValueError("Player asked for its pieces without being embedded in an environment.")

    @pieces.setter
    def pieces(self, value):
        self._pieces = list(value)

    @property
    def abilities(self):
        result = []
        for piece in self.pieces:
            result.extend(piece.abilities)
        return result

    def solve_legals(self):
        return self.environment.solve_legals(player=self)

    def choose_action(self):
        return random_choice(self.solve_legals())

    def __repr__(self):
        return "{}Player {}{}".format(TEAM_COLORS[self.team_id], self.debug_name, DEF)


class ManualChoiceMixin:
    def choose_action(self):
        options = self.solve_legals()
        while True:
            for i, option in enumerate(options):
                print("{}\t{}".format(i, option))
            result = input("?>>> ")
            try:
                result_int = int(result)
                option = options[result_int]
                if not(option is self.pass_binding):
                    option.ability.itsallbeendone = True
                break
            except:
                continue
        return option


    def choose_option(self, options):
        while True:
            tc_buffer()
            for i, option in enumerate(options):
                print("{}\t{}".format(i, option))
            result = input("?>>> ")
            try:
                result_int = int(result)
                option = options[result_int]
                if not(option is self.pass_binding):
                    option.ability.itsallbeendone = True
                break
            except:
                continue
        return option



class ManualPlayer(ManualChoiceMixin,Player):
    pass


class StatMap:
    def __init__(self, **kwargs):
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])


p0 = ManualPlayer(debug_name="0",
                  team_id=0,
                  stats=StatMap(speed=0, strength=1, hp=2, magic=3),
                  pieces=[])


p1 = ManualPlayer(debug_name="1",
                  team_id=1,
                  stats=StatMap(speed=2, strength=1, hp=2, magic=3),
                  pieces=[])



PLAYERS = [p0, p1]
