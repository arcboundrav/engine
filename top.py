from operator import add as ADD
from operator import sub as SUB
from operator import xor
from itertools import combinations, product, chain
from collections import defaultdict as defdict
from copy import deepcopy
import uuid
import numpy as np
np.random.seed(20211202)

##################################
# Combinatorics Helper Functions #
##################################
def powerset(x):
    '''\
        Generate the powerset of x.
    '''
    if not(isinstance(x, list)):
        x = list(x)
    N = len(x)
    N_ = N + 1
    return chain.from_iterable(combinations(x, r) for r in range(N_))


def subpowerset(x, n=1, N=None):
    '''\
        Generate the subset of the powerset of x where the elements are subsets
        with cardinalities falling in the closed interval [n:N].
    '''
    if not(isinstance(x, list)):
        x = list(x)

    # Case: [None, None] means "each / all / every"
    if (n is None):
        n = N = len(x)

    # Case: [n, None] means "n <= size <= len(X)"
    elif (N is None):
        N = len(x)

    N_ = N + 1
    return chain.from_iterable(combinations(x, r) for r in range(n, N_))


############################################
# Colour Constants for Terminal Formatting #
############################################
RESET = "\033[0;0m"
BOLD = "\033[;1m"

RED = RESET+"\033[0;31m"
HIR = RESET+"\033[1;31m"

GRN = RESET+"\033[0;32m"
HIG = RESET+"\033[1;32m"

YEL = RESET+"\033[0;33m"
HIY = RESET+"\033[1;33m"

BLU = RESET+"\033[0;34m"
HIB = RESET+"\033[1;34m"

MAG = RESET+"\033[0;35m"
HIM = RESET+"\033[1;35m"

CYN = RESET+"\033[0;36m"
HIC = RESET+"\033[1;36m"

DEF = RESET+"\033[0;37m"
HIK = RESET+"\033[1;30m"

WHITE = "\033[1:37m"
HIW = RESET+BOLD+WHITE

REVERSE = "\033[;7m"

TEAM_COLORS = [HIY, HIR]

TC_BUFFER_LINE = HIK+'________________________________________________________________________________\n'+RESET+''

def tc_buffer():
    print(TC_BUFFER_LINE)

def DP(object_name, object):
    print("{} <{}>: {}".format(object_name, type(object), object))


def random_choice(options):
    np.random.shuffle(options)
    return options[0]


##############################################
# Helper Functions For Solving Legal Actions #
##############################################
def verify_active_zone(piece, ability_to_verify):
    return piece.current_zone in ability_to_verify.active_zones


def verify_epoch_timing(piece, ability_to_verify):
    return piece.environment.current_epoch.msg in ability_to_verify.active_epoch_names


def verify_turn_timing(piece, ability_to_verify):
    if ability_to_verify.must_be_actors_turn:
        if (piece.owner is piece.environment.active_player):
            return True
        return False
    return True


def verify_stack_size(piece, ability_to_verify):
    return len(piece.environment.stack) <= ability_to_verify.max_stack_size


def verify_ability(piece, ability_to_verify):
    if verify_active_zone(piece, ability_to_verify):
        if verify_epoch_timing(piece, ability_to_verify):
            if verify_turn_timing(piece, ability_to_verify):
                if verify_stack_size(piece, ability_to_verify):
                    return True
    return False
