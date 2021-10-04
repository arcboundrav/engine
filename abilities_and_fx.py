from players import *


class Binding:
    '''\
        Represent a fixing of each of the parameters of an effect to apply.
    '''
    def __init__(self, actor, ability, target_subscope):
        self.actor = actor
        self.ability = ability
        self.target_subscope = target_subscope

    def apply(self):
        self.ability.apply(actor=self.actor, victims=self.target_subscope)

    def __repr__(self):
        return "| {} | {} | {} |".format(self.actor, self.ability, self.target_subscope)


class Effect:
    '''\
        Simplified version of a one shot effect.
    '''
    def __init__(self,
                 actor_stat_key,
                 victim_stat_key,
                 operation):
        self.actor_stat_key = actor_stat_key
        self.victim_stat_key = victim_stat_key
        self.operation = operation

    def apply(self, actor, victim):
        actor_stats = actor.stats
        victim_stats = victim.stats
        actor_stat_operand = getattr(actor_stats, self.actor_stat_key)
        victim_stat_operand = getattr(victim_stats, self.victim_stat_key)
        new_value = self.operation(victim_stat_operand, actor_stat_operand)
        setattr(victim_stats, self.victim_stat_key, new_value)
        print("{}'s {} {} ---> {}".format(victim, self.victim_stat_key, victim_stat_operand, new_value))


class Entailment:
    '''\
        Subclasses encode custom changes to the state entailed by the application of
        a given effect or the execution of a given instruction.
    '''
    def __init__(self):
        pass

    def apply(self, actor, victim):
        raise NotImplementedError("Each subclass of Entailment must define this method with this signature on its own.")



class Ability:
    '''\
        Simplified version of an affordance---signaling to the game engine
        when a Piece or Rule, in the right context, affords one or more players
        an opportunity to undertake a certain course of action in the game.
    '''
    def __init__(self,
                 ability_name = None,
                 effect = None,
                 target_data = None,
                 antecedents = [],
                 active_zones = [0],
                 active_epoch_names = ["Precombat Main Phase", "Postcombat Main Phase"],
                 max_stack_size = 0,
                 must_be_actors_turn = True):
        self.ability_name = ability_name
        self.effect = effect
        self.target_data = target_data
        self.antecedents = list(antecedents)
        self.active_zones = list(active_zones)
        self.active_epoch_names = list(active_epoch_names)
        self.max_stack_size = max_stack_size
        self.must_be_actors_turn = must_be_actors_turn
        self.itsallbeendone = False

    def apply(self, actor, victims):
        print("{} used {}".format(actor, self.__repr__()))
        for victim in victims:
            print("{} used {} against {}".format(actor, self.__repr__(), victim))
            self.effect.apply(actor, victim)
        self.itsallbeendone = True

    @property
    def antecedents_verified(self):
        if not(self.itsallbeendone):
            if (self.target_data is not None):
                return True
        return False

    def solve_target_subscopes_given_actor(self, actor):
        if self.antecedents_verified:
            return self.target_data.solve_target_subscopes_given_actor(actor)
        return []

    def __repr__(self):
        return HIM + self.ability_name + DEF


class Special(Ability):
    '''\
        Subclass for Game.grant_priority() type-inference so that special actions
        auto-resolve and don't use the stack but can be represented in the same
        way Ability is implemented.
    '''
    pass


class NullAbility(Ability):
    def __init__(self):
        super().__init__(ability_name="Pass")

    def solve_target_subscopes_given_actor(self, actor):
        raise NotImplementedError("NullAbility cannot solve target subscopes.")

    def apply(self, actor, victims=[]):
        print("{} used {}".format(actor, self.__repr__()))


ABILITY_NULL = NullAbility()

