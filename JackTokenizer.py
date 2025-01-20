"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
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
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        # Your code goes here!
        # A good place to start is to read all the lines of the input:

        input_lines = input_stream.read().splitlines()
        self.tokens_list = []
        self.text_to_tokens(input_lines)
        self.current_token = ""
        self.current_token_index = -1

    def text_to_tokens(self, input_lines):
        """Converts input lines into a list of tokens while handling comments and strings."""

        cleaned_lines = []  # This will store the cleaned tokenized lines.
        comment = False  # Flag to track if we're inside a block comment.

        # Iterate over each line in the input.
        for in_line in input_lines:
            i = 0  # Initialize the index for each line.
            tokens_lst = []  # List to store tokens found in the current line.

            # Process each character in the line.
            while i < len(in_line):

                # If we're inside a block comment, continue processing until we find the end of the comment.
                if comment:
                    end_index = in_line.find('*/', i)  # Look for the end of the block comment.
                    if end_index != -1:
                        comment = False  # Exit block comment mode once '*/' is found.
                        i = end_index + 2  # Skip past the closing comment symbol.
                    else:
                        break  # If no closing block comment is found, stop processing this line.

                # If we find the start of a block comment (/*), mark the flag as True.
                elif (in_line[i] == '/' and
                      i + 1 < len(in_line) and
                      in_line[i + 1] == '*'):
                    comment = True  # Start of a block comment.
                    i += 2  # Skip past the opening comment symbol.

                # If we find a quote (either " or '), process the string and handle escape sequences.
                elif in_line[i] in ['"', "'"]:
                    quote_str = in_line[i]  # Store the quote type (single or double).
                    end_index = i + 1  # Initialize the end index to start after the quote.

                    # Keep moving the end index until the string is closed, considering escape sequences.
                    while (end_index < len(in_line) and
                           (in_line[end_index] != quote_str or
                            in_line[end_index - 1] == '\\')):
                        end_index += 1

                    # If we find the closing quote, append the string token.
                    if end_index < len(in_line):
                        tokens_lst.append(in_line[i:end_index + 1])  # Add the string token.
                        i = end_index + 1  # Move past the closing quote.
                    else:
                        # If the string is not closed, add the remaining part of the line (unclosed string).
                        tokens_lst.append(in_line[i:])
                        break

                # If we find a single-line comment (//), ignore the rest of the line.
                elif (i + 1 < len(in_line) and
                      in_line[i] == '/' and
                      in_line[i + 1] == '/'):
                    break  # Skip the rest of the line after the comment.

                # If we encounter whitespace, simply move to the next character.
                elif in_line[i].isspace():
                    i += 1  # Skip the whitespace.

                # Otherwise, match regular tokens (alphanumeric or special characters).
                else:
                    matcher = re.match(PATTERN, in_line[i:])  # Try to match a token using the regex pattern.
                    if matcher:
                        tokens_lst.append(matcher.group(0))  # If a match is found, add it to the tokens list.
                        i += len(matcher.group(0))  # Move past the matched token.
                    else:
                        i += 1  # If no token is found, move to the next character.

            # If any tokens were found in the current line, add them to the cleaned_lines list.
            if tokens_lst:
                cleaned_lines.append(tokens_lst)
                # Add each token to the global tokens list.
                for token in tokens_lst:
                    self.tokens_list.append(token)

    def get_tokens_list(self):
        # simple get function to pass on the token list
        return self.tokens_list

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        return self.current_token_index < len(self.tokens_list) - 1

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token.
        This method should be called if has_more_tokens() is true.
        Initially there is no current token.
        """
        if self.has_more_tokens():
            self.current_token_index += 1
            self.current_token = self.tokens_list[self.current_token_index]

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
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
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT",
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO",
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        return str(self.current_token).upper()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' |
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        # Your code goes here!
        if self.current_token == '<':
            return "&lt;"
        if self.current_token == '>':
            return "&gt;"
        if self.current_token == '&':
            return "&amp;"

        return self.current_token

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.
        """
        # Your code goes here!
        return str(self.current_token)

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        # Your code goes here!
        return int(self.current_token) % 32768

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including
                      double quote or newline '"'
        """
        # Your code goes here!
        return self.current_token[1:-1]

    def get_token(self):
        return self.current_token

    def next_token(self):
        return self.tokens_list[self.current_token_index+1]
