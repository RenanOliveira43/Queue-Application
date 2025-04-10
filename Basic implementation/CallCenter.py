import cmd
import Call
import Operator

class CallCenter(cmd.Cmd):
    def __init__(self, operators):
        super().__init__()
        self.operators = {operator.id: operator for operator in operators}
        self.callQueue = []
        self.activeCalls = {}
    
    def do_call(self, callId):
        call = Call.Call(callId)
        self.activeCalls[callId] = call

        print(f"Call {callId} received")

        if not self.assignCallToOperator(call):
            self.callQueue.append(call)
            print(f"Call {callId} waiting in queue")

    def assignCallToOperator(self, call):
        for operator in self.operators.values():
            if operator.state == "avaliable":
                operator.state = "ringing"
                operator.currentCall = call
                call.assignedOperator = operator
        
                print(f"Call {call.id} ringing for operator {operator.id}")
                return True
            
        return False

    def do_answer(self, operatorId):
        operator = self.operators.get(operatorId)
        
        if operator and operator.state == "ringing":
            call = operator.currentCall
            call.answerd = True
            operator.state = "busy"
            print(f"Call {call.id} answered by operator {operator.id}")

    def do_reject(self, operatorId):
        operator = self.operators.get(operatorId)
        
        if operator and operator.state == "ringing":
            call = operator.currentCall
            call.assignedOperator = None
            operator.state = "avaliable"
            operator.currentCall = None
            print(f"Call {call.id} rejected by operator {operator.id}")

            if not self.assignCallToOperator(call):
                self.callQueue.append(call)
    
    def do_hangup(self, callId):
        call = self.activeCalls.get(callId)
        
        if call:
            operator = call.assignedOperator

            if operator:
                operator.state = "avaliable"
                operator.currentCall = None
                operator.currentCallId = None

            if call.answerd:
                print(f"Call {callId} finished and operator {operator.id} avaliable")
            else:
                print(f"Call {callId} missed")
            
            if self.callQueue:
                nextCall = self.callQueue.pop(0)
                self.assignCallToOperator(nextCall)
            
            del self.activeCalls[callId]
    
    def do_exit(self, arg):
        print("Exiting Call Center")
        return True

if __name__ == "__main__":
    operators = [Operator.Operator("A"), Operator.Operator("B")]
    CallCenter(operators).cmdloop()