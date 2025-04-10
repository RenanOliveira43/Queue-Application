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
        cmd = command.get("command")
        id = command.get("id")

        if cmd == "call":
            call = Call.Call(id)
            self.activeCalls[id] = call

            response = [f"Call {id} received\n"]

            if not self.assignCallToOperator(call):
                self.callQueue.append(call)
                response.append(f"Call {id} waiting in queue\n")
            
            return response
        
        elif cmd == "answer":
            operator = self.operators.get(id)
        
            if operator and operator.state == "ringing":
                call = operator.currentCall
                call.answerd = True
                operator.state = "busy"
                return f"Call {call.id} answered by operator {operator.id}\n"
        
        elif cmd == "reject":
            operator = self.operators.get(id)
        
            if operator and operator.state == "ringing":
                call = operator.currentCall
                call.assignedOperator = None
                operator.state = "avaliable"
                operator.currentCall = None
                response = [f"Call {call.id} rejected by operator {operator.id}\n"]

                if not self.assignCallToOperator(call):
                    self.callQueue.append(call)

            return response

    
    def assignCallToOperator(self, call):
        for operator in self.operators.values():
            if operator.state == "avaliable":
                operator.state = "ringing"
                operator.currentCall = call
                call.assignedOperator = operator
        
                return f"Call {call.id} ringing for operator {operator.id}\n"
        
        return None
    
class QueueManagerProtocol(LineReceiver):
    def __init__(self, queueManager):
        self.queueManager = queueManager
    
    def lineReceived(self, line):
        command = json.loads(line)
        response = self.queueManager.handleCommand(command)
        
        if response:
            self.sendLine(json.dumps(response).encode('utf-8'))

class QueueManagerFactory(Factory):
    def __init__(self):
        self.queueManager = QueueManager()
    
    def buildProtocol(self, addr):
        return QueueManagerProtocol(self.queueManager)

reactor.listenTCP(5678, QueueManagerFactory())
print("Call center server started on port 5678")
reactor.run()