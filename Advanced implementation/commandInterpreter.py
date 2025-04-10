from twisted.internet import reactor, protocol, stdio
from twisted.protocols.basic import LineReceiver
import json
import cmd

class CallCenterClientProtocol(LineReceiver):
    def __init__(self, app):
        self.app = app
    
    def connectionMade(self):
        self.app.setProtocol(self)
    
    def lineReceived(self, data):
        response = json.loads(data)

        if response:
            print(response)
        else:
            print("No response received.")

class CallCenterClientFactory(protocol.ClientFactory):
    protocol = CallCenterClientProtocol

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, addr):
        return CallCenterClientProtocol(self.app)

class CallCenterHandleInput(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.protocol = None
    
    def setProtocol(self, protocol):
        self.protocol = protocol
    
    def sendCommand(self, command, id):
        if self.protocol:  
            data = json.dumps({"command": command, "id": id})
            self.protocol.sendLine(data.encode())
        else:
            print("Not connected to server.")
    
    def do_call(self, id):
        self.sendCommand("call", id)
    
    def do_answer(self, id):
        self.sendCommand("answer", id)
    
    def do_reject(self, id):
        self.sendCommand("reject", id)

    def do_hangup(self, id):
        self.sendCommand("hangup", id)

class StdinInput(LineReceiver):
    delimiter = b'\n'

    def __init__(self, interpreter):
        self.interpreter = interpreter

    def connectionMade(self):
        self.transport.write(self.interpreter.prompt.encode())

    def lineReceived(self, line):
        if isinstance(line, bytes):
            line = line.decode()

        if self.interpreter.onecmd(line):
            self.transport.loseConnection()
        else:
            self.transport.write(self.interpreter.prompt.encode())


if __name__ == "__main__":
    interpreter = CallCenterHandleInput()
    interpreter.setProtocol(5678)
    stdio.StandardIO(StdinInput(interpreter))
    reactor.connectTCP("localhost", 5678, CallCenterClientFactory(interpreter))
    reactor.run()
