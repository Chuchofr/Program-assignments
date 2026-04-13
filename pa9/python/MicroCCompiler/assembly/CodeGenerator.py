import sys
import os

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor

class CodeGenerator(AbstractASTVisitor):

  def __init__(self):
    self.intRegCount = 1 # Changed from 0 so t0 is never used, this way maybe we could use t0 for the constant 0 register
    self.floatRegCount = 1 
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'
    self.numCtrlStructs = 0

    # Put code here for label counting



  def getIntRegCount(self):
    return self.intRegCount

  def getFloatRegCount(self):
    return self.floatRegCount

  # Generate code for Variables
  #
  # Create a code object that just holds a variable
  # Important: add a pointer from the code object to the symbol table entry so
  # we know how to generate code for it later (we'll need it to find the
  # address)
  #
  # Mark the code object as holding a variable, and also as an lval

  def postprocessVarNode(self, node: VarNode) -> CodeObject:
    sym = node.getSymbol()

    co = CodeObject(sym)
    co.lval = True
    co.type = node.getType()

    return co



  
  def postprocessIntLitNode(self, node: IntLitNode) -> CodeObject:
    co = CodeObject()

    temp = self.generateTemp(Scope.Type.INT)
    val = node.getVal()
    # LI t2, 5
    co.code.append(Li(temp, val))
    co.temp = temp
    co.lval = False
    co.type = node.getType()


    return co



  def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
    co = CodeObject()

    temp = self.generateTemp(Scope.Type.FLOAT)
    val = node.getVal()
    co.code.append(FImm(temp, val))
    co.temp = temp
    co.lval = False
    co.type = node.getType()

    return co
  

  def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
    ''' 
    Copy from PA8
    '''
    co = CodeObject()
    newcode = CodeObject()

    #print("Left: ", left, "Left Type: ", left.type)
    #print("Right: ", right, "Right Type: ", right.type)
    #print("Optype: ", str(node.op))

    optype = str(node.op) # Get string corresponding to the operation (+, -, *, /)
    #Step 1: add code from left child
    
    #Step 1a: check if left child is an lval or rval; if lval, rvalify
    if left.lval == True:
      left = self.rvalify(left) # create new code object, fix this, this is bad?
      #print("Left type after rvalify:", left.type)
    co.code.extend(left.code)

    #Step 2: add code from right child

    if right.lval == True:
      right = self.rvalify(right)
    
    co.code.extend(right.code)
  
    #Step 2a: check if left child is an lval or rval; if lval, rvalify

    #Step 3: generate correct binop.  8 cases for 4 ops, float vs. int. for 4 arithmetic ops.

    if left.type != right.type:
      print("Incompatible types in binary operation!\n")
    
    # Get appropriate new temporary for result of operation
    if left.type == Scope.Type.INT:
      #print("Processing binop with INTs")
      newtemp = self.generateTemp(Scope.Type.INT)
      if optype == "OpType.ADD":
        newcode = Add(left.temp, right.temp, newtemp)
      elif optype == "OpType.SUB":
        newcode = Sub(left.temp, right.temp, newtemp)
      elif optype == "OpType.MUL":
        newcode = Mul(left.temp, right.temp, newtemp)
      elif optype == "OpType.DIV":
        newcode = Div(left.temp, right.temp, newtemp)
      else:
        print("Bad operation in binop!\n")


    elif left.type == Scope.Type.FLOAT:
      newtemp = self.generateTemp(Scope.Type.FLOAT)
      if optype == "OpType.ADD":
        newcode = FAdd(left.temp, right.temp, newtemp)
      elif optype == "OpType.SUB":
        newcode = FSub(left.temp, right.temp, newtemp)
      elif optype == "OpType.MUL":
        newcode = FMul(left.temp, right.temp, newtemp)
      elif optype == "OpType.DIV":
        newcode = FDiv(left.temp, right.temp, newtemp)
      else:
        print("Bad operation in binop!\n")

    else:
      print("Bad type in binary op!\n")


    #Step 4: update temp, lval etc., return code object


    co.code.append(newcode)
    co.lval = False
    co.temp = newtemp
    co.type = left.type
    #print(newcode)
    return co
	 



  def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()  # Step 0

    
    if expr.lval:
      expr = self.rvalify(expr)

    co.code.extend(expr.code) # Add in all the code required to get expr after rvalifying


    if expr.type == Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(Neg(src=expr.temp, dest=temp))
      

    elif expr.type == Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(FNeg(src=expr.temp, dest=temp))

    else:
      raise Exception("Non int/float type in unary op!")

    co.type = expr.type
    co.temp = temp
    co.lval = False 

    return co
  

  def postprocessAssignNode(self, node: AssignNode, left: CodeObject, right: CodeObject) -> CodeObject:
    co = CodeObject()

    assert(left.isVar())

    if right.lval:
      right = self.rvalify(right)
    co.code.extend(right.code)

    address = self.generateAddrFromVariable(left)
    temp = self.generateTemp(Scope.Type.INT)
    co.code.append(La(temp, address))

    if left.type is Scope.Type.INT:
      co.code.append(Sw(right.temp, temp, '0'))
    elif left.type is Scope.Type.FLOAT:
      co.code.append(Fsw(right.temp, temp, '0'))
    else: 
      raise Exception("Bad Type in assign node")

    co.temp = right.temp
    co.lval = False
    co.type = left.type

    return co


  def postprocessStatementListNode(self, node: StatementListNode, statements: list) -> CodeObject:
    co = CodeObject()

    for subcode in statements:
      co.code.extend(subcode.code)

    co.type = None
    return co

	 # Generate code for read
	 # 
	 # Step 0: create new code object
	 # Step 1: add code from VarNode (make sure it's an lval)
	 # Step 2: generate GetI instruction, storing into temp
	 # Step 3: generate store, to store temp in variable
	
  def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
    co = CodeObject()

    assert(var.isVar())

    if var.type is Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(GetI(temp))
      address = self.generateAddrFromVariable(var)
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp2, address))
      co.code.append(Sw(temp, temp2, '0'))

    elif var.type is Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(GetF(temp))
      address = self.generateAddrFromVariable(var)
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp2, address))
      co.code.append(Fsw(temp, temp2, '0'))

    else:
      raise Exception("Bad type in read node")


    return co

	 

  def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()

    if expr.type is Scope.Type.INT:
      if expr.lval:
        expr = self.rvalify(expr)

      co.code.extend(expr.code)
      co.code.append(PutI(expr.temp))
    
    elif expr.type is Scope.Type.FLOAT:
      if expr.lval:
        expr = self.rvalify(expr)

      co.code.extend(expr.code)
      co.code.append(PutF(expr.temp))

    else: 
      assert(expr.isVar())
      address = self.generateAddrFromVariable(expr)
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp, address))
      co.code.append(PutS(temp))

    return co



  def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
    '''
    NEW:
    '''
    co = CodeObject()

    if left.lval == True:
      left = self.rvalify(left)
    co.code.extend(left.code)

    if right.lval == True:
      right = self.rvalify(right)
    co.code.extend(right.code)

    optype = str(node.getOp()).upper()
    temp = self.generateTemp(Scope.Type.INT)

    if left.type == Scope.Type.INT:
      truelabel = "condtrue_" + temp
      donelabel = "conddone_" + temp

      co.code.append(Li(temp, 0))

      if "!=" in optype or "NE" in optype:
        co.code.append(Bne(left.temp, right.temp, truelabel))
      elif "<=" in optype or "LE" in optype:
        co.code.append(Ble(left.temp, right.temp, truelabel))
      elif ">=" in optype or "GE" in optype:
        co.code.append(Bge(left.temp, right.temp, truelabel))
      elif "==" in optype or "EQ" in optype:
        co.code.append(Beq(left.temp, right.temp, truelabel))
      elif "<" in optype or "LT" in optype:
        co.code.append(Blt(left.temp, right.temp, truelabel))
      elif ">" in optype or "GT" in optype:
        co.code.append(Bgt(left.temp, right.temp, truelabel))
      else:
        raise Exception("Bad conditional operator in cond node: " + str(node.getOp()))

      co.code.append(J(donelabel))
      co.code.append(Label(truelabel))
      co.code.append(Li(temp, 1))
      co.code.append(Label(donelabel))

    elif left.type == Scope.Type.FLOAT:
      if "==" in optype or "EQ" in optype:
        co.code.append(Feq(left.temp, right.temp, temp))
      elif "<=" in optype or "LE" in optype:
        co.code.append(Fle(left.temp, right.temp, temp))
      elif ">=" in optype or "GE" in optype:
        co.code.append(Fle(right.temp, left.temp, temp))
      elif "<" in optype or "LT" in optype:
        co.code.append(Flt(left.temp, right.temp, temp))
      elif ">" in optype or "GT" in optype:
        co.code.append(Flt(right.temp, left.temp, temp))
      elif "!=" in optype or "NE" in optype:
        temp2 = self.generateTemp(Scope.Type.INT)
        truelabel = "condtrue_" + temp
        donelabel = "conddone_" + temp

        co.code.append(Feq(left.temp, right.temp, temp2))
        co.code.append(Li(temp, 0))
        co.code.append(Beq(temp2, "x0", truelabel))
        co.code.append(J(donelabel))
        co.code.append(Label(truelabel))
        co.code.append(Li(temp, 1))
        co.code.append(Label(donelabel))
      else:
        raise Exception("Bad conditional operator in cond node: " + str(node.getOp()))

    else:
      raise Exception("Bad type in cond node")

    co.temp = temp
    co.lval = False
    co.type = Scope.Type.INT

    return co

  def postprocessIfStatementNode(self, node: IfStatementNode, cond: CodeObject, tlist: CodeObject, elist: CodeObject) -> CodeObject:
    '''
    NEW
    '''
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()
    
    co = CodeObject()

    elselabel = self._generateElseLabel(labelnum)
    donelabel = self._generateDoneLabel(labelnum)

    co.code.extend(cond.code)
    co.code.append(Bne(cond.temp, "x0", elselabel))

    co.code.extend(tlist.code)
    co.code.append(J(donelabel))
    co.code.append(Label(elselabel))
    co.code.extend(elist.code)
    co.code.append(Label(donelabel))
    
    return co



  def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist:
  CodeObject) -> CodeObject:
    ''' 
    NEW
    '''
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()
    co = CodeObject()

    looplabel = self._generateLoopLabel(labelnum)
    donelabel = self._generateDoneLabel(labelnum)


    co.code.extend(cond.code)
    co.code.append(Bne(cond.temp, "x0", donelabel))

    co.code.extend(wlist.code)
    co.code.append(J(looplabel))
    co.code.append(Label(donelabel))

    return co
  


  
  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
    co = CodeObject()

    if retExpr.lval is True:
      retExpr = self.rvalify(retExpr)

    co.code.extend(retExpr.code)
    co.code.append(Halt())
    co.type = None
    return co


  
  def generateTemp(self, t: Scope.Type) -> str:
    if t == Scope.Type.INT:
      s = self.intTempPrefix + str(self.intRegCount)
      self.intRegCount += 1
      return s
    elif t == Scope.Type.FLOAT:
      s = self.floatTempPrefix + str(self.floatRegCount)
      self.floatRegCount += 1
      return s
    else:
      raise Exception("Generating temp for bad type")

  
  




  def rvalify(self, lco : CodeObject) -> CodeObject:
    assert(lco.lval is True)
    assert(lco.isVar() is True)
    
    co = CodeObject()

    address = self.generateAddrFromVariable(lco)
    temp1 = self.generateTemp(Scope.Type.INT) # Addresses are always ints
    co.code.append(La(temp1, address)) # Load address (global only)

    if lco.type is Scope.Type.INT:
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(Lw(temp2, temp1, '0'))

    elif lco.type is Scope.Type.FLOAT:
      temp2 = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(Flw(temp2, temp1, '0'))

    else:
      raise Exception("Bad type in rvalify!")

    co.type = lco.type
    co.lval = False
    co.temp = temp2


    return co

    
  def generateAddrFromVariable(self, lco: CodeObject) -> str:
    
    ''' 
    Copy from PA8
    Don't use the exact same thing as in PA8...use this to get addresses
    symbol = lco.getSTE()
    address = symbol.addressToString()
    Otherwise the hex addresses for globals will get mangled
    '''
    assert(lco.isVar() is True)

    symbol = lco.getSTE()   # Get symbol from symbol table
    address = str(symbol.getAddress()) # Get address of variable

    return address
  


# Here we should define functions that generate labels for conditionals and loops

  def _incrnumCtrlStruct(self):
    self.numCtrlStructs += 1

  def _getnumCtrlStruct(self) -> int:
    return self.numCtrlStructs
  
  def _generateThenLabel(self, num: int) -> str:
    return "then_"+str(num)

  def _generateElseLabel(self, num: int) -> str:
    return "else_"+str(num)

  def _generateLoopLabel(self, num: int) -> str:
    return "loop_"+str(num)

  def _generateDoneLabel(self, num: int) -> str:
    return "done_"+str(num)
  
 

  