from target import *
from combat import *

# NOTE #
# CombatDamageDealt and RemoveMarkedDamageAndUEoTFXExpire TBA are
# given intended_actor of active player instead of having both of these
# things handled for objects controlled by their respective players to
# promote simultaneity.




class TBA(Ability):
    '''\
        Subclass of Ability for Turn-Based Actions.
    '''
    def __init__(self, intended_actor, tba_name, **kwargs):
        self.intended_actor = intended_actor
        self.tba_name = tba_name.upper()
        super().__init__(**kwargs)

    def __call__(self):
        print("".join([DEF, '| ', HIG, 'TBA    ', DEF, '| ', self.tba_name]))


class TBA_PhasingEntailment(Entailment):
    def apply(self, actor, victim):
        # Case: time to phase out
        if not(victim.is_phased_out):
            actor.environment.announce_event("{} phased out.".format(victim))
            victim.is_phased_out = True
        # Case: time to phase in
        else:
            actor.environment.announce_event("{} phased in.".format(victim))
            victim.is_phased_out = False


class TBA_UntapEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_event("{} untapped {}.".format(actor, victim))
        actor.environment.announce_event("{} became untapped by {}.".format(victim, actor))
        victim.is_tapped = False


class TBA_Phasing(TBA):
    '''\
        502.1 All phased-in permanents with phasing that the active player controls phase out.
              All phased-out permanents (that the active player controlled when they phased out)
              phase in. These events all happen simultaneously.
        # NOTE # Correct target data is, subset of all_pieces where piece.controller_when_i_phased
        #        out is equal to the actor of this action
        # NOTE # Also, when something phases out, it should have its controller_when_i_phased_out
        #        attribute value updated.
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_Phasing",
                         ability_name="TBA_PhasingAbility",
                         effect=TBA_PhasingEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        return [list(filter(lambda p: (p.has_phasing), actor.pieces))]


class TBA_Untap(TBA):
    '''\
        502.2 The active player determines which permanents they control will untap.
              Then they untap them all simultaneously. Normally, all of a player's permanents untap,
              but effects can keep one or more of a player's permanents from untapping.
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_Untap",
                         ability_name="TBA_UntapAbility",
                         effect=TBA_UntapEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        return [list(filter(lambda p: ((p.can_untap) and (p.is_tapped)), actor.pieces))]


class TBA_Draw(TBA):
    '''\
        504.1 The active player draws a card.
        # TODO #
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor, tba_name="TBA_Draw")


class TBA_SagaLoreCounters(TBA):
    '''\      
        505.4 If the active player controls one or more Saga enchantments and it's the active
              player's precombat main phase, the active player puts a lore counter on each Saga
              they control.
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor, tba_name="TBA_SagaLoreCounters")


class TBA_ChooseDefendingOpponentEntailment(Entailment):
    def apply(self, actor, victim):
        actor.is_attacking = victim
        actor.environment.announce_combat("{} is attacking {}.".format(actor, victim))
        victim.is_defending_player = True
        actor.environment.announce_combat("{} is now the defending player.".format(victim))
        victim.is_being_attacked_by = actor
        actor.environment.announce_combat("{} is being attacked by {}.".format(victim, actor))


class TBA_DeclareAttackersEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_combat("{} has been declared as an attacker.".format(victim[0]))
        actor.environment.announce_combat("{} is attacking {}.".format(victim[0], victim[1]))
        victim[0].who_i_am_attacking = [victim[1]]


class TBA_DeclareBlockersEntailment(Entailment):
   def apply(self, actor, victim):
        # NOTE # actor is a blocking Piece
        # NOTE # victim is one of the >= 1 attacking Pieces actor is blocking.
        actor.environment.announce_combat("{} has been declared as a blocker.".format(actor))
        actor.environment.announce_combat("{} is blocking {}.".format(actor, victim))
        actor.who_i_am_blocking.append(victim)
        actor.environment.announce_combat("{} is blocked by {}.".format(victim, actor))
        victim.pieces_blocking_me.append(actor)
        victim.is_blocked = True


class TBA_AttackerDamageOrderEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_combat("{} will assign combat damage in the following order: {}.".format(actor, victim))
        actor.damage_order = victim

class TBA_BlockerDamageOrderEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_combat("{} will assign combat damage in the following order: {}.".format(actor, victim))
        actor.damage_order = victim

class TBA_MaintainLegalHandSizeEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_event("{} discarded {}.".format(actor, victim))




class TBA_ChooseDefendingOpponent(TBA):
    '''\
        506.2  During the combat phase, the active player is the attacking player; creatures that
               player controls may attack. During the combat phase of a two-player game, the
               nonactive player is the defending player; that player and planeswalkers they
               control may be attacked.
        506.2a During the combat phase of a multiplayer game, there may be one or more
               defending players... Unless all the attacking player's opponents automatically
               become defending players during the combat phase, the attacking player chooses
               one of their opponents as a turn-based action during the beginning of combat step.
               That player becomes the defending player.
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_ChooseDefendingOpponent",
                         ability_name="TBA_ChooseDefendingOpponentAbility",
                         effect=TBA_ChooseDefendingOpponentEntailment(),
                         target_data=TargetData(size=1, filtration=other_players))


class TBA_DeclareAttackers(TBA):
    '''\
        508.   Declare Attackers Step
        508.1a AP declares attackers as follows:
               [1] Choose which creatures that they control, if any, will attack.
                   The chosen creatures must be untapped, and each one must either
                   have haste or have been controlled by the AP continuously since the turn began.
        508.1b [2] If the defending player controls any planeswalkers ... AP announces which player
                   or planeswalker each of the chosen creatures is attacking.
    '''
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_DeclareAttackers",
                         ability_name="TBA_DeclareAttackers",
                         effect=TBA_DeclareAttackersEntailment())

    def apply(self, actor, victims):
        '''\
            Over-ride.
        '''
        attackers = return_attackers(victims)
        actor.environment.announce_combat("{} declared {} as attackers.".format(actor, attackers))
        actor.attacker_declaration = victims
        actor.attackers = attackers
        for victim in victims:
            self.effect.apply(actor, victim)
        self.itsallbeendone = True

    def solve_attackers_given_actor(self, actor):
        return list(filter(lambda p: (p.can_attack), actor.pieces))

    def solve_attackables_given_actor(self, actor):
        return [actor.is_attacking] + list(filter(lambda p: (p.is_planeswalker), actor.is_attacking.pieces))

    def solve_target_subscopes_given_actor(self, actor):
        '''\
            Must return: List[Tuple[Player]]]
        '''
        return declare_attackers(attackers=self.solve_attackers_given_actor(actor),
                                 attackables=self.solve_attackables_given_actor(actor))




class TBA_DeclareBlockers(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_DeclareBlockers",
                         ability_name="TBA_DeclareBlockers",
                         effect=TBA_DeclareBlockersEntailment())

    def solve_blockers_given_actor(self, actor):
        return list(filter(lambda p: (p.can_block), actor.pieces))

    def solve_target_subscopes_given_actor(self, actor):
        possible_blockers = self.solve_blockers_given_actor(actor)
        attackers = actor.is_being_attacked_by.attackers
        return solve_blocker_declarations(A=attackers, B=possible_blockers)

    def apply(self, actor, victims):
        attacking_actor = actor.is_being_attacked_by
        blocking_actor = actor
        blockers = list(victims.keys())
        blocking_actor.environment.announce_combat("{} declared {} as blockers.".format(blocking_actor, blockers))
        blocking_actor.blocker_declaration = victims
        blocking_actor.inverse_blocker_declaration = invert_blocker_declaration(blocking_actor.blocker_declaration)
        blocking_actor.blockers = blockers
        for victim in victims:
            blocked_by_victim = victims[victim]
            for blocked in blocked_by_victim:
                self.effect.apply(victim, blocked)


class TBA_AttackerDamageOrder(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_AttackerDamageOrder",
                         ability_name="TBA_AttackerDamageOrder",
                         effect=TBA_AttackerDamageOrderEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        blocking_actor = actor.is_attacking
        inverted_blocking_declaration = blocking_actor.inverse_blocker_declaration
        return attacker_damage_assignment_orders(inverted_blocking_declaration)

    def apply(self, actor, victims):
        actor.attacker_dao = victims
        for pairing in victims:
            attacker = pairing[0]
            blockers = pairing[1]
            # TODO # Validate that the blockers are still there?
            self.effect.apply(attacker, blockers)



class TBA_BlockerDamageOrder(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_BlockerDamageOrder",
                         ability_name="TBA_BlockerDamageOrder",
                         effect=TBA_BlockerDamageOrderEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        blocking_actor = actor
        return blocker_damage_assignment_orders(blocking_actor.blocker_declaration)

    def apply(self, actor, victims):
        blocking_actor = actor
        for pairing in victims:
            blocker = pairing[0]
            blocked_attackers = pairing[1]
            self.effect.apply(blocker, blocked_attackers)


class TBA_AttackerAssignCombatDamage(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_AttackerAssignCombatDamage",
                         ability_name="TBA_AttackerAssignCombatDamage")

class TBA_BlockerAssignCombatDamage(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_BlockerAssignCombatDamage",
                         ability_name="TBA_BlockerAssignCombatDamage")


class TBA_CombatDamageDealtEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_combat("{} had victim mark its damage {}.".format(actor, victim))
        actor.environment.preliminary_damage_events.extend(victim.mark_damage_on_victims())


class TBA_CombatDamageDealt(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_CombatDamageDealt",
                         ability_name="TBA_CombatDamageDealt",
                         effect=TBA_CombatDamageDealtEntailment())

    def apply(self, actor, victims):
        actor.environment.announce_combat("{} is generating damage subevents.".format(actor))
        for victim in victims:
            self.effect.apply(actor, victim)
        actor.environment.process_damage_events()
        actor.environment.simultaneous_application_of_damage_events()

    def solve_target_subscopes_given_actor(self, actor):
        return [tuple(actor.environment.pieces)]


class TBA_MaintainLegalHandSize(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_MaintainLegalHandSize",
                         ability_name="TBA_MaintainLegalHandSize",
                         effect=TBA_MaintainLegalHandSizeEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        n_to_discard = actor.n_to_discard
        return list(subpowerset(actor.pieces, n=n_to_discard, N=n_to_discard))


class TBA_RemoveDamageMarkersAndUEoTFXExpireEntailment(Entailment):
    def apply(self, actor, victim):
        actor.environment.announce_event("Removing all damage marked on {}.".format(victim))
        victim.marked_damage = 0
        victim.touched_by_death = False


class TBA_RemoveDamageMarkersAndUEoTFXExpire(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_RemoveDamageMarkersAndUEoTFXExpire",
                         ability_name="TBA_RemoveDamageMarkersAndUEoTFXExpire",
                         effect=TBA_RemoveDamageMarkersAndUEoTFXExpireEntailment())

    # NOTE # Make the AP responsible for this to maintain simultaneity.
    def solve_target_subscopes_given_actor(self, actor):
        return [tuple(actor.environment.pieces)]


class TBA_EmptyManaPoolEntailment(Entailment):
    def apply(self, actor, victim):
        actor.mana_pool.clear()
        actor.environment.announce_event("{} empties their mana pool.".format(actor))


class TBA_EmptyManaPool(TBA):
    def __init__(self, intended_actor):
        super().__init__(intended_actor=intended_actor,
                         tba_name="TBA_EmptyManaPool",
                         ability_name="TBA_EmptyManaPool",
                         effect=TBA_EmptyManaPoolEntailment())

    def solve_target_subscopes_given_actor(self, actor):
        return [(actor,)]


class Epoch:
    def __init__(self,
                 game,
                 previous_epoch=None,
                 head_tba=[],
                 tail_tba=[
                     TBA_EmptyManaPool("NAP"),
                     TBA_EmptyManaPool("AP")
                 ]):
        self.head_tba = list(head_tba)
        self.tail_tba = list(tail_tba)
        # NOTE # Begin attributes drawn from class Epoch
        self.game = game
        self.previous_epoch = previous_epoch
        self.msg = "Default"
        self._next_epoch = None
        self.next_epoch_type = None
        self.last_nonnull_actor = None

    @property
    def stack(self):
        return self.game.stack

    @property
    def limbo(self):
        return self.game.limbo

    @property
    def next_epoch(self):
        # Case: Never asked for the next epoch before.
        if (self._next_epoch is None):
            # Case: Expecting a non-null Epoch to follow.
            if (self.next_epoch_type is not None):
                self._next_epoch = self.next_epoch_type(game=self.game,
                                                        previous_epoch=self)
        return self._next_epoch

    @property
    def players(self):
        return self.game.players

    @property
    def active_player(self):
        return self.game.active_player

    @property
    def non_active_player(self):
        return self.game.non_active_player

    def other_player(self, player):
        return list(filter(lambda p: not(p is player), self.players))[0]

    def sba(self):
        self.game.sba()

    def grant_priority(self, player, n_passes):
        '''\
            Give priority to a player.            
        '''
        self.game.announce_debug("Running SBA loop prior to granting priority...")
        self.sba()
        self.game.announce_daemon("Granting priority to {}...".format(player))
        next_action = player.choose_action()

        # Case: Player passed when prompted.
        if (next_action is None):
            self.game.announce_debug("{} choose to pass...".format(player))

            # Case: This is the 2nd pass in succession.
            if n_passes:
                self.game.announce_debug("This is the 2nd pass in succession!!!")
                # Case: The Stack is not empty, thus:
                #           Resolve the topmost object on it; then,
                #           117.3b: The active player receives priority after a spell or non-mana
                #           ability resolves.
                if self.stack:
                    topmost_object = self.stack.pop()
                    topmost_object.apply()
                    self.grant_priority(self.active_player, 0)

                # Case: The Stack is empty, so, end the current epoch. (happens automatically)
                else:
                    self.game.announce_debug("Both players passed in succession and the Stack is empty...")

            # Case: This is the 1st pass in succession.
            #       Give the other player a chance to act or pass.
            else:
                other_player = self.other_player(player)
                self.game.announce_debug("We think the other player is: {}".format(other_player))
                self.grant_priority(other_player, 1)

        # Case: Player did not pass when prompted; however, they chose a special action.
        #       Therefore, automatically resolve it, and grant them priority again with 0 passes.
        elif isinstance(next_action.ability, Special):
            self.game.announce_debug("{} choose a Special non-pass action: {}".format(player, next_action))
            next_action.apply()
            self.grant_priority(player, 0)

        # Case: Player did not pass when prompted; and, they chose an action which uses the Stack.
        #       Add their input to the Stack and let them hold priority.
        else:
            self.game.announce_debug("{} choose a non-pass action: {}".format(player, next_action))
            self.stack.append(next_action)
            self.grant_priority(player, 0)

    def resolve_topmost_object_on_stack(self):
        if self.stack:
            topmost_object = self.stack.pop()
            topmost_object.apply()
            self.grant_priority(self.active_player, 0)

    def announce_start_of_epoch(self):
        self.game.announce_event("Start of {}.".format(self.msg))

    def announce_end_of_epoch(self):
        self.game.announce_event("End of {}.".format(self.msg))
        tc_buffer()

    def do_tba(self, src_tba):
        tbas_to_do = list(src_tba)
        while tbas_to_do:
            tba_to_do = tbas_to_do.pop()
            tc_buffer()
            tba_to_do()
            # Determine the correct actor for this TBA #
            if (tba_to_do.intended_actor == "AP"):
                which_player = self.active_player
            elif (tba_to_do.intended_actor == "NAP"):
                which_player = self.non_active_player
            tba_to_do_options = self.game.solve_tba_bindings(tba=tba_to_do,
                                                             player=which_player)
            tba_to_do_option = which_player.choose_option(options=tba_to_do_options)
            # Case # The option wasn't a pass_binding, which means it can be applied.
            if (tba_to_do_option is not None):
                tba_to_do_option.apply()

    def do_head_tba(self):
        self.game.announce_daemon("Enacting turn-based action(s) scheduled for the start of this Epoch...")
        self.do_tba(self.head_tba)

    def do_tail_tba(self):
        self.game.announce_daemon("Enacting turn-based action(s) scheduled for the end of this Epoch...")
        self.do_tba(self.tail_tba)

    def determine_skip(self):
        pass

    def execute(self):
        self.announce_start_of_epoch()
        self.do_head_tba()
        self.last_nonnull_actor = self.active_player
        self.grant_priority(self.active_player, 0)
        self.do_tail_tba()
        self.announce_end_of_epoch()
        self.determine_skip()

    def loop(self):
        self.execute()


class FirstStep(Epoch):
    '''\
        For the first step in each non-main phase.
    '''
    def __init__(self, phase_type, game, previous_epoch=None, head_tba=[]):
        self.phase_type = phase_type
        self.phase_msg = "Default"
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=head_tba)

    def announce_start_of_epoch(self):
        '''\
            Preface announcement of the start of this epoch with the announcement of
            the start of the phase of which this epoch is the first step.
        '''
        self.game.announce_event("Start of {} Phase.".format(self.phase_msg))
        super().announce_start_of_epoch()


class LastStep(Epoch):
    '''\
        For the final step in each non-main phase.
    '''
    def __init__(self, phase_type, game, previous_epoch=None, head_tba=[]):
        self.phase_type = phase_type
        self.phase_msg = "Default"
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=head_tba)

    def announce_end_of_epoch(self):
        '''\
            Follow the announcement of the end of this epoch with the announcement of
            the end of the phase of which this epoch is the last step.
        '''
        super().announce_end_of_epoch()
        self.game.announce_event("End of {} Phase.".format(self.phase_msg))


###############
# Phase Types #
###############
class BeginningPhase:
    pass

class CombatPhase:
    pass

class EndingPhase:
    pass


#########
# Steps #
#########
class CleanupStep(LastStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=EndingPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_RemoveDamageMarkersAndUEoTFXExpire("AP"),
                                   TBA_MaintainLegalHandSize("NAP"),
                                   TBA_MaintainLegalHandSize("AP")])
        self.phase_msg = "Ending"
        self.msg = "Cleanup Step"
        self.next_epoch_type = None


class EndStep(FirstStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=EndingPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[])
        self.phase_msg = "Ending"
        self.msg = "End Step"
        self.next_epoch_type = CleanupStep


class PostcombatMain(Epoch):
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[])
        self.msg = "Postcombat Main Phase"
        self.next_epoch_type = EndStep



class EndOfCombatStep(LastStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=CombatPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[])
        self.phase_msg = "Combat"
        self.msg = "End Of Combat Step"
        self.next_epoch_type = PostcombatMain


class CombatDamageStep(Epoch):
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_CombatDamageDealt("AP"),
                                   TBA_BlockerAssignCombatDamage("NAP"),
                                   TBA_AttackerAssignCombatDamage("AP")])
        self.msg = "Combat Damage Step"
        self.next_epoch_type = EndOfCombatStep

    def determine_skip(self):
        # TODO # Logic that governs additional combat damage steps due to first/double strike
        pass


class DeclareBlockersStep(Epoch):
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_BlockerDamageOrder("NAP"),
                                   TBA_AttackerDamageOrder("AP"),
                                   TBA_DeclareBlockers("NAP")])
        self.msg = "Declare Blockers Step"
        self.next_epoch_type = CombatDamageStep


class DeclareAttackersStep(Epoch):
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_DeclareAttackers("AP")])
        self.msg = "Declare Attackers Step"
        self.next_epoch_type = DeclareBlockersStep

    def determine_skip(self):
        # TODO # Logic that goes to EndOfCombatStep if no attackers exist.
        pass


class BeginningOfCombatStep(FirstStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=CombatPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_ChooseDefendingOpponent("AP")])
        self.phase_msg = "Combat"
        self.msg = "Beginning Of Combat Step"
        self.next_epoch_type = DeclareAttackersStep


class PrecombatMain(Epoch):
    '''\
        May need to introduce logic determining whether or not a main phase
        is a precombat or postcombat main phase by tracking how many have
        thus far occurred in the current Turn.
    '''
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_SagaLoreCounters("AP")])
        self.msg = "Precombat Main Phase"
        self.next_epoch_type = BeginningOfCombatStep


class DrawStep(LastStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=BeginningPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_Draw("AP")])
        self.phase_msg = "Beginning"
        self.msg = "Draw Step"
        self.next_epoch_type = PrecombatMain


class UpkeepStep(Epoch):
    def __init__(self, game, previous_epoch=None):
        super().__init__(game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[])
        self.msg = "Upkeep Step"
        self.next_epoch_type = DrawStep


class UntapStep(FirstStep):
    def __init__(self, game, previous_epoch=None):
        super().__init__(phase_type=BeginningPhase,
                         game=game,
                         previous_epoch=previous_epoch,
                         head_tba=[TBA_Untap("AP"),
                                   TBA_Phasing("AP")])
        self.phase_msg = "Beginning"
        self.msg = "Untap Step"
        self.next_epoch_type = UpkeepStep



class AbilityAttack(Ability):
    '''\
        Equivalent to an Instant speed action using the Stack.
    '''
    def __init__(self):
        super().__init__("Attack",
                         Effect(actor_stat_key="strength",
                                victim_stat_key="hp",
                                operation=SUB),
                         TargetData(size=1, filtration=enemies))
        self.max_stack_size = 1000
        self.must_be_actors_turn = False


ABILITY_ATTACK = AbilityAttack()

ABILITY_ATTACK2 = AbilityAttack()

class AbilityHeal(Ability):
    '''\
        Equivalent to a Sorcery speed action using the Stack.
    '''
    def __init__(self):
        super().__init__("Heal",
                         Effect(actor_stat_key="magic", victim_stat_key="hp", operation=ADD),
                         TargetData(size=1, filtration=other_players))

ABILITY_HEAL = AbilityHeal()


class AbilityHealAll(Ability):
    def __init__(self):
        super().__init__("Heal2",
                         Effect(actor_stat_key="magic", victim_stat_key="hp", operation=ADD),
                         TargetData(size=1, filtration=all_players))

ABILITY_HEAL_ALL = AbilityHealAll()


class SpecialPotion(Special):
    '''\
        Equivalent to a special action like playing a land which
        doesn't use the Stack.
    '''
    def __init__(self):
        super().__init__("Drink Potion",
                         Effect(actor_stat_key="magic", victim_stat_key="hp", operation=ADD),
                         TargetData(size=1, filtration=same_player))

SPECIAL_ABILITY_POTION = SpecialPotion()


p0_PIECE_ATTACK = ViciousConquistador(p0, [ABILITY_ATTACK])
p0_PIECE_HEAL = ViciousConquistador(p0, [ABILITY_HEAL_ALL])
p0_PIECE_SPECIAL = ViciousConquistador(p0, [SPECIAL_ABILITY_POTION])

p1_PIECE_ATTACK = ViciousConquistador(p1, [ABILITY_ATTACK2])

p0_pieces = [p0_PIECE_ATTACK, p0_PIECE_HEAL, p0_PIECE_SPECIAL]
p1_pieces = [p1_PIECE_ATTACK]
PIECES = p0_pieces + p1_pieces


class Turn:
    def __init__(self, game, intended_active_idx):
        self.game = game
        self.intended_active_idx = intended_active_idx
        self.first_epoch = UntapStep(game)
        self.current_epoch = self.first_epoch

    @property
    def active_player(self):
        return self.game.active_player

    def inject_intended_active_idx(self):
        # Over-ride the active player information in the superordinate Game
        # w.r.t. the intended active player encoded in the Turn instance.
        # Supports Effects which add extra Turn(s) with an active player which may not be
        # the active player of the Turn when the Effect is applied.
        self.game.active_idx = self.intended_active_idx

    def handle_end_of_turn(self):
        self.game.announce_event("End of Turn.")
        for player in self.game.players:
            player.n_lands_played_this_turn = 0

    def handle_start_of_turn(self):
        self.game.announce_event("Start of Turn.")
        self.inject_intended_active_idx()
        self.current_epoch = self.first_epoch

    def loop(self):
        self.handle_start_of_turn()
        while not(self.game.gameover):
            self.current_epoch.loop()
            self.current_epoch = self.current_epoch.next_epoch
            if (self.current_epoch is None):
                self.handle_end_of_turn()
                break



class Game:
    def __init__(self, players, pieces):
        self.players = list(players)
        self.pieces = list(pieces)
        self.zones = self.generate_zones()
        self.registration()
        self.gameover = False
        self.current_turn = None
        self.active_idx = 1
        self.n_extra_turns = 0
        self.stack = []
        self.limbo = []
        self.preliminary_damage_events = []
        self.preliminary_sba_events = []

    def simultaneous_application_of_damage_events(self):
        # TODO #
        for damage_subevent in self.preliminary_damage_events:
            damage_subevent.enact()


    def process_damage_events(self):
        # TODO #
        pass

    def generate_zones(self):
        # TODO #
        return []

    def registration(self):
        for player in self.players:
            player.environment = self
        for piece in self.pieces:
            piece.environment = self
        for zone in self.zones:
            zone.environment = self

    @property
    def no_attackers(self):
        # TODO # Actually implement something like this.
        return True

    @property
    def active_player(self):
        return self.players[self.active_idx]

    @property
    def non_active_idx(self):
        return xor(1, self.active_idx)

    @property
    def non_active_player(self):
        return self.players[self.non_active_idx]

    @property
    def current_epoch(self):
        return self.current_turn.current_epoch

    def swap_active_player(self):
        self.active_idx = self.non_active_idx

    def start_game(self):
        self.gameover = False
        self.n_extra_turns = 0
        self.active_idx = 1
        self.stack = []
        self.limbo = []

    def _announce(self, prefix_color, prefix, announcement_color, announcement):
        true_prefix = "{}{}{}".format(prefix_color, prefix, DEF)
        true_prefix = true_prefix.center(10)
        prefix = "| " + true_prefix + " |"
        suffix = " {}{}{}".format(announcement_color, announcement, DEF)
        print("".join([prefix, suffix]))

    def announce_event(self, announcement):
        self._announce(prefix_color=HIW, prefix="EVENT ", announcement_color=DEF, announcement=announcement)

    def announce_daemon(self, announcement):
        self._announce(prefix_color=CYN, prefix="ENGINE", announcement_color=DEF, announcement=announcement)

    def announce_debug(self, a):
        self._announce(prefix_color=MAG, prefix="DEBUG ", announcement_color=DEF, announcement=a)

    def announce_combat(self, a):
        self._announce(prefix_color=RED, prefix="COMBAT", announcement_color=DEF, announcement=a)

    def upload_triggered_abilities(self):
        '''\
            Move all of the contents of limbo to the_stack.
        '''
        # TODO #
        # Expand to various orders of adding, in AP/NAP order, when applicable.
        self.stack.extend(self.limbo)
        self.limbo.clear()

    def sba_check_hp(self):
        for player in self.players:
            if (player.stats.hp < 1):
                return True
        return False

    def sba_check_hp_event(self):
        self.announce_event("SBA_CHECK_HP_EVENT (Game ended because someone has < 1 HP).")
        self.end_game()

    def sba(self):
        # Case: Game hasn't ended yet.
        if not(self.gameover):
            self.announce_daemon("Checking state based actions...")

            # Case: SBA is required to take place.
            if self.sba_check_hp():
                self.sba_check_hp_event()
                self.sba()

            # Case: No SBA required to take place, time to check triggered abilities...
            elif self.limbo:
                self.upload_triggered_abilities()
                self.sba()

        # Case: Game is over.
        else:
            print("DEBUG: sba() called and found the game is already over.")

    def new_turn_same_active_player(self):
        return Turn(game=self, intended_active_idx=self.active_idx)

    def new_turn_swap_active_player(self):
        return Turn(game=self, intended_active_idx=self.non_active_idx)

    def end_game(self):
        self.gameover = True
        self.announce_event("End of Game.")

    def solve_affordance_bindings(self, player):
        # Return the legal actions that this Player can perform at a given
        # point in a combat round.
        # A Binding is a 3-tuple of the form:
        #   (actor, ability, choice_of_target_subscope)
        bindings = [player.pass_binding]
        for ability in player.abilities:
            target_subscopes = ability.solve_target_subscopes_given_actor(player)
            for target_subscope in target_subscopes:
                bindings.append(Binding(actor=player, ability=ability, target_subscope=target_subscope))
        return bindings

    def solve_tba_bindings(self, tba, player):
        bindings = []
        target_subscopes = tba.solve_target_subscopes_given_actor(player)
        for target_subscope in target_subscopes:
            bindings.append(Binding(actor=player, ability=tba, target_subscope=target_subscope))
        if bindings:
            return bindings
        return [player.pass_binding]

    def solve_legals(self, player):
        return self.solve_affordance_bindings(player)

    def determine_current_turn(self):
        '''\
            Automatically generates a new Turn when extra_turns is empty
            so there needs to be an Epoch with a loop() method that contains
            a call to a given Game instance's end_game() method or else
            the loop will never terminate.
        '''
        if self.n_extra_turns:
            self.n_extra_turns -= 1
            return self.new_turn_same_active_player()
        return self.new_turn_swap_active_player()

    def loop(self):
        self.start_game()
        n_turns = 0
        max_n_turns = 1
        while not(self.gameover):
            if (n_turns <= max_n_turns):
                self.current_turn = self.determine_current_turn()
                self.current_turn.loop()
                n_turns += 1
            else:
                break
        self.announce_debug("Maximum N Turns Reached.")
        self.end_game()


G = Game(players=PLAYERS, pieces=PIECES+pp0_pieces+pp1_pieces)
G.loop()
