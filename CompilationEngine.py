import typing

import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter

OP = ['+', '-', '*', '/', '&', '|', '<', '>', '=']

OP_VM = {'+': "add", '-': "sub", "&amp;": "and", '|': "or",
         "&lt;": "lt", "&gt;": "gt", '=': "eq"}

UNARY_OP = {'~': "not", '-': "neg", '#': "shiftright", '^': "shiftleft"}

KIND = {
    "static": "static",
    "field": "this",
    "arg": "argument",
    "var": "local"}


class CompilationEngine:

    def __init__(self, input_stream: "JackTokenizer", output_stream: typing.TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        """
        self.curr_subroutine_type = None
        self.subroutine_name = None
        self.field_counter = None
        self.jack_tokenizer = input_stream
        self.vm_writer = VMWriter(output_stream)
        self.symbol_table = SymbolTable()
        self.label_if_counter = 0
        self.label_while_counter = 0
        self.class_name = ""

    def compile_class(self) -> None:
        """Compiles a complete class."""
        self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()
        self.class_name = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()
        while True:
            if self.jack_tokenizer.get_token() == '}':
                break
            match self.jack_tokenizer.keyword():
                case "FIELD":
                    self.compile_class_var_dec()
                case "STATIC":
                    self.compile_class_var_dec()
                case "CONSTRUCTOR" | "METHOD" | "FUNCTION":
                    self.compile_subroutine()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        kind = self.jack_tokenizer.keyword()
        self.jack_tokenizer.advance()
        type = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        name = self.jack_tokenizer.get_token()
        self.symbol_table.define(name, type, kind)
        self.jack_tokenizer.advance()
        while self.jack_tokenizer.get_token() != ';':
            self.jack_tokenizer.advance()
            name = self.jack_tokenizer.get_token()
            self.symbol_table.define(name, type, kind)
            self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()

    def compile_subroutine(self):
        """Compiles a function name."""
        self.symbol_table.start_subroutine()
        self.curr_subroutine_type = self.jack_tokenizer.keyword()
        self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()
        self.subroutine_name = self.class_name + "." + self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        self.compile_parameter_list()
        self.jack_tokenizer.advance()
        while self.jack_tokenizer.keyword() == "VAR":
            self.compile_class_var_dec()

        self.vm_writer.write_function(self.subroutine_name, self.symbol_table.get_local_variable_count())

        if self.curr_subroutine_type == "METHOD":
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        if self.curr_subroutine_type == "CONSTRUCTOR":
            self.vm_writer.write_push("constant", self.symbol_table.get_field_variable_count())
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)

        while self.jack_tokenizer.get_token() != '}':
            self.compile_statements()

        self.jack_tokenizer.advance()

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list. Does not handle the enclosing parentheses tokens ( and )."""
        if self.curr_subroutine_type == "METHOD":
            self.symbol_table.define("this", "Array", "ARG")
        self.jack_tokenizer.advance()
        while self.jack_tokenizer.get_token() != ')':
            type = self.jack_tokenizer.get_token()
            self.jack_tokenizer.advance()
            name = self.jack_tokenizer.get_token()
            self.symbol_table.define(name, type, "ARG")
            self.jack_tokenizer.advance()
            if self.jack_tokenizer.get_token() != ')':
                self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        pass

    def compile_statements(self):
        """Compiles a sequence of statements. Does not handle the enclosing curly bracket tokens { and }."""
        while True:
            token_type = self.jack_tokenizer.token_type()
            if self.jack_tokenizer.get_token() == '}':
                break
            if token_type == "KEYWORD":
                self.vm_writer.write_to_file(f"// {self.jack_tokenizer.get_token()} {self.jack_tokenizer.next_token()}")
                match self.jack_tokenizer.keyword():
                    case "LET":
                        self.compile_let()
                    case "IF":
                        self.compile_if()
                    case "WHILE":
                        self.compile_while()
                    case "DO":
                        self.compile_do()
                    case "RETURN":
                        self.compile_return()

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.jack_tokenizer.advance()
        if self.jack_tokenizer.get_token() == ';':
            self.vm_writer.write_push("constant", 0)
        else:
            self.compile_expression()
        self.vm_writer.write_return()
        self.jack_tokenizer.advance()

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.jack_tokenizer.advance()
        var_name = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        kind = self.symbol_table.kind_of(var_name)
        index = self.symbol_table.index_of(var_name)
        if self.jack_tokenizer.get_token() == '[':
            self.jack_tokenizer.advance()
            self.compile_expression()
            self.vm_writer.write_push(KIND[kind.lower()], index)
            self.vm_writer.write_arithmetic("add")
            self.jack_tokenizer.advance()
            self.jack_tokenizer.advance()
            self.compile_expression()
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)
        elif self.jack_tokenizer.get_token() == '=':
            self.jack_tokenizer.advance()
            self.compile_expression()
            self.vm_writer.write_pop(KIND[kind.lower()], index)
        self.jack_tokenizer.advance()

    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.jack_tokenizer.advance()
        self.compile_expression()
        self.vm_writer.write_pop("temp", 0)
        self.jack_tokenizer.advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.label_while_counter += 1
        self.vm_writer.write_label("L" + str(self.label_while_counter))
        self.jack_tokenizer.advance()
        self.compile_expression()
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if("L" + str(self.label_while_counter + 1))
        self.jack_tokenizer.advance()
        self.compile_statements()
        self.vm_writer.write_goto("L" + str(self.label_while_counter))
        self.label_while_counter += 1
        self.vm_writer.write_label("L" + str(self.label_while_counter))
        self.jack_tokenizer.advance()

    def compile_if(self) -> None:
        """Compiles an if statement, possibly with a trailing else clause."""
        self.jack_tokenizer.advance()
        self.compile_expression()
        self.label_if_counter += 1
        label_true = 'TrueIf' + str(self.label_if_counter)
        label_false = 'FalseIf' + str(self.label_if_counter)
        label_end = 'EndIf' + str(self.label_if_counter)
        self.vm_writer.write_if(label_true)
        self.vm_writer.write_goto(label_false)
        self.vm_writer.write_label(label_true)
        self.jack_tokenizer.advance()
        self.compile_statements()
        self.vm_writer.write_goto(label_end)
        self.jack_tokenizer.advance()
        self.vm_writer.write_label(label_false)
        if self.jack_tokenizer.get_token().lower() == 'else':
            self.jack_tokenizer.advance()
            self.jack_tokenizer.advance()
            self.compile_statements()
            self.jack_tokenizer.advance()
        self.vm_writer.write_label(label_end)

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        while self.jack_tokenizer.get_token() in OP:
            op = self.jack_tokenizer.symbol()

            self.jack_tokenizer.advance()
            self.compile_term()
            match op:
                case "*":
                    self.vm_writer.write_call("Math.multiply", 2)
                case "/":
                    self.vm_writer.write_call("Math.divide", 2)
                case _:
                    self.vm_writer.write_arithmetic(OP_VM[op])

    def compile_term(self) -> None:
        """
        Compiles a term. If the current token is an identifier, the routine must resolve it into a variable,
        array entry, or subroutine call. A single lookahead token, which may be [, (, or ., suffices to distinguish
        between the possibilities. Any other token is not part of this term and should not be advanced over.
        """
        token_type = self.jack_tokenizer.token_type()
        if token_type in ["INT_CONST", "STRING_CONST", "KEYWORD"]:
            self.simple_term(token_type)
        elif token_type in ["SYMBOL"]:
            cur_symbol = self.jack_tokenizer.symbol()
            self.expression_or_unary(cur_symbol)
        else:
            identifier = self.jack_tokenizer.identifier()
            self.jack_tokenizer.advance()
            current_token = self.jack_tokenizer.get_token()
            match current_token:
                case "(" | ".":
                    self.call_subroutine(current_token, identifier)

                case "[":
                    self.array_term(identifier)
                case _:
                    self.push_identifier(identifier)

    def expression_or_unary(self, cur_symbol):
        match cur_symbol:
            case "(":
                self.jack_tokenizer.advance()
                self.compile_expression()
                self.jack_tokenizer.advance()
            case "-" | "~" | "#" | "^":
                self.jack_tokenizer.advance()
                self.compile_term()
                self.vm_writer.write_arithmetic(UNARY_OP[cur_symbol])

    def array_term(self, identifier):
        self.jack_tokenizer.advance()
        self.compile_expression()
        self.jack_tokenizer.advance()
        self.push_identifier(identifier)
        self.vm_writer.write_arithmetic("add")
        self.vm_writer.write_pop("pointer", 1)
        self.vm_writer.write_push("that", 0)

    def simple_term(self, token_type):
        match token_type:
            case "INT_CONST":
                self.vm_writer.write_push("constant", self.jack_tokenizer.int_val())
            case "STRING_CONST":
                str_token = self.jack_tokenizer.string_val()
                self.vm_writer.write_push("constant", len(str_token))
                self.vm_writer.write_call("String.new", 1)
                for i in range(len(str_token)):
                    self.vm_writer.write_push("constant", ord(str_token[i]))
                    self.vm_writer.write_call("String.appendChar", 2)
            case "KEYWORD":
                token = self.jack_tokenizer.keyword()
                match token:
                    case "FALSE" | "NULL":
                        self.vm_writer.write_push("constant", 0)
                    case "TRUE":
                        self.vm_writer.write_push("constant", 1)
                        self.vm_writer.write_arithmetic("neg")
                    case "THIS":
                        self.vm_writer.write_push("pointer", 0)
        self.jack_tokenizer.advance()

    def push_identifier(self, identifier):
        kind = self.symbol_table.kind_of(identifier)
        index = self.symbol_table.index_of(identifier)
        self.vm_writer.write_push(KIND[kind.lower()], index)

    def call_subroutine(self, current_token, identifier):
        num_args = 0
        if current_token == "(":
            func_name = self.class_name + "." + identifier
            num_args += 1
            self.vm_writer.write_push("pointer", 0)
        else:
            self.jack_tokenizer.advance()
            identifier2 = self.jack_tokenizer.identifier()
            kind = self.symbol_table.kind_of(identifier)
            if kind is None:
                func_name = identifier + "." + identifier2
            else:
                func_name = self.symbol_table.type_of(identifier) + "." + identifier2
                index = self.symbol_table.index_of(identifier)
                self.vm_writer.write_push(KIND[kind.lower()], index)
                num_args += 1
            self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()
        num_args += self.compile_expression_list()
        self.jack_tokenizer.advance()
        self.vm_writer.write_call(func_name, num_args)

    def compile_expression_list(self) -> int:
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        Returns the number of expressions in the list.
        """
        args_num = 0
        if self.jack_tokenizer.get_token() != ')':
            args_num += 1
            self.compile_expression()
        while True:
            if self.jack_tokenizer.get_token() == ')':
                break

            if self.jack_tokenizer.get_token() == ',':
                args_num += 1
                self.jack_tokenizer.advance()
                self.compile_expression()

        return args_num

