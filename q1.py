import sys
import json

transition_function = []
hase = False
letters = []
final_states = set()
from_states = set()
final_states2 = []


class VertexEdge:
    '''Class representing the Vertex/Edge of Expression Tree'''

    def __init__(self, _type, left, right, value):
        # Type represents the Type of the edge - 1-char, 2-*,3-+,4-.
        self._type = _type
        # Value will be None if it is an edge...
        self.value = value
        # Left and right connections...
        self.left = left
        self.right = right


class NFA:
    '''Class representing an NFA. The final solution is a recursive building of this'''

    def __init__(self):
        self.next_state = {}


def constructTree(postfix):
    '''Given a postfix expression, construct the corresponding expression tree.'''
    global letters

    nfa_stack = []  # Make an empty stack

    # loop through the characters in the postfix regular expression
    for c in postfix:
        # if c is an alpha or a num
        if c.isalnum():
            # Make a new Vertex out of this character...
            letters.append(c)
            z = VertexEdge(1, None, None, c)
        else:
            if c == "*":
                # Pop a single element and make a new Vertex/Edge
                left = nfa_stack.pop()
                z = VertexEdge(2, left, None, None)
            else:
                # Pop 2 Vertex off the stack
                right = nfa_stack.pop()
                left = nfa_stack.pop()
                # Make a Vertex NFA
                if c == "+":
                    z = VertexEdge(3, left, right, None)
                else:
                    z = VertexEdge(4, left, right, None)
        # Append the new Vertex to stack
        nfa_stack.append(z)
    # There will be only one element on stack at this point if the expression is correct.. Pop it...
    return nfa_stack.pop()


def shunt(infix):
    # Add .
    temp = []
    for i in range(len(infix)):
        if i != 0 and (infix[i-1].isalnum() or infix[i-1] == ")" or infix[i-1] == "*") and (infix[i].isalnum() or infix[i] == "("):
            temp.append(".")
        temp.append(infix[i])
    infix = temp
    specials = {'*': 3, '.': 2, '+': 1}
    pofix = ""
    stack = ""

    for c in infix:

        if c == '(':
            # Add '(' to stack
            stack = stack + c
        elif c == ')':
            while stack[-1] != '(':
                # Add the last item on the stack to pofix, then Remove '(' from stack
                pofix, stack = pofix + stack[-1], stack[:-1]
            # Remove '(' from stack
            stack = stack[:-1]

        elif c in specials:
            # Compare precedence of special characters
            while stack and specials.get(c, 0) <= specials.get(stack[-1], 0):
                # Add the last item on the stack to pofix, then Remove it from stack
                pofix, stack = pofix + stack[-1], stack[:-1]
            # Add character to the stack
            stack = stack + c
        else:
            # Add character to Postfix Expression
            pofix = pofix + c

    while stack:
        # Add the last item on the stack to pofix, then Remove '(' from stack
        pofix, stack = pofix + stack[-1], stack[:-1]

    return pofix


def getNFA(et):
    # returns equivalent E-NFA for given expression tree (representing a Regular
    # Expression)
    if et._type == 1:
        # This is a symbol..
        start_state = NFA()
        end_state = NFA()
        # Make NFA : start ->(a) end
        start_state.next_state[et.value] = [end_state]
        # and return start and end state
        return start_state, end_state
    elif et._type == 2:
        # '*' Operator
        # Get the sub NFA...
        start_state = NFA()
        end_state = NFA()
        sub_nfa = getNFA(et.left)
        # An ε-transition connects initial and final state of the NFA with the sub-NFA N(s) in between. Another ε-transition from the inner final to the inner initial state of N(s) allows for repetition of expression s according to the star operator.
        start_state.next_state['$'] = [sub_nfa[0], end_state]
        sub_nfa[1].next_state['$'] = [sub_nfa[0], end_state]
        return start_state, end_state
    elif et._type == 3:
        # The '+' Operator
        # Get the NFA to the top.. Get NFA to the bottom.. i.e left and right NFAs of tree
        start_state = NFA()
        end_state = NFA()
        up_nfa = getNFA(et.left)
        down_nfa = getNFA(et.right)
        # State q goes via ε either to the initial state of N(s) or N(t). Their final states become intermediate states of the whole NFA and merge via two ε-transitions into the final state of the NFA.
        start_state.next_state['$'] = [up_nfa[0], down_nfa[0]]
        up_nfa[1].next_state['$'] = [end_state]
        down_nfa[1].next_state['$'] = [end_state]
        return start_state, end_state
    elif et._type == 4:
        # '.' operator
        # Get Left and right NFA
        left_nfa = getNFA(et.left)
        right_nfa = getNFA(et.right)
        # The initial state of N(s) is the initial state of the whole NFA. The final state of N(s) becomes the initial state of N(t). The final state of N(t) is the final state of the whole NFA. They are connected by $.
        left_nfa[1].next_state['$'] = [right_nfa[0]]
        return left_nfa[0], right_nfa[1]


def getTransitions(state, states_done, symbol_table, f):
    global transition_function
    global from_states
    global final_states
    global hase
    global final_states2
    if state == f:
        final_states2 = ["Q"+str(symbol_table[state])]

        # If it has been already added.. don't add..
    if state in states_done:
        return
    # This is done now.. so add to the done list
    states_done.append(state)
    # Get the symbols from this state (keys of the dictionary next_state)
    frs = "Q"+str(symbol_table[state])  # from_state
    for symbol in list(state.next_state):  # Get the symbols from this state
        # get the next state of this symbol
        for ns in state.next_state[symbol]:
            if ns not in symbol_table:
                # If not in symbol table, increment highest value of symbol by one and add this...
                symbol_table[ns] = 1 + sorted(symbol_table.values())[-1]
            nxs = "Q" + str(symbol_table[ns])  # Next State
            # Append to global transition function
            transition_function.append([frs, symbol, nxs])
            if symbol == "$":
                hase = True
            from_states.add(frs)
            final_states.add(nxs)
        # Recursive calls
        for ns in state.next_state[symbol]:
            getTransitions(ns, states_done, symbol_table, f)


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    with open(input_file, "r") as f:
        r = json.load(f)
        r = r["regex"]
    r = r.replace(" ", "")
    pr = shunt(r)
    et = constructTree(pr)
    nfa = getNFA(et)
    getTransitions(nfa[0], [], {nfa[0]: 0}, nfa[1])
    #final_states2 = list(final_states.difference(from_states))
    start_states = ["Q0"]
    states = list(final_states.union(from_states))
    letters = list(set(letters))
    if hase == True:
        letters.append("$")
    output = {
        "states": sorted(states),
        "letters": sorted(letters),
        "transition_function": transition_function,
        "start_states": start_states,
        "final_states": final_states2,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=4)
