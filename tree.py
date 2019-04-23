class Tree:

    def __init__(self, label, children):
        self.label = label
        self.children = children if isinstance(children, list) else [children]

    def json(self):
        string = self.label + " {\n"
        for child in self.children:
            if isinstance(child, Tree):
                string += "\n".join(["\t" + line for line in (child).json().split("\n")]) + "\n"
            elif child:
                string += f"\t{child}\n"
        string += "}"
        return string

    def draw(self):
        print(self.json())

    def __str__(self):
        return f"{self.label}: ({', '.join([str(child) for child in self.children])})"

    def __repr__(self):
        return f"{self.label}: ({', '.join([repr(child) for child in self.children])})"

    def terminals(self):
        terminals = []
        for child in self.children:
            if isinstance(child, Tree):
                terminals.extend(child.terminals())
            elif child:
                terminals.append(child)
        return terminals

    def subtrees(self):
        subtrees = []
        for child in self.children:
            if isinstance(child, Tree):
                subtrees.append(child)
                subtrees.extend(child.subtrees())
        return subtrees

    def parent(self):
        for t in [t for t in globals().values() if isinstance(t, Tree)]:
            if self in t.children:
                return t
        return None

    def sisters(self):
        if self.parent():
            return [t for t in self.parent().children if t is not self]
        else:
            return None

    def dominates(self, other, immediately=False):
        if immediately:
            return other in self.children
        else:
            return other in self.subtrees() + self.terminals()

    def c_commands(self, other):
        if self.parent():
            domain = self.parent().subtrees() + self.parent().terminals()
            return other in domain and not self.dominates(other)
        else:
            return False

    def c_command_domain(self):
        if self.parent():
            return self.parent().subtrees() + self.parent().terminals()
        else:
            return []

    def government_domain(self):
        return [t for t in self.c_command_domain() if isinstance(t, Tree) and self in t.c_command_domain()]

    def governs(self, other):
        return self.c_commands(other) and other.c_commands(self)

    def sisterhood(self, other):
        return self.parent() is other.parent()