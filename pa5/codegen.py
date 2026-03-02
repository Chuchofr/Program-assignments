from acdcast import *

class InstructionList:

    def __init__(self):

        self.instructions = []

    def append(self, instruction: str):

        self.instructions.append(instruction)

    def extend(self, newinstructions: "InstructionList"):
        
        self.instructions.extend(newinstructions.instructions)

    def __iter__(self):
        return iter(self.instructions)




def codegenerator(program: list[ASTNode]) -> InstructionList:

    code = InstructionList()

    for statement in program:

        newcode = stmtcodegen(statement)
        code.extend(newcode)

    return code
    

def stmtcodegen(statement: ASTNode) -> InstructionList:

    code = InstructionList()

    if isinstance(statement, IntDclNode):
        return code 


    if isinstance(statement, IntLitNode):

        code.append(str(statement.value))
        return code


    if isinstance(statement, VarRefNode):

        code.append(f"l{statement.varname}") # missing lettler l for loading the variable 
        return code 
    
    if isinstance(statement, PrintNode): # two instructions load the variable and then print

        code.append(f"l{statement.varname}")
        code.append("p")
        return code

    
    if isinstance(statement, AssignNode): # Recursive

        code.extend(stmtcodegen(statement.expr))
        code.append(f"s{statement.varname}")
        return code
    

    if isinstance(statement, BinOpNode): # Recursive

        code.extend(stmtcodegen(statement.left))
        

        if statement.optype == TokenType.EXPONENT:

            if isinstance(statement.right, IntLitNode):
                exp = statement.right 
            #Put d's and *'s here
                if exp == 0:
                    code.append("si")
                    code.append("1")
                    return code
                
                #if exp > 0
                for _ in range(exp - 1):
                    code.append("d")

                for _ in range(exp - 1):
                    code.append("*")

                return code
            else:
                code.extend(stmtcodegen(statement.right))
                code.append("^")
                return code



        else:
           code.extend(stmtcodegen(statement.right))
           code.append(statement.optype.value)
           return code



        raise ValueError(f"Unknown binary operator: {statement.optype}")
    

    # Should never get here
    return code
