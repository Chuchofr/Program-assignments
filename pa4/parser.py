from tokens import Token, TokenType
from tokenstream import *
from acdcast import *

class ParseError(Exception):
    pass 


def parse(ts: TokenStream) -> ASTNode:
    """Parse a single statement from the token stream.

    Policy: each TokenStream represents exactly one line/statement.
    Therefore, after parsing a statement we must be at EOF.
    """
    t = ts.peek()
    #print(f"parse() peeked: {t}")

    if t.tokentype == TokenType.PRINT:
        ts.read()  # consume PRINT
        if t.name is None:
            raise ParseError("Malformed PRINT token")
        node = PrintNode(t.name)
        expect(ts, TokenType.EOF)
        return node

    if t.tokentype == TokenType.INTDEC:
        ts.read()  # consume INTDEC
        if t.name is None:
            raise ParseError("Malformed INTDEC token")
        node = IntDclNode(t.name)
        expect(ts, TokenType.EOF)
        return node

    if t.tokentype == TokenType.VARREF:
        lhs = ts.read()  # consume VARREF
        expect(ts, TokenType.ASSIGN)
        rhs = parse_expression(ts)
        if lhs.lexeme is None:
            raise ParseError("Malformed VARREF token on LHS")
        node = AssignNode(lhs.lexeme, rhs)
        expect(ts, TokenType.EOF)
        return node

    raise ParseError(
        f"Expected TokenType.PRINT, TokenType.INTDCL/INTDEC, or TokenType.VARREF; got {t.tokentype}"
    )


def parse_expression(ts: TokenStream) -> ASTNode:
    """Parse an infix arithmetic expression using shunting-yard, producing an AST."""

    opstack = []   # stack of operator Tokens (and LPAREN)
    valstack = []  # stack of ASTNodes

    precedence = {
        TokenType.EXPONENT: 3,
        TokenType.TIMES: 2,
        TokenType.DIVIDE: 2,
        TokenType.PLUS: 1,
        TokenType.MINUS: 1,
    }

    # True means left-associative
    leftassoc = {
        TokenType.EXPONENT: False,
        TokenType.TIMES: True,
        TokenType.DIVIDE: True,
        TokenType.PLUS: True,
        TokenType.MINUS: True,
    }

    operatortypes = {
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.TIMES,
        TokenType.DIVIDE,
        TokenType.EXPONENT,
    }

    while ts.peek().tokentype != TokenType.EOF:
        tok = ts.peek()

        if tok.tokentype == TokenType.INTLIT:
            tok = ts.read()
            if tok.intvalue is None:
                raise ParseError("Malformed INTLIT token")
            next = ts.peek()
            if ((next.tokentype in operatortypes) or (next.tokentype == TokenType.RPAREN) or (next.tokentype == TokenType.EOF)):
                valstack.append(IntLitNode(tok.intvalue))
                continue
            raise ParseError("Expected operator or rparen after int literal")

        if tok.tokentype == TokenType.VARREF:
            tok = ts.read()
            if tok.lexeme is None:
                raise ParseError("Malformed VARREF token")
            next = ts.peek()
            if ((next.tokentype in operatortypes) or (next.tokentype == TokenType.RPAREN) or (next.tokentype == TokenType.EOF)):
                valstack.append(VarRefNode(tok.lexeme))
                continue
            raise ParseError("Expected operator or rparen after varref")

        if tok.tokentype == TokenType.LPAREN:
            tok = ts.read() # Consume lparen
            next = ts.peek()
            if next.tokentype not in {TokenType.LPAREN, TokenType.VARREF, TokenType.INTLIT}:
                raise ParseError("Expected lparen, intlit, or varref after lparen")
            opstack.append(tok)
            continue

        if tok.tokentype == TokenType.RPAREN:
            ts.read()  # consume RPAREN
            # reduce until matching LPAREN
            while True:
                if len(opstack) == 0:
                    raise ParseError("Mismatched parentheses")
                if opstack[-1].tokentype == TokenType.LPAREN:
                    opstack.pop()  # discard LPAREN
                    break
                reduce(opstack, valstack)
            continue

        if tok.tokentype in operatortypes:
            incoming = ts.read()  # consume operator
            next = ts.peek() # Get next item
            if next.tokentype not in {TokenType.INTLIT, TokenType.LPAREN, TokenType.VARREF}:
                raise ParseError("Expected operand or lparen after operator")

            while len(opstack) > 0 and opstack[-1].tokentype in operatortypes:
                top = opstack[-1]

                top_prec = precedence[top.tokentype]
                inc_prec = precedence[incoming.tokentype]

                if (top_prec > inc_prec) or (top_prec == inc_prec and leftassoc[incoming.tokentype]):
                    reduce(opstack, valstack)
                else:
                    break

            opstack.append(incoming)
            continue

        raise ParseError(f"Unexpected token in expression: {tok}")

    # consume remaining operators
    while len(opstack) > 0:
        if opstack[-1].tokentype == TokenType.LPAREN:
            raise ParseError("Mismatched parentheses")
        reduce(opstack, valstack)

    if len(valstack) != 1:
        raise ParseError("Expression did not reduce to one AST")

    return valstack.pop()





def reduce(opstack: list, valstack: list) -> None:
    """Pop one operator and two operands to build a BinOpNode and push it back."""
    if len(opstack) == 0:
        raise ParseError("Expected operator")
    
    operator = opstack.pop()

    if len(valstack) <= 1:
        raise ParseError(f"Expected two operands for operator {operator.tokentype}")
    
    rhs = valstack.pop()
    lhs = valstack.pop()
    valstack.append(BinOpNode(operator.tokentype, lhs, rhs))


def expect(ts: TokenStream, expectedtype: TokenType) -> Token:
    tok = ts.peek()
    if tok.tokentype != expectedtype:
        raise ParseError(f"Expected {expectedtype} but found {tok.tokentype}")
    tok = ts.read()
    return tok
