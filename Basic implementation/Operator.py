class Operator:
    def __init__(self, operatorId):
        self.id = operatorId
        self.state = "avaliable"
        self.currentCall = None