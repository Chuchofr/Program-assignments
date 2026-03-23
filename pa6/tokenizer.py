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

                if self.cs.eof() or self.cs.peek() == '':
                    raise ValueError("Expected variable name after 'i':")


                if (not self.cs.peek().isalpha()) or (self.cs.peek() not in VALID_VARS):
                    raise ValueError(f"Invalid variable character: {self.cs.peek()!r}")
                
                name = self.cs.read()
                return Token(TokenType.INTDEC, lexeme=f"i{name}", name=name)

            case 'p':
                # consume optional whitespace after 'p'
                while not self.cs.eof() and self.cs.peek() in {' ', '\n', '\r', '\t'}:
                    self.cs.read()

                if self.cs.eof() or self.cs.peek() == '':
                    raise ValueError("Expected variable name after 'p'")

                if (not self.cs.peek().isalpha()) or (self.cs.peek() not in VALID_VARS):
                    raise ValueError(f"Invalid variable character after 'p': {self.cs.peek()!r}")
                
                name = self.cs.read()
                return Token(TokenType.PRINT, lexeme=f"p{name}", name=name)


            case 'f':
                while not self.cs.eof() and self.cs.peek() in {' ', '\n', '\r', '\t'}:
                    self.cs.read()

                if self.cs.eof() or self.cs.peek() == '':
                    raise ValueError("Expected variable name after 'f'")
                
                if (not self.cs.peek().isalpha()) or (self.cs.peek() not in VALID_VARS):
                    raise ValueError(f"invalid character: {self.cs.peek()!r}")
                
                name = self.cs.read()
                return Token(TokenType.FLOATDEC, lexeme = f"f{name}", name = name)
            
            case _:
                pass # Move on to secondary inspection to handle digits, vars, error case

        if char.isdigit():
            lexeme, value, is_float = self.readnumberliteral(char)
            if is_float:
                return Token(TokenType.FLOATLIT, lexeme = lexeme, floatvalue = value)
            return Token(TokenType.INTLIT, lexeme = lexeme, intvalue = value)


        if char.isalpha():
            if char not in VALID_VARS:
                raise ValueError(f"Invalid variable character: {char!r}")
            else:
                return Token(TokenType.VARREF, lexeme = f"{char}")
           
        raise ValueError(f"Unexpected character: {char!r}")
        
    

    def readnumberliteral(self, firstchar: str) -> tuple[str, int | float, bool]:
        chars = [firstchar]
        seen_dot = False

        if firstchar == '0' and self.cs.peek().isdigit():
            raise ValueError("Integer literal cannot have a leading zero")

        while not self.cs.eof():
            nxt = self.cs.peek()

            if nxt.isdigit(): 
                chars.append(self.cs.read())
            elif nxt == '.' and not seen_dot:
                seen_dot = True
                chars.append(self.cs.read())
            else:
                break
        
        lexeme = ''.join(chars)

        if seen_dot:
            if lexeme.endswith('.'):
                raise ValueError("Float literal must have digits after decimal point")
            return lexeme, float(lexeme), True
        
        return lexeme, int(lexeme), False
