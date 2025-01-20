import typing

import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter

OP = ['+', '-', '*', '/', '&', '|', '<', '>', '=']

OP_VM = {'+': "add", '-': "sub", "&amp;": "and", '|': "or",
         "&lt;": "lt", "&gt;": "gt", '=': "eq"}

UNARY_OP = {'~': "not", '-': "neg"}

KIND = {
    "static": "static",
    "field": "this",
    "arg": "argument",
    "var": "local"}


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer", output_stream: typing.TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.current_subroutine_type = None
        self.subroutine_name = None
        self.field_counter = None
        self.jack_tokenizer = input_stream
        self.vm_writer = VMWriter(output_stream)
        self.symbol_table = SymbolTable()
        self.label_counter = 0
        self.class_name = ""

    def compile_class(self) -> None:
        """Compiles a complete class."""
        self.jack_tokenizer.advance()
        # token = class
        self.jack_tokenizer.advance()
        # token = className
        self.class_name = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        # token = (
        self.jack_tokenizer.advance()
        # token = {

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
        # token = field | static
        var_kind = self.jack_tokenizer.keyword()
        self.jack_tokenizer.advance()
        # token = int | String | Array ...
        var_type = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()
        # token = varName
        var_name = self.jack_tokenizer.get_token()
        self.symbol_table.define(var_name, var_type, var_kind)
        self.jack_tokenizer.advance()

        # token = ; | ,
        while self.jack_tokenizer.get_token() != ';':
            self.jack_tokenizer.advance()
            # token = varName
            var_name = self.jack_tokenizer.get_token()
            self.symbol_table.define(var_name, var_type, var_kind)
            self.jack_tokenizer.advance()
            # token = ; | ,
        self.jack_tokenizer.advance()


    def compile_subroutine(self):
        """Compiles a function name."""
        self.symbol_table.start_subroutine()
        # token = method
        self.current_subroutine_type = self.jack_tokenizer.keyword()

        self.jack_tokenizer.advance()
        # token = (return_type)
        self.jack_tokenizer.advance()
        # token = methodName
        self.subroutine_name = self.class_name + "." + self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()

        #if subroutine_type == "METHOD":
            #self.symbol_table.define("this", "", "ARG")
            #self.jack_tokenizer.advance()

        # token = (
        self.compile_parameter_list()
        # token = {
        self.jack_tokenizer.advance()

        while self.jack_tokenizer.keyword() == "VAR":
            self.compile_class_var_dec()

        self.vm_writer.write_function(self.subroutine_name, self.symbol_table.get_scope_vars())  # function xxx.yyy n

        if self.current_subroutine_type == "METHOD":
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)

        if self.current_subroutine_type == "CONSTRUCTOR":
            self.vm_writer.write_push("constant", self.symbol_table.get_fields_num())
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)

        while self.jack_tokenizer.get_token() != '}':
            self.compile_statements()

        self.jack_tokenizer.advance()


    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the
        enclosing "()".
        """
        if self.current_subroutine_type == "METHOD":
            self.symbol_table.define("this", "Array", "ARG")

        # token = [_](
        self.jack_tokenizer.advance()
        while self.jack_tokenizer.get_token() != ')':
            # token = (type)
            arg_type = self.jack_tokenizer.get_token()
            self.jack_tokenizer.advance()
            # token = (varName)
            arg_name = self.jack_tokenizer.get_token()
            self.symbol_table.define(arg_name, arg_type, "ARG")
            self.jack_tokenizer.advance()
            # token = (,)
            if self.jack_tokenizer.get_token() != ')':
                self.jack_tokenizer.advance()
        self.jack_tokenizer.advance()
        # token = ({)

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        pass

    def compile_statements(self):
        """Compiles a sequence of statements, not including the enclosing
        "{}".
        """
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
        # token = (return)
        self.jack_tokenizer.advance()
        if self.jack_tokenizer.get_token() == ';':
            self.vm_writer.write_push("constant", 0)
        else:
            self.compile_expression()
        self.vm_writer.write_return()
        self.jack_tokenizer.advance()
        # token = (;)

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # WE SKIP THE "LET" KEYWORD
        self.jack_tokenizer.advance()

        var_name = self.jack_tokenizer.get_token()
        self.jack_tokenizer.advance()

        kind = self.symbol_table.kind_of(var_name)
        index = self.symbol_table.index_of(var_name)

        if self.jack_tokenizer.get_token() == '[':

            self.jack_tokenizer.advance()  # opening square bracket [

            # and now, deal with expression
            self.compile_expression()
            self.vm_writer.write_push(KIND[kind.lower()], index)
            self.vm_writer.write_arithmetic("add")
            self.jack_tokenizer.advance()  # closing square bracket ]

            self.jack_tokenizer.advance()  # equals sign =
            self.compile_expression()
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)

        elif self.jack_tokenizer.get_token() == '=':
            self.jack_tokenizer.advance()  # equals sign =
            self.compile_expression()
            self.vm_writer.write_pop(KIND[kind.lower()], index)

        self.jack_tokenizer.advance()

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # token = (do)
        self.jack_tokenizer.advance()
        # token = (expression)
        self.compile_expression()

        # remove last stack element
        self.vm_writer.write_pop("temp", 0)

        self.jack_tokenizer.advance()
        # token = (;)

    def compile_while(self) -> None:
        """Compiles a while statement."""

        self.label_counter += 1
        self.vm_writer.write_label("L" + str(self.label_counter))  # label L1
        # token = (while)
        self.jack_tokenizer.advance()
        # token = (expression)
        self.compile_expression()  # compiled-expression
        self.vm_writer.write_arithmetic("not")  # not
        self.vm_writer.write_if("L" + str(self.label_counter + 1))  # if-goto L2

        self.jack_tokenizer.advance()
        # token = (statements)
        self.compile_statements()
        self.vm_writer.write_goto("L" + str(self.label_counter))  # goto L1
        self.label_counter += 1
        self.vm_writer.write_label("L" + str(self.label_counter))  # label L2

        self.jack_tokenizer.advance()
        # token = }

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # token = (if)
        self.jack_tokenizer.advance()
        # token = (expression)
        self.compile_expression()
        # token = '{'
        self.label_counter += 1

        label_true = 'TrueIf' + str(self.label_counter)
        label_false = 'FalseIf' + str(self.label_counter)
        label_end = 'EndIf' + str(self.label_counter)

        self.vm_writer.write_if(label_true)  # if-goto labelTrue
        self.vm_writer.write_goto(label_false)  # goto labelFalse
        self.vm_writer.write_label(label_true)  # label labelTrue

        self.jack_tokenizer.advance()
        # token = (statements)
        self.compile_statements()
        # token = '}'

        self.vm_writer.write_goto(label_end)  # labelEnd
        self.jack_tokenizer.advance() # token = else // next statement

        self.vm_writer.write_label(label_false)  # labelFalse
        # if token == else
        if self.jack_tokenizer.get_token().lower() == 'else':
            self.jack_tokenizer.advance() # now '{'
            self.jack_tokenizer.advance() # now statements
            self.compile_statements() # '}'
            self.jack_tokenizer.advance() # next statement

        self.vm_writer.write_label(label_end)


    def compile_expression(self) -> None:
        """Compiles an expression."""
        # start with term
        self.compile_term()

        # (op term)*
        while self.jack_tokenizer.get_token() in OP:  # operator
            op = self.jack_tokenizer.symbol()

            self.jack_tokenizer.advance()  # continue to next term

            self.compile_term()
            match op:
                case "*":
                    self.vm_writer.write_call("Math.multiply", 2)
                case "/":
                    self.vm_writer.write_call("Math.divide", 2)
                case _:
                    self.vm_writer.write_arithmetic(OP_VM[op])

    def compile_term(self) -> None:
        """Compiles a term."""
        # checks if the term is intConstant, stringConstant, keywordConstant or varName.
        token_type = self.jack_tokenizer.token_type()
        if token_type in ["INT_CONST", "STRING_CONST", "KEYWORD"]:
            self.simple_term(token_type)

        # checks if the term is ('expression') or (unaryOP term)
        elif token_type in ["SYMBOL"]:
            cur_symbol = self.jack_tokenizer.symbol()
            self.expression_or_unary(cur_symbol)

        # token_type must be "IDENTIFIER" - compiling varName, varName '['expression']', subroutineCall
        else:
            identifier = self.jack_tokenizer.identifier()  # get current identifier
            self.jack_tokenizer.advance()
            # now the token can be:
            # "[" for  varName '['expression']'
            # "(" or "." for subroutineCall
            # none of them for simple varName
            current_token = self.jack_tokenizer.get_token()

            match current_token:
                case "(" | ".":
                    self.call_subroutine(current_token, identifier)

                case "[":
                    # example -> arr[5] = 8;
                    self.array_term(identifier)
                case _:
                    self.push_identifier(identifier)


    def expression_or_unary(self, cur_symbol):
        match cur_symbol:
            case "(":
                self.jack_tokenizer.advance()  # (
                self.compile_expression()
                self.jack_tokenizer.advance()  # )

            case "-" | "~":
                self.jack_tokenizer.advance()
                self.compile_term()
                # compiling the term and then negative it.
                self.vm_writer.write_arithmetic(UNARY_OP[cur_symbol])

    def array_term(self, identifier):
        # example -> arr[5] = 8;
        self.jack_tokenizer.advance()  # [
        self.compile_expression()  # the index of the Array (5)
        self.jack_tokenizer.advance()  # ]

        self.push_identifier(identifier)
        # push the identifier (arr)

        self.vm_writer.write_arithmetic("add")  # calc the address of arr[5]
        self.vm_writer.write_pop("pointer", 1)  # pop the address from the heap
        self.vm_writer.write_push("that", 0)  # push the address to the stack

    def simple_term(self, token_type):
        match token_type:
            case "INT_CONST":
                self.vm_writer.write_push("constant", self.jack_tokenizer.int_val())

            case "STRING_CONST":
                # constructor for the str - acting like Array.
                str_token = self.jack_tokenizer.string_val()
                self.vm_writer.write_push("constant", len(str_token))
                self.vm_writer.write_call("String.new", 1)

                # add all the token chars.
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
        n_args = 0
        if current_token == "(":
            function_name = self.class_name + "." + identifier
            n_args += 1
            self.vm_writer.write_push("pointer", 0)

        else:
            # className.subroutine
            self.jack_tokenizer.advance()
            identifier2 = self.jack_tokenizer.identifier()
            kind = self.symbol_table.kind_of(identifier)
            if kind is None:
                # not a variable, therefore it's a class name and we call a function
                function_name = identifier + "." + identifier2

            else:
                # varName.subroutine
                # identifier2 is a variable name, method call different class
                function_name = self.symbol_table.type_of(identifier) + "." + identifier2
                # class_name + method_name
                index = self.symbol_table.index_of(identifier)
                self.vm_writer.write_push(KIND[kind.lower()], index)
                n_args += 1
            self.jack_tokenizer.advance()  # ( in case the symbol was "."

        self.jack_tokenizer.advance()
        n_args += self.compile_expression_list()
        self.jack_tokenizer.advance()  # )
        self.vm_writer.write_call(function_name, n_args)

    def compile_expression_list(self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
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

