import typing
import re


KEYWORDS = ["class", "constructor", "function", "method", "field",
           "static", "var", "int", "char", "boolean",
           "void", "true", "false", "null", "this",
           "let", "do", "if", "else", "while", "return"]

SYMBOLS = ['{', '}', '(', ')', '[',
           ']', '.', ',', ';', '+',
           '-', '*', '/', '&', '|',
           '<', '>', '=', '~', '^', '#']

PATTERN = r'[A-Za-z0-9_]+|[^\sA-Za-z0-9_]'


class JackTokenizer:

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input .jack file / stream and gets ready to tokenize it."""
        input_lines = input_stream.read().splitlines()
        self.tokens_list = []
        self.text_to_tokens(input_lines)
        self.current_token = ""
        self.current_token_index = -1

    def text_to_tokens(self, input_lines):
        """Converts input lines into a list of tokens."""

        handled_lines = []
        comment = False

        # Iterate over each line in the input.
        for line in input_lines:
            i = 0
            tokens_list = []
            while i < len(line):
                # If we're inside a block comment, continue processing until we find the end of the comment.
                if comment:
                    end_index = line.find('*/', i)
                    if end_index != -1:
                        comment = False
                        i = end_index + 2
                    else:
                        break
                elif (line[i] == '/' and
                      i + 1 < len(line) and
                      line[i + 1] == '*'):
                    comment = True
                    i += 2
                elif line[i] in ['"', "'"]:
                    quote_str = line[i]
                    end_index = i + 1
                    while (end_index < len(line) and
                           (line[end_index] != quote_str or
                            line[end_index - 1] == '\\')):
                        end_index += 1
                    if end_index < len(line):
                        tokens_list.append(line[i:end_index + 1])
                        i = end_index + 1
                    else:
                        tokens_list.append(line[i:])
                        break
                elif (i + 1 < len(line) and
                      line[i] == '/' and
                      line[i + 1] == '/'):
                    break
                elif line[i].isspace():
                    i += 1
                else:
                    matcher = re.match(PATTERN, line[i:])
                    if matcher:
                        tokens_list.append(matcher.group(0))
                        i += len(matcher.group(0))
                    else:
                        i += 1
            if tokens_list:
                handled_lines.append(tokens_list)
                for token in tokens_list:
                    self.tokens_list.append(token)

    def get_tokens_list(self):
        # simple get function to pass on the token list
        return self.tokens_list

    def has_more_tokens(self) -> bool:
        """Checks if there are more tokens in the input."""
        return self.current_token_index < len(self.tokens_list) - 1

    def advance(self) -> None:
        """
        Gets the next token from the input and makes it the current token.
        This method should be called only if hasMoreTokens is true. Initially, there is no current token.
        """
        if self.has_more_tokens():
            self.current_token_index += 1
            self.current_token = self.tokens_list[self.current_token_index]

    def token_type(self) -> str:
        """Returns the type of the current token as a constant."""
        if self.current_token in KEYWORDS:
            return "KEYWORD"

        elif self.current_token in SYMBOLS:
            return "SYMBOL"

        elif self.current_token.isdigit():
            return "INT_CONST"

        elif self.current_token[0] == '"' and self.current_token[-1] == '"':
            return "STRING_CONST"

        return "IDENTIFIER"

    def keyword(self) -> str:
        """Returns the keyword which is the current token as a constant.
        This method should be called only if tokenType is KEYWORD."""
        return str(self.current_token).upper()

    def symbol(self) -> str:
        """Returns the character which is the current token. Should be called only if tokenType is SYMBOL."""
        if self.current_token == '<':
            return "&lt;"
        if self.current_token == '>':
            return "&gt;"
        if self.current_token == '&':
            return "&amp;"

        return self.current_token

    def identifier(self) -> str:
        """Returns the string which is the current token. Should be called only if tokenType is IDENTIFIER."""
        return str(self.current_token)

    def int_val(self) -> int:
        """Returns the integer value of the current token. Should be called only if tokenType is INT_CONST."""
        return int(self.current_token) % 32768

    def string_val(self) -> str:
        """Returns the string value of the current token, without the opening and closing double quotes.
        Should be called only if tokenType is STRING_CONST."""
        return self.current_token[1:-1]

    def get_token(self):
        return self.current_token

    def next_token(self):
        return self.tokens_list[self.current_token_index+1]
