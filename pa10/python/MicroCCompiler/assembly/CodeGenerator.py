import sys
import os
from typing import List

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor

class CodeGenerator(AbstractASTVisitor):

  def __init__(self):
    self.intRegCount = 1
    self.floatRegCount = 1
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'
    self.numCtrlStructs = 0
    self.loopLabel = 0
    self.elseLabel = 0
    self.outLabel = 0
    self.currFunc = None

  def getIntRegCount(self):
    return self.intRegCount

  def getFloatRegCount(self):
    return self.floatRegCount



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
    co.code.append(Li(temp, str(val)))
    co.temp = temp
    co.lval = False
    co.type = node.getType()


    return co


  def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
    co = CodeObject()

    temp = self.generateTemp(Scope.Type.FLOAT)
    val = node.getVal()
    co.code.append(FImm(temp, str(val)))
    co.temp = temp
    co.lval = False
    co.type = node.getType()

    return co

  def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
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

    symbol = left.getSTE()
    address = symbol.addressToString()

    if symbol.isLocal():
      if left.type is Scope.Type.INT:
        co.code.append(Sw(right.temp, "fp", address))
      elif left.type is Scope.Type.FLOAT:
        co.code.append(Fsw(right.temp, "fp", address))
      else:
        raise Exception("Bad Type in assign node")
    else:
      addressco = self.generateAddrFromVariable(left)
      co.code.extend(addressco)

      if left.type is Scope.Type.INT:
        co.code.append(Sw(right.temp, addressco.getLast().getDest(), '0'))
      elif left.type is Scope.Type.FLOAT:
        co.code.append(Fsw(right.temp, addressco.getLast().getDest(), '0'))
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


  def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
    co = CodeObject()

    assert(var.isVar())

    symbol = var.getSTE()
    address = symbol.addressToString()

    if var.type is Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(GetI(temp))

      if symbol.isLocal():
        co.code.append(Sw(temp, "fp", address))
      else:
        addressco = self.generateAddrFromVariable(var)
        co.code.extend(addressco)
        co.code.append(Sw(temp, addressco.getLast().getDest(), "0"))

    elif var.type is Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(GetF(temp))

      if symbol.isLocal():
        co.code.append(Fsw(temp, "fp", address))
      else:
        addressco = self.generateAddrFromVariable(var)
        co.code.extend(addressco)
        co.code.append(Fsw(temp, addressco.getLast().getDest(), "0"))

    else:
      raise Exception("Bad type in read node")

    return co


  def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
    co = CodeObject()

    if node.getWriteExpr().getType() is Scope.Type.STRING:
      assert(expr.isVar())

      addressco = self.generateAddrFromVariable(expr)
      co.code.extend(addressco)
      co.code.append(PutS(addressco.getLast().getDest()))

    elif expr.type is Scope.Type.INT:
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
      raise Exception("Bad type in write node")

    return co
	
  def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
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

      co.code.append(Li(temp, '0'))

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
      co.code.append(Li(temp, '1'))
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
        co.code.append(Li(temp, '0'))
        co.code.append(Beq(temp2, "x0", truelabel))
        co.code.append(J(donelabel))
        co.code.append(Label(truelabel))
        co.code.append(Li(temp, '1'))
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
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()
  
    co = CodeObject()

    elselabel = self._generateElseLabel(labelnum)
    donelabel = self._generateDoneLabel(labelnum)

    co.code.extend(cond.code)

    if elist is None:
      co.code.append(Beq(cond.temp, "x0", donelabel))
      co.code.extend(tlist.code)
      co.code.append(Label(donelabel))
    else:
      co.code.append(Beq(cond.temp, "x0", elselabel))
      co.code.extend(tlist.code)
      co.code.append(J(donelabel))
      co.code.append(Label(elselabel))
      co.code.extend(elist.code)
      co.code.append(Label(donelabel))
  
    return co

  def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist:
  CodeObject) -> CodeObject:
    self._incrnumCtrlStruct()
    labelnum = self._getnumCtrlStruct()
    co = CodeObject()

    looplabel = self._generateLoopLabel(labelnum)
    donelabel = self._generateDoneLabel(labelnum)

    co.code.append(Label(looplabel))
    co.code.extend(cond.code)
    co.code.append(Beq(cond.temp, "x0", donelabel))

    co.code.extend(wlist.code)
    co.code.append(J(looplabel))
    co.code.append(Label(donelabel))

    return co
  

  def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
    co = CodeObject()

    if retExpr is not None and retExpr.lval is True:
      retExpr = self.rvalify(retExpr)

    if retExpr is not None:
      co.code.extend(retExpr.code)

    rettype = node.getFuncSymbol().getReturnType()

    if rettype is Scope.Type.INT:
      co.code.append(Sw(retExpr.temp, "fp", "8"))
    elif rettype is Scope.Type.FLOAT:
      co.code.append(Fsw(retExpr.temp, "fp", "8"))
    elif rettype is not Scope.Type.VOID:
      raise Exception("Bad return type in return node")

    co.code.append(J(self._generateFunctionRetLabel()))
    co.type = None

    return co




  def preprocessFunctionNode(self, node: FunctionNode):

    self.currFunc = node.getFuncName()

    self.intRegCount = 1
    self.floatRegCount = 1


  def postprocessFunctionNode(self, node: FunctionNode, body: CodeObject) -> CodeObject:
    '''
    Responsible for actually putting together a function's code
    Step 1: Set up stack frame
    Step 2: Save temporaries
    Step 3: Add in body code (this will include a return node)
    Step 4: Load temporaries
    Step 5: Undo stack frame
    Step 6: Append the RET instruction
    '''

    co = CodeObject()

    numlocals = node.getScope().getNumLocals()
    numintregs = self.getIntRegCount() - 1
    numfloatregs = self.getFloatRegCount() - 1

    co.code.append(Label(self._generateFunctionEntryLabel()))
    co.code.append(Sw("fp", "sp", "0"))
    co.code.append(Mv("sp", "fp"))
    co.code.append(Addi("sp", "-4", "sp"))
    co.code.append(Addi("sp", "-" + str(4 * numlocals), "sp"))

    for i in range(1, numintregs + 1):
      co.code.append(Sw("t" + str(i), "sp", "0"))
      co.code.append(Addi("sp", "-4", "sp"))

    for i in range(1, numfloatregs + 1):
      co.code.append(Fsw("f" + str(i), "sp", "0"))
      co.code.append(Addi("sp", "-4", "sp"))

    co.code.extend(body.code)
    co.code.append(Label(self._generateFunctionRetLabel()))

    for i in range(numfloatregs, 0, -1):
      co.code.append(Addi("sp", "4", "sp"))
      co.code.append(Flw("f" + str(i), "sp", "0"))

    for i in range(numintregs, 0, -1):
      co.code.append(Addi("sp", "4", "sp"))
      co.code.append(Lw("t" + str(i), "sp", "0"))

    co.code.append(Mv("fp", "sp"))
    co.code.append(Lw("fp", "fp", "0"))
    co.code.append(Ret())

    return co

	

  def postprocessFunctionListNode(self, node: FunctionListNode, functions: List[CodeObject]) -> CodeObject:
    '''
    Generate code for the list of functions. This is the "top level" code generation function
    Step 1: Set fp to point to sp
    Step 2: Insert a JR to main
    Step 3: Insert a HALT
    Step 4: Include all the code of the functions
    '''

    co = CodeObject()

    co.code.append(Mv("sp", "fp"))
    co.code.append(Jr(self._generateFunctionEntryLabel("main")))
    co.code.append(Halt())
    co.code.append(Blank())

    # Add code for each of the functions
    for c in functions:
      co.code.extend(c.code)
      co.code.append(Blank())
    
    return co


  def postprocessCallNode(self, node: CallNode, args: List[CodeObject]) -> CodeObject:
    '''
    Responsible for handling when we actually make a function call, for example, something like a = foo(b)
    The call node would be the foo(b) call.
    Step 1: For each argument, insert rvalified code object and push result to stack
    Step 2: Allocate space for return value (what if there isn't one?)
    Step 3: Push ra to stack
    Step 4: JR to function
    Step 5: Pop ra back from stack
    Step 6: Pop return value into fresh temporary
    Step 7: Remove arguments from stack (move sp up, no need to keep these values)
    '''
    co = CodeObject()

    for arg in args:
      if arg.lval:
        arg = self.rvalify(arg)
      co.code.extend(arg.code)

      if arg.type is Scope.Type.FLOAT:
        co.code.append(Fsw(arg.temp, "sp", "0"))
      else:
        co.code.append(Sw(arg.temp, "sp", "0"))
      co.code.append(Addi("sp", "-4", "sp"))

    if node.getType() is not Scope.Type.VOID:
      co.code.append(Addi("sp", "-4", "sp"))

    co.code.append(Sw("ra", "sp", "0"))
    co.code.append(Addi("sp", "-4", "sp"))
    co.code.append(Jr(self._generateFunctionEntryLabel(node.getFuncName())))

    co.code.append(Addi("sp", "4", "sp"))
    co.code.append(Lw("ra", "sp", "0"))

    if node.getType() is Scope.Type.INT:
      co.temp = self.generateTemp(Scope.Type.INT)
      co.code.append(Addi("sp", "4", "sp"))
      co.code.append(Lw(co.temp, "sp", "0"))
      co.lval = False
      co.type = Scope.Type.INT

    elif node.getType() is Scope.Type.FLOAT:
      co.temp = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(Addi("sp", "4", "sp"))
      co.code.append(Flw(co.temp, "sp", "0"))
      co.lval = False
      co.type = Scope.Type.FLOAT

    elif node.getType() is Scope.Type.VOID:
      co.lval = False
      co.temp = None
      co.type = Scope.Type.VOID

    else:
      raise Exception("Bad return type in the call node")

    if len(args) > 0:
      co.code.append(Addi("sp", str(4 * len(args)), "sp"))

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

    symbol = lco.getSTE()
    address = symbol.addressToString()

    if lco.type is Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)

      if symbol.isLocal():
        co.code.append(Lw(temp, "fp", address))
      else:
        addressco = self.generateAddrFromVariable(lco)
        co.code.extend(addressco)
        co.code.append(Lw(temp, addressco.getLast().getDest(), "0"))

    elif lco.type is Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.FLOAT)

      if symbol.isLocal():
        co.code.append(Flw(temp, "fp", address))
      else:
        addressco = self.generateAddrFromVariable(lco)
        co.code.extend(addressco)
        co.code.append(Flw(temp, addressco.getLast().getDest(), "0"))


    else:
      raise Exception("Bad type in rvalify!")

    co.type = lco.type
    co.lval = False
    co.temp = temp


    return co
 


  def generateAddrFromVariable(self, lco: CodeObject) -> str:
    assert(lco.isVar() is True)

   
    il = InstructionList()
    symbol = lco.getSTE()
    address = symbol.addressToString()
    temp = self.generateTemp(Scope.Type.INT)

    if symbol.isLocal():
      il.append(Addi("fp", address, temp))
    else:
      il.append(La(temp, address))

    return il


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
    return "out_"+str(num)
  


  
  def _generateFunctionEntryLabel(self, func = None) -> str:
    if func is None:
      return "func_entry_" + self.currFunc
    else:
      return "func_entry_" + func
    
  def _generateFunctionCodeLabel(self, func = None) -> str:
    if func is None:
      return "func_code_" + self.currFunc
    else:
      return "func_code_" + func  


  def _generateFunctionRetLabel(self) -> str:
    return "func_ret_" + self.currFunc