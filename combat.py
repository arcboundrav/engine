from top import *


###################################################################
# Helper Functions Supporting the Combat Phase Turn-Based Actions #
###################################################################


def validate_blocker_restrictions(declared_blockers, n_declared_blockers):
    result = True
    for blocker in declared_blockers:
        if blocker.cannot_block:
            result = False
            break
        elif blocker.cannot_block_alone:
            if (n_declared_blockers == 1):
                result = False
                break
    return result


def validate_attacker_restrictions(declared_attackers, n_declared_attackers):
    result = True
    for attacker in declared_attackers:
        if attacker.cannot_attack:
            result = False
            break
        elif attacker.cannot_attack_alone:
            if (n_declared_attackers == 1):
                result = False
                break
    return result


def validate_unique_attackers(declared_attackers, n_declared_attackers):
    return len(set(declared_attackers)) == n_declared_attackers


def validate_attacker_declaration(tuple_of_tuples):
    declared_attackers = [t[0] for t in tuple_of_tuples]
    n_declared_attackers = len(declared_attackers)
    # Case: Obeys the rule that each attacker may only attack a single attackable in any
    #       given declaration.
    if validate_unique_attackers(declared_attackers, n_declared_attackers):
        # Case: Among declared attackers, none have any restrictions that are being violated.
        if validate_attacker_restrictions(declared_attackers, n_declared_attackers):
            return True
    return False


def declare_attackers(attackers, attackables):
    if attackers:
        if attackables:
            attackers_X_attackables = product(attackers, attackables)
            # NOTE #
            # declarations_to_filter is a generator which yields tuples containing
            # tuples containing ProxyPlayers or ProxyPieces.
            declarations_to_filter = subpowerset(attackers_X_attackables, n=1, N=len(attackers))
            filtered_declarations = filter(lambda dec: validate_attacker_declaration(dec), declarations_to_filter)
            return list(filtered_declarations)
    return None


def return_attackers(declaration_of_attackers):
    return [t[0] for t in declaration_of_attackers]


def which_attacker_subsets(subP_A, b):
    '''\
        Filter subP_A to include only those subsets of attackers which are
        legal subsets for b (as a strict function of b for now).
    '''
    result = []
    for attacker_subset in subP_A:
        subset_cardinality = len(attacker_subset)
        if (subset_cardinality <= b.max_block_n):
            if (subset_cardinality >= b.min_block_n):
                result.append(attacker_subset)
    return result


def translate_into_blocker_declaration(bt, tuple_of_tuple_of_attackers):
    '''\
        Alter representation of a pairing of attackers_to_block for each blocker
        in a choice of blockers to declare.
    '''
    translation = {}
    n = len(bt)
    for i in range(n):
        key = bt[i]
        value = tuple_of_tuple_of_attackers[i]
        translation[key] = value
    return translation


def invert_blocker_declaration(blocker_declaration):
    '''\
        Given a translated blocker declaration return the inverse representation,
        i.e., instead of keys as blockers and values as tuples of the attackers each
        blocker is going to block, return keys as attackers and values as tuples of
        blockers that will be blocking that attacker.
    '''
    inverse_blocker_declaration = dict()
    unique_attackers_being_blocked = set([])

    # Take the union of the attackers being blocked in this declaration to act
    # as the keys of the inverse declaration.
    for choice_of_attackers_to_block in blocker_declaration.values():
        unique_attackers_being_blocked |= set(choice_of_attackers_to_block)

    # Collect the blockers who will be blocking this attacker according to the
    # blocker_declaration.
    for unique_attacker_being_blocked in unique_attackers_being_blocked:
        inverse_blocker_declaration[unique_attacker_being_blocked] = []
        for blocker in blocker_declaration:
            if (unique_attacker_being_blocked in blocker_declaration[blocker]):
                inverse_blocker_declaration[unique_attacker_being_blocked].append(blocker)

    return inverse_blocker_declaration


def solve_blocker_declarations(A, B):
    '''\
        Given a list of attackers who are attacking, and a list of possible blockers,
        return a list of dictionaries where each dictionary is of the form:
            key   : unique choice of blocker
            value : tuple of attackers they will be blocking
    '''
    # All possible ways to select >=1 a in A.
    # NOTE # Cast as list since it needs to be re-used.
    subP_A = list(subpowerset(A, n=1, N=None))

    # All possible ways to select >=1 b in B.
    # NOTE # This one can be left as a generator as opposed to the one above.
    subP_B = subpowerset(B, n=1, N=None)

    result = []
    for choice_of_blockers in subP_B:
        basis = [which_attacker_subsets(subP_A, blocker) for blocker in choice_of_blockers]
        tuples_mapping_attackers_to_block_for_each_blocker_in_choice_of_blockers = list(product(*basis))
        for tuple_to_translate in tuples_mapping_attackers_to_block_for_each_blocker_in_choice_of_blockers:
            result.append(translate_into_blocker_declaration(choice_of_blockers, tuple_to_translate))


    return result


def derive_assignment_orders_(t):
    '''\
        Takes a 2-tuple, t, of the form:
            t[0] = attacker
            t[1] = [b0, ..., bN-1] (i.e., the blockers chosen to block it)
        Returns a list of new tuples t_i of length N! of the form:
            t_i[0] = attacker
            t_i[1] = a distinct permutation of t[1].
    '''
    N = len(t[1])

    # Case: There aren't alternative assignment orders.
    if (N < 2):
        return [t]

    # Case: Alternative assignment orders to derive.
    assignment_orders = permutations(t[1], N)
    return [(t[0], list(assignment_order)) for assignment_order in assignment_orders]


def derive_assignment_orders(ibd):
    new_basis = [derive_assignment_orders_(item) for item in ibd.items()]
    return list(product(*new_basis))


# DONE # Logic governing attacker damage assignment order.
# 703.4i Immediately after blockers have been declared during the declare blockers step,
# for each attacking creature that’s become blocked by multiple creatures, the active player
# announces the damage assignment order among the blocking creatures. See rule 509.2

def attacker_damage_assignment_orders(d):
    return derive_assignment_orders(d)


# DONE # Logic governing blocker damage assignment order.
# 703.4j Immediately after the active player has announced damage assignment orders (if necessary)
# during the declare blockers step, for each creature that’s blocking multiple creatures, the
# defending player announces the damage assignment order amongthe attacking creatures.
# See rule 509.3.
def blocker_damage_assignment_orders(ibd):
    return derive_assignment_orders(ibd)
