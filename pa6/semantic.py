from acdcast import *

class SemanticError(Exception):
    pass


def semanticanalysis(program: list[ASTNode]) -> None:

    declared = []
    initialized = []

    for linenumber, statement in enumerate(program, start=1):
        _semantic_check_stmt(statement, declared, initialized, linenumber)
    
    return 


def _semantic_check_stmt(statement: ASTNode, declared: list[str], initialized: list[str], linenumber: int) -> None:

    if isinstance(statement, IntDclNode):
        varname = statement.varname
        if varname in declared:
            raise SemanticError(f"Variable {varname!r} redeclared at line {linenumber}")
        declared.append(varname)
        return
        # SemanticError(f"Variable {varname!r} redeclared at line {linenumber}")    
    
    if isinstance(statement, FloatDclNode):
        varname = statement.varname
        if varname in declared:
            raise SemanticError(f"Variable {varname!r} redeclared at line {linenumber}")
        declared[varname] = "float"
        return

    if isinstance(statement, PrintNode):
        varname = statement.varname
        if varname not in declared:
            raise SemanticError(f"Trying to print undeclared variable {varname!r} at line {linenumber}")
        if varname not in initialized:
            raise SemanticError(f"Trying to print uninitialized variable {varname!r} at line {linenumber}")
        return 
        # SemanticError(f"Trying to print undeclared variable {varname!r} at line {linenumber}")
        # SemanticError(f"Trying to print uninitialized variable {varname!r} at line {linenumber}")
    
    if isinstance(statement, AssignNode):
        varname = statement.varname
        if varname not in declared:
            raise SemanticError(f"Assignment to undeclared variable {varname!r} at line {linenumber}")
       
        exprtype =  _semantic_check_expr(statement.expr, declared, initialized, linenumber)
        vartype = declared[varname]
    
        if vartype == "int" and exprtype == "float":
            raise SemanticError(f"cannot assign float expression to int variable {varname!r} at line {linenumber}")

        if varname not in initialized:
            initialized.append(varname)
        return 
        # SemanticError(f"Assignment to undeclared variable {varname!r} at line {linenumber}")


    raise SemanticError("Unknown statement type at line {linenumber}")
    # Catches any weird statement types; this should never happen for a validly parsed program
    # Keeping it here though will help if your parser has an undiscovered or unfixed bug


def _semantic_check_expr(expr: ASTNode, declared: dict[str, str], initialized: list[str], linenumber: int):
    if isinstance(expr, IntLitNode):
        return "int"
    
    if isinstance(expr, FloatLitNode):
        return "float"
    
    if isinstance(expr, VarRefNode):
        varname = expr.varname
        if varname not in declared:
            raise SemanticError(f"Use of undeclared variable {varname!r} at line {linenumber}")
        if varname not in initialized:
            raise SemanticError(f"Use of unitialized variable {varname!r} at line {linenumber}")
        return declared[varname]
        # SemanticError(f"Use of undeclared variable {varname!r} at line {linenumber}")
        # SemanticError(f"Use of unitialized variable {varname!r} at line {linenumber}")
        
    if isinstance(expr, BinOpNode):
        # Two recursive calls go here...
        lefttype = _semantic_check_expr(expr.left, declared, initialized, linenumber)
        righttype = _semantic_check_expr(expr.right, declared, initialized, linenumber)

        if lefttype == "float" or righttype == "float":
            return "float"
        return "int"

    
    raise SemanticError(f"Unknown expression type at line {linenumber}")
    # Catches any weird statement types; this should never happen for a validly parsed program
    # Keeping it here though will help if your parser has an undiscovered or unfixed bug