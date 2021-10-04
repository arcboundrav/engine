from abilities_and_fx import *


class DamageSubEvent:
    def __init__(self, actor, victim, amount):
        self.actor = actor
        self.victim = victim
        self.amount = amount

    def enact(self):
        # NOTE # TODO # NOTE #
        # Add in the custom processed damage subevents such as marking -1/-1 or infect counters.
        # Case: The victim is a Player; reduce HP by amount of damage.
        if isinstance(self.victim, Player):
            self.victim.stats.hp -= self.amount
        # Case: The victim is a Piece; mark damage accordingly.
        else:
            self.victim.marked_damage += self.amount
        self.actor.environment.announce_combat("{} dealt {} damage to {}!".format(self.actor, self.amount, self.victim))

    def __repr__(self):
        return "damage({}, {}, {})".format(self.actor, self.victim, self.amount)


class Piece:
    def __init__(self, owner, debug_name, p, t, ability_list=[], charx_dict={}):
        self.owner = owner
        self.debug_name = debug_name
        self.ability_list = list(ability_list)
        self.current_zone = 0
        self.environment = None

        ##################################
        # NOTE # Kludge for DamageDaemon #
        ##################################
        self.p = p
        self.t = t
        ##################################
        self.has_deathtouch = False
        self.has_lifelink = False
        self.has_trample = False
        self.has_haste = False
        self.has_phasing = False
        ##################################
        self.marked_damage = 0
        self.touched_by_death = False
        ##################################
        self.is_tapped = False
        self.is_flipped = False
        self.is_face_down = False
        self.is_phased_out = False
        ##################################
        self.can_untap = True
        ##################################
        self.is_attacking = False
        self.who_i_am_attacking = list([])
        self.is_blocking = False
        self.who_i_am_blocking = list([])
        self.is_attacked = False
        self.players_attacking_me = list([])
        self.pieces_attacking_me = list([])
        self.is_blocked = False
        self.pieces_blocking_me = list([])
        ##################################
        self.damage_order = list([])
        ##################################
        self.is_creature = True
        self.is_planeswalker = False
        ##################################
        self.controller = None
        self.controller_changed_this_turn = False
        self.controller_when_i_phased_out = None
        ##################################
        self.min_block_n = 0
        self.max_block_n = 1
        ##################################
        self.cannot_attack = False
        self.cannot_block = False
        self.cannot_attack_alone = False
        self.cannot_block_alone = False
        ##################################
        self.must_attack_if_able = False
        self.must_block_if_able = False
        self.must_be_blocked_if_able = False
        self.must_be_attacked_if_able = False
        ##################################
        self.removed_from_combat = False
        ##################################
        #super().__init__(**charx_dict)
        for charx in charx_dict:
            setattr(self, charx, charx_dict[charx])


    @property
    def abilities(self):
        return (ability for ability in self.ability_list if verify_ability(self, ability))

    @abilities.setter
    def abilities(self, value):
        self.ability_list = list(value)

    @property
    def has_summoning_sickness(self):
        if self.is_creature:
            if not(self.has_haste):
                if self.controller_changed_this_turn:
                    return True
        return False

    @property
    def can_attack(self):
        if self.is_creature:
            if not(self.has_summoning_sickness):
                if not(self.is_phased_out):
                    if not(self.is_tapped):
                        return True
        return False

    @property
    def can_block(self):
        if self.is_creature:
            if not(self.is_phased_out):
                if not(self.is_tapped):
                    return True
        return False

    @property
    def lethally_damaged(self):
        if not(self.touched_by_death):
            if (self.t > self.marked_damage):
                return False
        return True

    def calibrate_combat_attributes(self):
        self.is_attacking = False
        self.is_blocking = False
        self.is_attacked = False
        self.is_blocked = False

    def clear_marked_damage(self):
        self.marked_damage = 0
        self.touched_by_death = False

    def mark_damage_on_victims(self):
        '''\
            Generate the damage subevents that should occur simultaneously.
        '''
        # NOTE # Ignores deathtouch for now.
        # NOTE # Ignores effects causing damage to be based on toughness rather than power.
        # NOTE # Ignores effects causing toughness to be based on power.

        # Damage order solution
        # If we're unblocked, then the damage order is simply a list containing who we are
        # attacking. If we're blocked, it's the standard situation.

        # Case: Attacking and not blocked.
        if (self.who_i_am_attacking and not(self.is_blocked)):
            self.damage_order = self.who_i_am_attacking

        # Case: Either blocking and self.damage_order is correct; or,
        #       not involved in combat at all and self.damage_order is empty.

        damage_subevents = []

        total_damage_to_deal = self.p
        damage_dealt_so_far = 0
        n_victims = len(self.damage_order)
        last_victim_i = n_victims - 1

        for victim_i in range(n_victims):
            victim = self.damage_order[victim_i]

            # Case: Damaging a Player.
            if isinstance(victim, Player):
                amount_to_deal = total_damage_to_deal - damage_dealt_so_far
                damage_dealt_so_far += amount_to_deal
                damage_subevents.append(DamageSubEvent(actor=self, victim=victim, amount=amount_to_deal))

            # Case: Damaging a Piece.
            elif isinstance(victim, Piece):

                # Case: This is the last Piece to damage. No need to cap
                #       amount to deal by the toughness of the Piece.
                if (victim_i == last_victim_i):
                    amount_to_deal = total_damage_to_deal - damage_dealt_so_far
                    damage_dealt_so_far += amount_to_deal
                    damage_subevents.append(DamageSubEvent(actor=self, victim=victim, amount=amount_to_deal))

                # Case: This is not the last Piece to damage. Cap the amount
                #       by the toughness of the Piece if necessary.
                # NOTE # This is where deathtouch comes into play.
                else:
                    amount_to_deal = total_damage_to_deal - damage_dealt_so_far
                    amount_to_deal = min(victim.t, amount_to_deal)
                    damage_dealt_so_far += amount_to_deal
                    damage_subevents.append(DamageSubEvent(actor=self, victim=victim, amount=amount_to_deal))

        return damage_subevents

    def __repr__(self):
        return self.debug_name.ljust(24)



VC_CHARX_DICT = dict(impl_name="Vicious Conquistador",
                     mana_cost="{B}",
                     color="black",
                     card_types=set(['creature']),
                     subtypes=set(['vampire', 'soldier']),
                     power=1,
                     toughness=2)


class ViciousConquistador(Piece):
    def __init__(self, owner, ability_list=[]):
        super().__init__(owner, "Vicious Conquistador", 1, 2, ability_list, dict(VC_CHARX_DICT))



vc0 = ViciousConquistador(p0)

PIECES = [vc0]


c0 = Piece(p0, "Legion Lieutenant", 2, 2)
c0.has_phasing = True
c0.is_phased_out = False

c1 = Piece(p0, "Brazen Borrower", 3, 1)
c1.has_phasing = True
c1.is_phased_out = True
c1.is_tapped = True
c1.can_untap = False

c2 = Piece(p0, "Vampire of the Dire Moon", 1, 1)
c2.is_tapped = True
c2.can_untap = True

pp0_pieces = [c0, c1, c2]


c3 = Piece(p1, "Vicious Conquistador", 1, 2)
c4 = Piece(p1, "Skymarcher Aspirant", 2, 1)
pp1_pieces = [c3, c4]

