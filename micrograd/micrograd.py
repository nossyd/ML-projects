class Value:
    def __init__(self, data):
        self.data = data
        # self.children = set()

    def __repr__(self):
        return(f"Value = {self.data}")

    def __add__(self, other):
        return Value(self.data + other.data)
    
    def __mul__(self, other):
        return Value(self.data * other.data)
