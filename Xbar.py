import re
import copy

Parameters = {
    "head parameter": "head-first",
    "spec parameter": "spec-first",
}


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


class XP(Tree):
    def __init__(self, category, head, specifier=None, complements=None, adjuncts=None):
        self.category = category
        comp = [complements] if type(complements) != list and complements else complements
        adju = [adjuncts] if type(adjuncts) != list and adjuncts else adjuncts
        xbar = Tree(category, [head])
        if comp:
            for c in comp:
                xbar = Tree(category + "c'", [xbar, c])
        if adju:
            for a in adju:
                if isinstance(a, str) and len(a.split(" ")) == 1:
                    xbar = Tree(category + "a'", [a, xbar]) 
                else:
                    xbar = Tree(category + "a'", [xbar, a])
        super().__init__(category + "P", [specifier, xbar])

    def head(self):
        xbar = self.children[1]

        while isinstance(xbar, Tree) and any([child.label.endswith("'") if isinstance(child, Tree) else child.endswith("'") for child in xbar.children]):
            if isinstance(xbar.children[0], Tree):
                bar = xbar.children[0].label.endswith("'")
            else:
                bar = xbar.children[0].endswith("'")
            xbar = xbar.children[0] if bar else xbar.children[1]
        return xbar.children[0]

    def spec(self):
        return self.children[0]

    def comp(self):
        comp = []
        xbar = [t for t in self.subtrees() if t.label.endswith("c'")][0]
        while isinstance(xbar, Tree) and any([child.label.endswith("c'") if isinstance(child, Tree) else child.endswith("c'") for child in xbar.children]):
            if isinstance(xbar.children[0], Tree):
                bar = xbar.children[0].label.endswith("'")
            else:
                bar = xbar.children[0].endswith("'")
            comp.append(xbar.children[1] if bar else xbar.children[0])
            xbar = xbar.children[0] if bar else xbar.children[1]
        comp.append(xbar.children[1])
        return comp


    def adju(self):
        adju = []
        xbar = [t for t in self.subtrees() if t.label.endswith("a'")][0]
        while isinstance(xbar, Tree) and any([child.label.endswith("a'") if isinstance(child, Tree) else child.endswith("a'") for child in xbar.children]):
            if isinstance(xbar.children[0], Tree):
                bar = xbar.children[0].label.endswith("'")
            else:
                bar = xbar.children[0].endswith("'")
            adju.append(xbar.children[1] if bar else xbar.children[0])
            xbar = xbar.children[0] if bar else xbar.children[1]
        adju.append(xbar.children[1])
        return adju

    def terminals(self):
        terminals = super().terminals()
        new_terminals = []
        for item in terminals:
            if isinstance(item, list):
                new_terminals.extend(item)
            else:
                new_terminals.append(item)
        return new_terminals

    def __eq__(self, other):
        if issubclass(type(other), XP):
            return all([
                self.category == other.category,
                self.spec == other.spec,
                self.head == other.head,
                self.comp == other.comp,
                self.adju == other.adju,
            ])
        else:
            return False

    def words(self):
        return [element for element in self.terminals() if element not in ["AGR", "C", "T", "e", "t", None] and not re.fullmatch("\[.*\]", element)]

    def __str__(self):
        return f"{self.category}P: {' '.join([str(element) for element in self.terminals()])}"

    def __repr__(self):
        return f"<{str(self)}>"

a = XP("X", head="son", specifier="the", complements="of Morwen", adjuncts=["stern", "who wore the dragon-helm", "and who defeated Glaurung"])

'''
print(a)
a.draw()
print(a.children)
print(a.terminals())
print(a.words())
'''


class NP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("N", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)


class VP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("V", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)


class AP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("A", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)


class PP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("P", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)


class IP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("I", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)


