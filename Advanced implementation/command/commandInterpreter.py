from twisted.internet import reactor, protocol, stdio
from twisted.protocols.basic import LineReceiver
import json
import cmd

class CallCenterHandleInput(cmd.Cmd):
    """
    CallCenterHandleInput is a command-line interpreter class for handling call center operations.
    This class extends `cmd.Cmd` and provides a set of commands to interact with a call center protocol.
    It allows sending commands such as `call`, `answer`, `reject`, and `hangup` to a server via a protocol.
    """
    def __init__(self):
        super().__init__()
        self.protocol = None
        self.prompt = '> '
    
    def setProtocol(self, protocol):
        """
        Sets the communication protocol for sending commands.
        """
        self.protocol = protocol
    
    def sendCommand(self, command, id):
        """
        Sends a command to the server using the established protocol.
        """
        if self.protocol:  
            data = json.dumps({"command": command, "id": id})
            self.protocol.sendLine(data.encode())
        else:
            print("Not connected to server.")
    
    """
    Command methods for handling call center operations.
    """
    def do_call(self, id):
        self.sendCommand("call", id)
    
    def do_answer(self, id):
        self.sendCommand("answer", id)
    
    def do_reject(self, id):
        self.sendCommand("reject", id)

    def do_hangup(self, id):
        self.sendCommand("hangup", id)

    def do_exit(self, line):
        print("Exiting...")
        reactor.stop()
        return True

class StdinInput(LineReceiver):
    """
    A class that handles standard input commands using the Twisted framework's LineReceiver.
    """
    delimiter = b'\n'

    def __init__(self, interpreter):
        """
        Initializes the StdinInput instance with a reference to the command-line interpreter.
        This allows the StdinInput class to delegate command processing to the interpreter.
        """
        self.interpreter = interpreter

    def connectionMade(self):
        """
        Called when the connection to the standard input is established.
        Sends the command prompt to the user to indicate readiness for input.
        """
        self.transport.write(self.interpreter.prompt.encode())

    def lineReceived(self, line):
        """
        Handles a line of input received from the standard input.
        Decodes the input if it is in bytes, processes the command using the interpreter,
        and determines whether to close the connection or prompt for the next command.
        """
        if isinstance(line, bytes):
            line = line.decode()  # Decode bytes to string if necessary

        if self.interpreter.onecmd(line):  # Process the command
            self.transport.loseConnection()  # Close the connection if the command signals to exit
        else:
            self.transport.write(self.interpreter.prompt.encode())  # Prompt for the next command

class CallCenterClientProtocol(LineReceiver):
    """
    A protocol class for handling communication with the call center server.
    This class extends `LineReceiver` to process incoming and outgoing messages.
    """
    def __init__(self, app):
        """
        Initializes the protocol with a reference to the application.
        """
        self.app = app
    
    def connectionMade(self):
        """
        Sets the protocol in the application to enable communication.
        """
        self.app.setProtocol(self)
    
    def lineReceived(self, data):
        """
        Called when a line of data is received from the server.
        Decodes the data, processes the response, and displays it to the user.
        """
        response = json.loads(data)  # Parse the JSON response
        print()  # Print a blank line for better readability
        
        if "response" in response:
            resp = response["response"]
            
            if isinstance(resp, list):  # If the response is a list, print each item
                for msg in resp:
                    print(msg)
            else:  # Otherwise, print the single response
                print(resp)
            
            # Display the command prompt again
            print(self.app.prompt, end='', flush=True)
        
        else:
            print("No response received.")  # Handle cases where no response is provided

class CallCenterClientFactory(protocol.ClientFactory):
    """
    A factory class for creating instances of the CallCenterClientProtocol.
    This class is responsible for managing the lifecycle of the protocol objects
    and associating them with the application.
    """
    def __init__(self, app):
        """
        Initializes the factory with a reference to the application.
        """
        self.app = app

    def buildProtocol(self, addr):
        """
        Creates and returns an instance of CallCenterClientProtocol.
        Associates the protocol instance with the application.
        """
        return CallCenterClientProtocol(self.app)
    
if __name__ == "__main__":
    try:
        interpreter = CallCenterHandleInput()
        stdio.StandardIO(StdinInput(interpreter))
        factory = CallCenterClientFactory(interpreter)
        # reactor.connectTCP("host.docker.internal", 5678, factory)
        reactor.connectTCP("localhost", 5678, factory)
        reactor.run()
    
    except Exception as e:
        print(f"Error: {e}")
        reactor.stop()