from charstream import CharStream
from tokens import Token, TokenType
from tokenstream import TokenStream
import string

RESERVED = {'i', 'f', 'o', 'n', 'p', 'l', 's'}
VALID_VARS = set(string.ascii_lowercase) - RESERVED

class Tokenizer:

    def __init__(self, cs: CharStream):
        self.cs = cs

    def tokenize(self) -> TokenStream:
        ts = TokenStream()
        while True:
            tok = self.nexttoken()
            ts.append(tok)
            if tok.tokentype == TokenType.EOF:
                break

        return ts
    

    def nexttoken(self) -> Token:

        char = self.cs.read()

        while char in {' ', '\n', '\r', '\t'}:
            char = self.cs.read() # Consume chars for space, newline, etc.
        
        
        if char == '':
            return Token(TokenType.EOF, lexeme = f"{char}")



        match char:

            case '=':
                return Token(TokenType.ASSIGN, lexeme = f"{char}")
            
            case '(':
                return Token(TokenType.LPAREN, lexeme = f"{char}")
                
            case ')': 
                return Token(TokenType.RPAREN, lexeme = f"{char}")
            
            case '+':
                return Token(TokenType.PLUS, lexeme = f"{char}")
            
            case '-':
                return Token(TokenType.MINUS, lexeme = f"{char}")
            
            case '*':
                return Token(TokenType.TIMES, lexeme = f"{char}")
            
            case '/':
                return Token(TokenType.DIVIDE, lexeme = f"{char}")
            
            case '^':
                return Token(TokenType.EXPONENT, lexeme = f"{char}")
            
            case 'i':
                # consume optional whitespace after 'i'
                while not self.cs.eof() and self.cs.peek() in {' ', '\n', '\r', '\t'}:
                    self.cs.read()

                if self.cs.eof():
                    raise ValueError("Expected variable name after 'i'")

                name = self.cs.read()

                if (not name.isalpha()) or (name not in VALID_VARS):
                    raise ValueError(f"Invalid variable character after 'i': {name}")

                return Token(TokenType.INTDEC, lexeme=f"i{name}", name=f"{char}")

            case 'p':
                # consume optional whitespace after 'p'
                while not self.cs.eof() and self.cs.peek() in {' ', '\n', '\r', '\t'}:
                    self.cs.read()

                name = self.cs.read()

                if (not name.isalpha()) or (name not in VALID_VARS):
                    raise ValueError(f"Invalid variable character after 'p': {name}")

                return Token(TokenType.PRINT, lexeme=f"p{name}", name=char)

            
            case _:
                pass # Move on to secondary inspection to handle digits, vars, error case

        if char.isdigit():
            lexeme, intvalue = self.readintliteral(char)
            return Token(TokenType.INTLIT, lexeme = lexeme, intvalue = intvalue)


        if char.isalpha():
            if char not in VALID_VARS:
                raise ValueError(f"Invalid variable character ater 'i': {char}")
            else:
                return Token(TokenType.VARREF, lexeme = f"{char}", name=char)
           
        raise ValueError(f"Unexpected character: {char!r}")
        
    

    def readintliteral(self, firstchar: str) -> tuple[str, int]:
        
        digits: list[str] = []
        digits.append(firstchar)
        #if CONDITION:
        #    raise ValueError("Integer literal cannot have a leading zero")

        #while not self.cs.eof() and SOMETHING:
        #    digits.append(SOMETHING)

        if firstchar == '0' and self.cs.peek().isdigit():
            raise ValueError("Integral literal cannot have a leading zero")
        
        while not self.cs.eof() and self.cs.read().isdigit():
            digits.append(self.cs.read())
       
       
        lexeme = ''.join(digits)

        return lexeme, int(lexeme)
