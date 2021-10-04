from pieces import *


def same_player(actor):
    return [actor]


def other_players(actor):
    ''' Assumes that actors can never target themselves with an Ability. '''
    return filter(lambda player: (player is not actor), PLAYERS)


def opponent_pieces(actor):
    return filter(lambda piece: (piece.owner is not actor), PIECES)


def actor_pieces(actor):
    return filter(lambda piece: (piece.owner is actor), PIECES)


def all_pieces(actor):
    return PIECES


def filter_by_identity_and_team_ids(actor, legal_team_ids):
    '''\
        Return the subset of PLAYERS which:
            are not a given actor, aka, other_players(actor); and,
            have a team_id in legal_team_ids
    '''
    def player_team_id_predicate(player):
        return player.team_id in legal_team_ids
    return filter(player_team_id_predicate, other_players(actor))


def allies(actor):
    ''' Assumes that team_ids are either 0 or 1. '''
    return filter_by_identity_and_team_ids(actor, {actor.team_id})


def enemies(actor):
    ''' Assumes that team_ids are either 0 or 1. '''
    return filter_by_identity_and_team_ids(actor, {not(actor.team_id)})

def all_players(actor):
    return PLAYERS


class TargetData:
    '''\
        Only supports cardinality constraints which are fixed constants given as size.
    '''
    def __init__(self, size, filtration):
        self.size = size
        self.filtration = filtration

    def solve_target_subscopes_given_actor(self, actor):
        # -> List[Tuple[Player]]
        candidate_target_set = self.filtration(actor)
        return list(combinations(candidate_target_set, self.size))


TARGET_single_self = TargetData(1, same_player)
TARGET_single_enemy = TargetData(1, enemies)
TARGET_single_ally = TargetData(1, allies)
TARGET_single_player = TargetData(1, other_players)

TARGET_double_enemy = TargetData(2, enemies)
TARGET_double_player = TargetData(2, other_players)

TARGET_triple_player = TargetData(3, other_players)