class CP(XP):
    def __init__(self, head, complements=None, specifier=None, adjuncts=None):
        super().__init__("C", head=head, complements=complements, specifier=specifier, adjuncts=adjuncts)

    def move(self, question=False):
        surface = copy.deepcopy(self)

        if question:
            if [t for t in self.subtrees() if isinstance(t, VP)][-1].children[1].children[0] in ["be", "have"]:
                alpha = [t for t in self.subtrees() if isinstance(t, VP)][-1].children[1].children[0]
                surface.children[0] = alpha
                [t for t in surface.subtrees() if isinstance(t, VP)][-1].children[1].children[0] = ""
            else:
                alpha = "do"
                surface.children[0] = alpha
        '''

        passive_morphology = not [t for t in self.subtrees() if isinstance(t, VP)][-1].spec.head

        if passive_morphology:
            alpha = [t for t in surface.subtrees() if isinstance(t, VP)][-1].comp[0]
            [t for t in surface.subtrees() if isinstance(t, AGRP) and [t for t in surface.subtrees() if isinstance(t, VP)][-1] in surface.subtrees()][-1].spec = alpha
            [t for t in surface.subtrees() if isinstance(t, VP)][-1].comp[0] = NP("t")
            [t for t in surface.subtrees() if isinstance(t, VP)][-1].head = "be " + [t for t in surface.subtrees() if isinstance(t, VP)][-1].head + "ed"
        else:
            # Subject-movement
            # The specifier NP of the 'deepest' verb phrase

            subj = [t for t in surface.subtrees() if isinstance(t, VP)][-1].spec
            # Becomes the specifier of the enclosing AGRP
            [t for t in surface.subtrees() if isinstance(t, AGRP)][-1].spec = subj
            [t for t in surface.subtrees() if isinstance(t, VP)][-1].spec = "t"


        # Verb-movement
        # The head verb of the 'deepest' verb phrase

        verb = [t for t in surface.subtrees() if isinstance(t, VP)][-1].head
        print(verb)
        # Acquire agreement from AGR
        print([t for t in surface.subtrees() if isinstance(t, AGRP)][-1].head)
        agreement = [t for t in surface.subtrees() if isinstance(t, AGRP)][-1].head
        [t for t in surface.subtrees() if isinstance(t, AGRP)][-1].head = verb + " " + ("-s" if agreement == "[SINGULAR]" else "")
        [t for t in surface.subtrees() if isinstance(t, VP)][-1].head = "t"
        '''

        return surface


class AGRP(XP):
    def __init__(self, head, specifier=None, complements=None, adjuncts=None):
        super().__init__("AGRP", head=head, specifier=specifier, complements=complements, adjuncts=adjuncts)


class AGRSP(AGRP):
    def __init__(self, head, specifier=None, complements=None, adjuncts=None):
        super().__init__("AGRSP", head=head, specifier=specifier, complements=complements, adjuncts=adjuncts)


class AGROP(AGRP):
    def __init__(self, head, specifier=None, complements=None, adjuncts=None):
        super().__init__("AGROP", head=head, specifier=specifier, complements=complements, adjuncts=adjuncts)


class TP(XP):
    def __init__(self, head, specifier=None, complements=None, adjuncts=None):
        super().__init__("TP", head=head, specifier=specifier, complements=complements, adjuncts=adjuncts)

a = XP("NP", "the dragon's", "defeat", adjuncts="at the ford")
b = XP("PP", head="of", complements=a)
c = XP("NP", head="news", complements=b)
d = XP("VP", c, "spread", complements=["across the land", "like wildfire"])

# print(d)


class clause(CP):
    def __init__(self, vp):
        super().__init__(
            "C",
            complements=AGRP(
                "AGR",
                specifier="e",
                complements=TP(
                    "T",
                    complements=vp
                )
            )
        )


a = NP(head="son", specifier="the", complements="of Morwen", adjuncts=["stern", "in the dragon-helm", "who slew Glaurung"])
c = PP(head="onto", complements=NP(head="sword", specifier="his"))
b = VP(head="threw", specifier=a, complements=["himself", c])
d = VP(head="grieved", specifier="he", complements=PP(head="for", complements=NP(head="sister", specifier="his", adjuncts="dead")))
e = AP(head="sad", complements=TP(head="to", complements=VP(head="see", complements=TP(head="", complements=VP(head="go", specifier="you")))))

f = CP("", complements=AGRP("", complements=TP("", complements=VP("play", complements=NP("football"), specifier=NP("you")))))
g = CP("", complements=AGRP("", complements=TP("", complements=VP("like", complements=NP("music") , specifier=NP("we")))))

