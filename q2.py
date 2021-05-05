from __future__ import annotations
import queue
from itertools import chain, combinations
from typing import Union
import sys
import json


class State:

    def __init__(self, name: Union[str, set]):
        self.name = name
        self.adjs = []
        self.delta_s = {}
        for letter in alphabets:
            self.delta_s[letter] = set()

    def bfs(self):
        # Initiliase Queue
        q = queue.Queue()
        # Add this state to q
        q.put(self)
        length = 0
        # Do a BFS.. The length should be less than 2*epsilon + 1 as if it becomes equal that means the queue has extra stuff without edges..
        while (not q.empty()) and length <= 2 * epsilon_count + 1:
            length += 1
            state = q.get()  # get the top of the Queue
            # visit the adjacency list of this State (BFS)
            for neighbor, letter in state.adjs:
                if letter == '$':
                    # If this is a epsilon transition, add to q, this will lead to new state..
                    q.put(neighbor)
                else:
                    # This is normal edge.. Calculate Transition...
                    self.delta_s[letter].add(neighbor)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return str(self.name).replace(' ', '')

    def mystr(self):
        if isinstance(self.name, str):
            temp = [self.name]
        else:
            temp = list(self.name)
        return temp

    def __repr__(self):
        return self.__str__()


def states_to_list(states):
    states_list = []
    for state in states:
        states_list.append(str(state))
    return states_list


def convert_to_dfa(nfa):
    states_list = states_to_list(nfa)  # Get a list of states in NFA...
    powerset = list(map(set, chain.from_iterable(combinations(
        list(states_list), r) for r in range(len(list(states_list)) + 1))))
    dfa = [State(dfa_state)
           for dfa_state in powerset]  # DFA has power set of NFA

    # Calculating DFAs' transitions for all states using NFAs' transitions we calcuted using BFS for every state and alphabets
    for dfa_state in dfa:
        nfa_states = [st for st in nfa if st.name in dfa_state.name]
        for letter in alphabets:
            dst = set()
            for sub_state in nfa_states:
                dst.update(sub_state.delta_s[letter])
            dst = [st for st in dfa if st.name == dst][0]
            dfa_state.adjs.append((dst, letter))

    return dfa


if __name__ == '__main__':
    # Read the input file and set output file
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    # JSON Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
        # These are the alphabets
        alphabets = data["letters"]
        # Initialise given NFA using State Class
        nfa = [State(st_name) for st_name in data["states"]]
        # Initial Start State's Name
        int_st_name = data["start_states"][0]
        # Get the State Object from NFA which has same name as initial state
        initial_state = [st for st in nfa if st.name ==
                         int_st_name][0]  # Object of Initial State
        # This is a list of Final States
        fnl_st_name = data["final_states"]  # List of Object of Final State
        # Get a list of all objects of State of NFA having name in Final States
        final_states = [st for st in nfa if st.name in fnl_st_name]

        # Get all Transitions
        epsilon_count = 0  # Counts epsilon transitions for bfs termination
        transitions = data["transition_function"]
        for transition in transitions:
            src = []
            dst = []
            curr_from = transition[0]
            curr_to = transition[-1]
            for st in nfa:
                if st.name == curr_from:
                    src = st
                if st.name == curr_to:
                    dst = st
            if transition[1] == '$':
                epsilon_count += 1
            src.adjs.append((dst, transition[1]))
    # After reaching here the whole NFA is made...
    # For each state in NFA we do a BFS...
    # In BFS we visit all States reachable from this State and get the Transitions to those states, including epsilon transitions...
    for st in nfa:
        st.bfs()
    dfa = convert_to_dfa(nfa)
    with open(output_file, 'w') as f:
        states = []
        final_states = [st.mystr() for st in dfa if set(
            states_to_list(st.name)) & set(fnl_st_name)]
        for state in dfa:
            states.append(state.mystr())
        transition_function = []
        for st in dfa:
            for adj in st.adjs:
                transition_function.append(
                    [st.mystr(), adj[1], adj[0].mystr()])
        output = {
            "letters": alphabets,
            "states": states,
            "start_states": [[int_st_name]],
            "final_states": final_states,
            "transition_function": transition_function}
        json.dump(output, f, indent=4)
