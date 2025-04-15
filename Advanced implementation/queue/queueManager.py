from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import json
import Call
import Operator

class QueueManager: 
    """
    This class handles commands such as call, answer, reject, and hangup, and 
    ensures proper call routing and operator assignment.
    """
    def __init__(self):
        """
        Initializes the QueueManager instance with the following attributes:
        - operators: A dictionary of available operators, keyed by their IDs.
        - callQueue: A list to hold calls waiting to be assigned to an operator.
        - activeCalls: A dictionary of currently active calls, keyed by their IDs.
        - callTimers: A dictionary to manage timeouts for calls, keyed by call IDs.
        - currentClient: The current client connection being handled.
        """
        self.operators = {op.id: op for op in [Operator.Operator("A"), Operator.Operator("B")]}
        self.callQueue = []
        self.activeCalls = {}
        self.callTimers = {}
        self.currentClient = None
    
    def handleCommand(self, command):
        """
        Processes incoming commands from the client.
        The command should be a dictionary containing the command type and ID.
        The command can be one of the following:
        - "call"
        - "answer"
        - "reject"
        - "hangup"
        """
        try:
            cmd = command.get("command")
            id = command.get("id")
            
            if cmd == "call":
                '''
                Receives a new call and assigns it to an operator if available. 
                If no operator is available, the call is added to the queue.
                Returns a list of messages indicating the call status.
                '''
                if id in self.activeCalls:
                    return f"Call {id} already exists"

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
                """
                Marks a call as answered by the operator if the operator is in a "ringing" state.
                Returns a message indicating the call was answered.
                """
                if not self.checkForValidId(id):
                    return f"Invalid id: {id}"

                operator = self.operators.get(id)
                self.disableTimeOut(operator)
                
                if operator and operator.state == "ringing":
                    call = operator.currentCall
                    call.answered = True
                    operator.state = "busy"
                    return f"Call {call.id} answered by operator {operator.id}"
            
            elif cmd == "reject":
                """
                Rejects a call assigned to an operator in the "ringing" state. 
                The call is either reassigned to another operator or added back to the queue.
                Returns a list of messages indicating the rejection and reassignment status.
                """
                if not self.checkForValidId(id):
                    return f"Invalid id: {id}"
                
                operator = self.operators.get(id)
                self.disableTimeOut(operator)

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
                """
                Ends a call and updates the operator's state to "available". 
                If the call was answered, it is marked as finished; otherwise, it is marked as missed.
                If there are calls in the queue, the next call is assigned to an operator.
                Returns a list of messages indicating the call's conclusion and any subsequent assignments.
                """
                if not self.checkForValidId(id):
                    return f"Invalid id: {id}"
                
                call = self.activeCalls.get(id)
                operator = call.assignedOperator
                self.disableTimeOut(operator)

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
                    assingment = self.assignCallToOperator(nextCall)
                    
                    if assingment:
                        response.append(assingment)

                del self.activeCalls[id]

                return response
        
        except Exception as e:
            return f"Error processing command"

    def assignCallToOperator(self, call):
        """
        Assigns a call to an available operator. 
        A timeout is scheduled to handle cases where the call is not answered within a specified duration.
        Returns a message indicating the call is ringing for a specific operator, 
        or None if no operators are available.
        """
        for operator in self.operators.values():
            if operator.state == "available":
                operator.state = "ringing"
                operator.currentCall = call
                call.assignedOperator = operator

                timeout = reactor.callLater(10, self.handleTimeOut, call.id, operator.id)
                self.callTimers[call.id] = timeout

                return f"Call {call.id} ringing for operator {operator.id}"
        
        return None
    
    def handleTimeOut(self, callId, operatorId):
        """
        Handles the timeout of a call by resetting the operator's state, 
        removing the call from active calls, and assigning the next call 
        in the queue if available.
        """
        call = self.activeCalls.get(callId)
        operator = self.operators.get(operatorId)

        operator.state = "available"
        operator.currentCall = None
        call.assignedOperator = None
        del self.activeCalls[callId]

        response = [f"Call {callId} ignored by operator {operatorId}"]

        # checks if there are calls in the queue
        nextCall = self.callQueue.pop(0) if self.callQueue else None
        
        if nextCall:
            self.assignCallToOperator(nextCall) 
            response.append(f"Call {nextCall.id} ringing for operator {nextCall.assignedOperator.id}")       
        
        self.currentClient.sendLine(json.dumps({"response": response}).encode('utf-8'))

    def checkForValidId(self, id):
        """
        Checks if the id is in any of the lists
        """
        if id not in self.activeCalls and id not in self.operators and id not in self.callQueue:
            return False
        return True
    
    def disableTimeOut(self, operator):
        """
        Cancels the timeout for the current call assigned to the given operator.
        Removes the timeout entry from the callTimers dictionary.
        """
        if operator.currentCall and operator.currentCall.id in self.callTimers:
            self.callTimers[operator.currentCall.id].cancel()
            del self.callTimers[operator.currentCall.id]


class QueueManagerProtocol(LineReceiver):
    """
    Protocol class for handling client connections and communication.
    This class is responsible for managing the connection lifecycle and
    processing incoming commands from the client.
    """
    def __init__(self, queueManager):
        """
        Initializes the QueueManager instance.
        """
        self.queueManager = queueManager
    
    def connectionMade(self):
        """
        Sets the current client in the QueueManager to this connection instance.
        """
        self.queueManager.currentClient = self
    
    def connectionLost(self, reason):
        """
        Handles the event when the connection to the client is lost.
        """
        self.queueManager.currentClient = None

    def lineReceived(self, line):
        """
        Called when a line of data is received from the client.
        Parses the incoming JSON command, processes it using the QueueManager,
        and sends back the response to the client.
        """
        command = json.loads(line)  # parse the incoming JSON command
        response = self.queueManager.handleCommand(command)  # process the command
        
        if response:
            # send the response back to the client as a JSON-encoded string
            self.sendLine(json.dumps({"response": response}).encode('utf-8'))

class QueueManagerFactory(Factory):
    """
    Factory class for creating instances of QueueManagerProtocol.
    This class is responsible for managing the lifecycle of protocol instances
    and sharing a single QueueManager instance across all connections.            
    """
    def __init__(self):
        """
        Initializes the factory with a new QueueManager instance.
        """
        self.queueManager = QueueManager()
    
    def buildProtocol(self, addr):
        """
        Creates and returns a new QueueManagerProtocol instance for a connection.
        """
        return QueueManagerProtocol(self.queueManager)

reactor.listenTCP(5678, QueueManagerFactory())
print("Call center server started on port 5678")
reactor.run()