a = VP("gave", specifier=NP("he"), complements=[NP("me"), NP("the gift")], adjuncts=[PP("on Tuesday"), "happily"])

print(a)
print(a.json())

print(a.head())
print(a.spec())
print(a.comp())
print(a.adju())

e = PP(
    head="in",
    complements=NP(
        specifier="a",
        head=AP(
            head="distant and second-hand",
            complements=NP(
                head="set",
                complements=PP(
                    head="of",
                    complements="dimensions"
                )
            )
        )
    )
)

f = PP(
    head="in",
    complements=NP(
        specifier="an",
        head="astral plane",
        adjuncts=CP(
            head="that",
            complements="was never meant to fly"
        )
    )
)

g = VP(
    specifier=NP(
        specifier="the",
        adjuncts="curling",
        head="star-mists",
    ),
    head="waver and part"
)

h = XP(
    "XP",
    head="",
    complements=XP(
        "XP",
        head="",
        complements=VP(
            specifier="the plant",
            head="was",
            complements="where"
        )
    )
)

i = XP(
    "XP",
    head="",
    complements=XP(
        "XP",
        head="",
        complements=VP(
            specifier=NP(
                "land",
                specifier="the",
                adjuncts=PP(
                    "of",
                    complements=AP(
                        "seven",
                        complements=NP(
                            "rivers"
                        )
                    )
                )
            ),
            head="is",
            complements="where"
        )
    )
)

# print(" ".join(i.elements()).capitalize() + "?")


j = VP(
    "were defeated",
    "e",
    "the Normans"
)

k = CP(
    head="",
    complements=AGRP(
        specifier=NP("e"),
        head="[Singular]",
        complements=TP(
            head="[Past]",
            complements=VP(
                "defeat",
                NP("e"),
                NP("Glaurung")
            )
        )
    )
)


x = clause(j)


y = CP(
    head="",
    complements=AGRP(
        specifier=NP("e"),
        head="[Singular]",
        complements=TP(
            head="[Past]",
            complements=VP(
                "win",
                specifier=NP("e"),
                complements=NP("the battle"),
                adjuncts=PP(
                    "by",
                    complements="the Normans"
                )
            )
        )
    )
)

z = CP(
    "",
    complements=AGRP(
        "[Singular]",
        specifier=NP("e"),
        complements=TP(
            head="[Past]",
            complements=VP(
                "was said",
                specifier=NP("e"),
                complements=CP(
                    "",
                    complements=AGRP(
                        "to",
                        specifier=NP("e"),
                        complements=TP(
                            "[Past]",
                            complements=VP(
                                "be lost",
                                specifier=NP("e"),
                                complements=NP("the book")
                            )
                        )
                    )
                )
            )
        )
    )
)

z2 = CP(
    "",
    complements=AGRP(
        "[Singular]",
        specifier=NP("e"),
        complements=TP(
            head="[Past]",
            complements=VP(
                "was thought",
                specifier=NP("e"),
                complements=CP(
                    "",
                    complements=AGRP(
                        "to",
                        specifier=NP("e"),
                        complements=TP(
                            "[Past]",
                            complements=VP(
                                "have been killed",
                                specifier=NP("e"),
                                complements=NP("the king")
                            )
                        )
                    )
                )
            )
        )
    )
)


z = CP(
    "C",
    None,
    AGRP(
        "[SINGULAR]",
        None,
        TP(
            "will",
            None,
            VP(
                "crush",
                NP(None),
                NP(
                    "enemy",
                    "the")
            )
        )
    )
)

# print(z.words())

# print(z.move().words())

'''
a = Tree("Sentence", ["Subject", "Predicate"])
b = Tree("Predicate", [Tree("Verb", ["chases"]), Tree("Object", [Tree("D", ["the"]), Tree("N", ["fox"])])])
c = Tree("Subject", [Tree("D", ["The"]), Tree("N", ["dog"])])
a.children[1] = b
a.children[0] = c


print(b.sisterhood(c))
print(b.dominates("Object"))
print(b.c_commands("Object"))
print(b.governs(c))

print(a)
'''