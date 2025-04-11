from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import json
import Call
import Operator

class QueueManager: 
    def __init__(self):
        self.operators = {op.id: op for op in [Operator.Operator("A"), Operator.Operator("B")]}
        self.callQueue = []
        self.activeCalls = {}
    
    def handleCommand(self, command):
        try:
            cmd = command.get("command")
            id = command.get("id")
            
            if cmd == "call":
                call = Call.Call(id)
                self.activeCalls[id] = call
                response = [f"Call {id} received"]
                assingment = self.assignCallToOperator(call)

                if not assingment:
                    self.callQueue.append(call)
                    response.append(f"Call {id} waiting in queue")
                else:
                    response.append(assingment)
                
                return response
            
            elif cmd == "answer":
                if self.checkForValidId(id):
                    return f"Invalid id: {id}"

                operator = self.operators.get(id)
                
                if operator and operator.state == "ringing":
                    call = operator.currentCall
                    call.answered = True
                    operator.state = "busy"
                    return f"Call {call.id} answered by operator {operator.id}"
            
            elif cmd == "reject":
                if self.checkForValidId(id):
                    return f"Invalid id: {id}"
                
                operator = self.operators.get(id)

                if operator and operator.state == "ringing":
                    call = operator.currentCall
                    call.assignedOperator = None
                    operator.state = "available"
                    operator.currentCall = None
                    response = [f"Call {call.id} rejected by operator {operator.id}"]

                    assingment = self.assignCallToOperator(call)

                    if not assingment:
                        self.callQueue.append(call)
                    else:
                        response.append(assingment)

                return response
                    
            elif cmd == "hangup":
                if self.checkForValidId(id):
                    return f"Invalid id: {id}"
                
                call = self.activeCalls.get(id)
                operator = call.assignedOperator
                
                if operator:
                    operator.state = "available"
                    operator.currentCall = None
                    operator.currentCallId = None

                if call.answered:
                    response = [f"Call {id} finished and operator {operator.id} available"]
                else:
                    response = [f"Call {id} missed"]

                if self.callQueue:
                    nextCall = self.callQueue.pop(0)
                    a = self.assignCallToOperator(nextCall)
                    if a:
                        response.append(a)

                del self.activeCalls[id]

                return response
        
        except Exception as e:
            return f"Error processing command"

    def assignCallToOperator(self, call):
        for operator in self.operators.values():
            if operator.state == "available":
                operator.state = "ringing"
                operator.currentCall = call
                call.assignedOperator = operator
                return f"Call {call.id} ringing for operator {operator.id}"
        
        return None
    
    def checkForValidId(self, id):
        if id not in self.activeCalls and id not in self.operators and id not in self.callQueue:
            return True
        return False


class QueueManagerProtocol(LineReceiver):
    def __init__(self, queueManager):
        self.queueManager = queueManager
    
    def lineReceived(self, line):
        command = json.loads(line)
        response = self.queueManager.handleCommand(command)
        
        if response:
            self.sendLine(json.dumps({"response": response}).encode('utf-8'))

class QueueManagerFactory(Factory):
    def __init__(self):
        self.queueManager = QueueManager()
    
    def buildProtocol(self, addr):
        return QueueManagerProtocol(self.queueManager)

reactor.listenTCP(5678, QueueManagerFactory())
print("Call center server started on port 5678")
reactor.run()