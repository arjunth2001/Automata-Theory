import sys
import json
from collections import deque


class State(object):

    def __init__(self, name, accepting, transitions, alphabet, state_names=None):
        self.name = name
        self.accepting = accepting
        self.transitions = transitions

    def transition(self, symbol):
        if symbol not in self.transitions.keys():
            return ""
        else:
            return self.transitions[symbol]

    def copy(self):
        return State(self.name, self.accepting, dict(self.transitions), list(self.transitions.keys()))


class DFA(object):

    def __init__(self, states, start_name, alphabet):
        self.states = states
        self.alphabet = alphabet
        self.start_name = start_name

    def copy(self):
        return DFA({name: self.states[name].copy() for name in self.states.keys()}, self.start_name, list(self.alphabet))

    def get_class(self, state, eq_classes):
        for eq_class in eq_classes:
            if state in eq_class:
                return eq_class
        return [state]

    def assignment_output(self, eq_classes):
        output_file = sys.argv[2]
        states = sorted([self.get_class(x, eq_classes)
                         for x in self.states.keys()])
        letters = sorted(self.alphabet)
        start_states = [self.get_class(self.start_name, eq_classes)]
        final_states = sorted([self.get_class(n, eq_classes)
                               for n in self.states.keys() if self.states[n].accepting])
        transition_function = []
        for name in self.states.keys():
            for alpha in self.states[name].transitions.keys():
                to = self.states[name].transitions[alpha]
                transition_function.append(
                    [self.get_class(name, eq_classes), alpha, self.get_class(to, eq_classes)])
        output = {
            "states": states,
            "letters": letters,
            "start_states": start_states,
            "final_states": final_states,
            "transition_function": transition_function,
        }
        # print(output)
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

    def imm_state_equiv(self, sName1, sName2):
        s1 = self.states[sName1]
        s2 = self.states[sName2]
        if s1.accepting != s2.accepting:
            return False

        if s1.transitions != s2.transitions:
            return -1

        return True

    def minimised(self):

        machine = self.copy()

        # First remove any orphaned subgraphs. Handles some cases the table-filling algorithm misses. Here we use BFS
        reachables = []
        to_process = deque([self.start_name])
        # BFS
        while len(to_process) != 0:
            current = to_process.popleft()
            reachables.append(current)

            for name in self.states[current].transitions.values():
                if not (name in reachables or name in to_process):
                    to_process.append(name)
        # delete Unreachable States
        state_names = list(machine.states.keys())
        for name in state_names:
            if name not in reachables:
                del machine.states[name]

        # Use the table-filling algorithm to determine equivalence classes.
        state_names = list(machine.states.keys())
        equivalences = {state_names[i]: {
            state_names[i]: -1 for i in range(len(state_names))} for i in range(len(state_names))}

        # Accepting/non-accepting distinction:
        for state1 in state_names:
            for state2 in state_names:
                equivalences[state1][state2] = equivalences[state2][state1] = machine.imm_state_equiv(
                    state1, state2)

        # Determine all inequivalences
        new_results = True
        # While there are new results...
        while new_results:
            new_results = False

            for state1 in state_names:
                for state2 in state_names:
                    if state1 == state2:
                        continue
                     # If the equivalence of two states in undetermined, we can look for transitions of the two states
                    #  on the same symbol, where the destinations are known to be distinct. If such transitions are
                    #  found, the original states are known to be distinct also.
                    equivalence = equivalences[state1][state2]

                    if equivalence == -1:
                        for letter in machine.alphabet:
                            if machine.states[state1].transition(letter) == "" or machine.states[state2].transition(letter) == "":
                                continue
                            if equivalences[machine.states[state1].transition(letter)][machine.states[state2].transition(letter)] == False:
                                equivalences[state1][state2] = equivalences[state2][state1] = False
                                new_results = True
                                continue
                    # If certain states are equivalent, they must share equivalence relations with all other states.
                    elif equivalence == True:
                        for name in state_names:
                            if equivalences[state1][name] != equivalences[state2][name]:
                                new_results = True
                                if equivalences[state1][name] == -1:
                                    equivalences[state1][name] = equivalences[state2][name]
                                else:
                                    equivalences[state2][name] = equivalences[state1][name]

        # Anything left is an equivalence, so make them one
        for state1 in state_names:
            for state2 in state_names:
                if equivalences[state1][state2] == -1:
                    equivalences[state1][state2] = True

        # Build a list of equivalence classes, for easier processing.
        eq_classes = []
        for state in state_names:
            redundant = False
            for eq_class in eq_classes:
                if state in eq_class:
                    redundant = True
                    break
            if redundant:
                continue

            eq_class = []
            for k, v in equivalences[state].items():
                if v:
                    eq_class.append(k)
            eq_classes.append(sorted(eq_class))

        # Redirect the start state
        for eq_class in eq_classes:
            if machine.start_name in eq_class:
                machine.start_name = eq_class[0]

        # Remove redundant states from the machine
        for eq_class in eq_classes:
            if len(eq_class) > 1:
                for name in eq_class[1:]:
                    del machine.states[name]

        # Redirect transitions to redundant states
        for state in machine.states.values():
            for k, v in state.transitions.items():
                for eq_class in eq_classes:
                    if v in eq_class:
                        state.transitions[k] = eq_class[0]

        return machine, eq_classes


def parse_dfa():
    # Initialize the DFA
    dfa = dict(dict())
    input_file = sys.argv[1]
    data = None
    with open(input_file, 'r') as f:
        data = json.load(f)
    transition_fun = data["transition_function"]
    for trans in transition_fun:
        original_state = trans[0]
        transition_character = trans[1]
        resulting_state = trans[2]
        if original_state in dfa:
            dfa[original_state].update({transition_character: resulting_state})
        else:
            dfa[original_state] = {transition_character: resulting_state}

    state_names = data["states"]
    alphabet = data["letters"]
    start_name = data["start_states"][0]
    accept_states = data["final_states"]

    if alphabet == ['']:
        alphabet = []
    if accept_states == ['']:
        accept_states = []

    states = {state_names[i]: State(state_names[i], state_names[i] in accept_states,
                                    dfa[state_names[i]], alphabet, state_names) for i in range(len(state_names))}

    return DFA(states, start_name, alphabet)


if __name__ == '__main__':
    dfa = parse_dfa()
    min_dfa, eq = dfa.minimised()
    min_dfa.assignment_output(eq)
