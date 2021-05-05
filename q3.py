import sys
import json


class transition:
    _from = ""
    _to = ""
    _value = ""

    def __init__(self, _from, _to, _value):
        self._from = _from
        self._to = _to
        self._value = _value


class State:
    label = ""
    isStart = False
    isAccept = False
    inTransitions = {}
    outTransitions = {}
    selfLoop = None

    def __init__(self, label, isAccept, isStart):
        self.label = label
        self.isAccept = isAccept
        self.isStart = isStart
        self.inTransitions = {}
        self.outTransitions = {}

    def addSelfLoop(self, value):
        if self.selfLoop == None:
            self.selfLoop = transition(self.label, self.label, value)
        else:
            self.selfLoop._value = "("+self.selfLoop._value+"+"+value+")"

    def addInTransition(self, from_, value_):
        if (not(from_ in self.inTransitions)):
            self.inTransitions[from_] = transition(from_, self.label, value_)
        else:
            self.inTransitions[from_]._value = "(" + \
                self.inTransitions[from_]._value+"+"+value_+")"

    def addOutTransition(self, to_, value_):
        if (not(to_ in self.outTransitions)):
            self.outTransitions[to_] = transition(self.label, to_, value_)
        else:
            self.outTransitions[to_]._value = "(" + \
                value_+"+"+self.outTransitions[to_]._value+")"

    def removeInTransitions(self, dest):
        self.inTransitions.pop(dest, None)

    def removeOutTransitions(self, dest):
        self.outTransitions.pop(dest, None)


class Regex:
    fsm = {}
    start = ""
    accept = []
    allStates = []

    def addNewStart(self):
        # Add new start state qinit and connect to old start.. by $. Make the old start non-start
        newStart = State("qinit", False, True)
        newStart.addOutTransition(self.fsm[self.start].label, "$")
        self.fsm[newStart.label] = newStart
        self.fsm[self.start].isStart = False
        self.fsm[self.start].addInTransition(newStart.label, "$")
        self.start = newStart.label
        self.allStates.insert(0, newStart.label)

    def addNewAccept(self):
        # Add new final state qfin and connect all final states to qfin by $ and make them non-accept
        newAccept = State("qfin", True, False)
        for state in self.fsm.values():
            if state.label in self.accept:
                newAccept.addInTransition(state.label, "$")
                state.addOutTransition(newAccept.label, "$")
                state.isAccept = False
                self.accept.remove(state.label)
        self.fsm[newAccept.label] = newAccept
        self.accept.append(newAccept.label)
        self.allStates.append(newAccept.label)

    def removeDeadState(self):
        # Remove Dead States.. (ie without outgoing transition and is not a final state)
        removed = True
        while removed:
            label = ""
            removed = False
            for state in self.fsm.values():
                if len(state.outTransitions) == 0 and not state.isAccept:
                    for trans in state.inTransitions.values():
                        self.fsm[trans._from].outTransitions.pop(trans._to)
                        removed = True
                    label = state.label
            if label != "":
                self.fsm.pop(label)
            if label in self.allStates:
                self.allStates.remove(label)

    def pickState(self):
        # returns state with least amount of transitions to be removed...
        optimum_list = []
        curr_sum = 0
        for state in self.fsm.values():
            curr_sum = 0
            if not state.isAccept and not state.isStart:
                if state.selfLoop != None:
                    curr_sum += 1
                curr_sum += len(state.inTransitions) + \
                    len(state.outTransitions)
                optimum_list.append((state.label, curr_sum))
        mini = None
        for value in optimum_list:
            if mini == None:
                mini = value
            elif mini[1] > value[1]:
                mini = value
        mini = mini[0]
        return mini

    def eliminateState(self):
        # remove Dead States
        self.removeDeadState()
        # Pick a state with least amount of transitions to remove...
        removeState = self.pickState()
        # State = qrip
        state = self.fsm[removeState]
        # removeIn, removeOut are transitions to remove after loop finished
        removeIn = []
        removeOut = []
        # For all incoming states
        for transIn in state.inTransitions.values():
            # For all outgoing states
            for transOut in state.outTransitions.values():
                transIn._value = "" if transIn._value == "$" else transIn._value
                transOut._value = "" if transOut._value == "$" else transOut._value
                # If incoming from and outgoing to are same(self loop)
                if transIn._from == transOut._to:
                    if self.fsm[state.label].selfLoop == None:
                        self.fsm[transIn._from].addSelfLoop(
                            transIn._value+transOut._value)
                    else:
                        selfLoopValue = state.selfLoop._value if len(
                            state.selfLoop._value) == 1 else "("+state.selfLoop._value+")"
                        self.fsm[transIn._from].addSelfLoop(
                            transIn._value+selfLoopValue+"*"+transOut._value)
                # Ex:  q1 -> q2 -> q3   transIn.from = q1 tranOut.to = q3
                else:
                    if self.fsm[state.label].selfLoop == None:
                        self.fsm[transIn._from].addOutTransition(
                            transOut._to, transIn._value+transOut._value)
                        self.fsm[transOut._to].addInTransition(
                            transIn._from, transIn._value+transOut._value)
                    else:
                        selfLoopValue = state.selfLoop._value if len(
                            state.selfLoop._value) == 1 else "("+state.selfLoop._value+")"
                        self.fsm[transIn._from].addOutTransition(
                            transOut._to, transIn._value+selfLoopValue+"*"+transOut._value)
                        self.fsm[transOut._to].addInTransition(
                            transIn._from, transIn._value+selfLoopValue+"*"+transOut._value)
                removeOut.append(transOut._to)
            removeIn.append(transIn._from)
        self.allStates.remove(removeState)
        self.fsm.pop(removeState)
        # Remove all transitions
        for state in removeOut:
            self.fsm[state].removeInTransitions(removeState)
        for state in removeIn:
            self.fsm[state].removeOutTransitions(removeState)

    def main(self):
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        transitions = []
        with open(input_file, 'r') as f:
            data = json.load(f)
            self.start = data["start_states"][0]
            self.accept = data["final_states"]
            self.allStates = data["states"]
            transitions = data["transition_function"]

        for state in self.allStates:
            self.fsm[state] = State(
                state, (state in self.accept), (state == self.start))
        for transition in transitions:
            from_ = transition[0]
            value_ = transition[1]
            to_ = transition[2]
            if from_ == to_:
                self.fsm[from_].addSelfLoop(value_)
            else:
                self.fsm[from_].addOutTransition(to_, value_)
                self.fsm[to_].addInTransition(from_, value_)
        self.addNewAccept()  # Add new Accept
        self.addNewStart()  # Add new start
        # until we have only start and end left, eliminate state by state
        while len(self.fsm) > 2:
            # remove q rip
            self.eliminateState()
        # print(self.fsm["qinit"].outTransitions["qfin"]._value)
        # final regex is the edge between qinit and qfin
        with open(output_file, "w") as f:
            output = {
                "regex": self.fsm["qinit"].outTransitions["qfin"]._value
            }
            json.dump(output, f, indent=4)


re = Regex()
re.main()
