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

        code.append.str(statement.value)
        return code


    if isinstance(statement, VarRefNode):

        code.append.str(statement.varname) # missing lettler l for loading the variable 
        return code 
    
    if isinstance(statement, PrintNode): # two instructions load the variable and then print

        raise NotImplementedError

    
    if isinstance(statement, AssignNode): # Recursive

        raise NotImplementedError
    

    if isinstance(statement, BinOpNode): # Recursive

        raise NotImplementedError
    

    # Should never get here
    return code
