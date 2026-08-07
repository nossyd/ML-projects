class Value:
    def __init__(self, data, _children=(), op=''):
        self.data = data
        self._prev = set(_children)
        self.op = op

    def __repr__(self):
        return(f"Value = {self.data}")

    def __add__(self, other):
        return Value(self.data + other.data, (self, other), '+')
    
    def __mul__(self, other):
        return Value(self.data * other.data, (self, other), '*')
