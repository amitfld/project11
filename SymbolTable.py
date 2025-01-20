import typing

class SymbolTable:

    def __init__(self) -> None:
        """Creates a new symbol table."""
        self.class_table = {}
        self.subroutine_table = {}
        self.counters = {"FIELD": 0, "STATIC": 0, "ARG": 0, "VAR": 0}

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope"""
        self.subroutine_table = {}
        self.counters["VAR"] = 0
        self.counters["ARG"] = 0


    def define(self, name: str, type: str, kind: str) -> None:
        """
        Defines (adds to the table) a new variable of the given name, type, and kind.
        Assigns it the index value of that kind, and adds 1 to the index.
        """
        if kind in ["STATIC", "FIELD"]:
            self.class_table[name] = (kind, type, self.counters[kind])
            self.counters[kind] += 1
        elif kind in ["ARG", "VAR"]:
            self.subroutine_table[name] = (kind, type, self.counters[kind])
            self.counters[kind] += 1
        else:
            raise ValueError(f"Unknown type {type}")

    def var_count(self, kind: str) -> int:
        """Returns the number of variables of the given kind already defined in the table."""
        return self.counters[kind]

    def kind_of(self, name: str):
        """Returns the kind of the named identifier. If the identifier is not found, returns NONE."""
        if name in self.subroutine_table:
            return self.subroutine_table[name][0]
        elif name in self.class_table:
            return self.class_table[name][0]
        else:
            return None

    def type_of(self, name: str) -> str:
        """Returns the type of the named variable."""
        if name in self.subroutine_table:
            return self.subroutine_table[name][1]
        elif name in self.class_table:
            return self.class_table[name][1]
        else:
            raise ValueError(f"Unknown symbol {name}")

    def index_of(self, name: str) -> int:
        """Returns the index of the named variable."""
        if name in self.subroutine_table:
            return self.subroutine_table[name][2]
        elif name in self.class_table:
            return self.class_table[name][2]
        else:
            raise ValueError(f"Unknown symbol {name}")

    def get_local_variable_count(self):
        return self.counters["VAR"]

    def get_field_variable_count(self):
        return self.counters["FIELD"]
