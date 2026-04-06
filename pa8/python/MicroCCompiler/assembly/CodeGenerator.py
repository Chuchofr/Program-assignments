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
    self.intRegCount = 0
    self.floatRegCount = 0
    self.intTempPrefix = 't'
    self.floatTempPrefix = 'f'
    self.numCtrlStructs = 0

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

    co = CodeObject()

    newcode = CodeObject()

    optype = str(node.op)

    if left.lval == True:
      left = self.rvalify(left)
    co.code.extend(left.code)

    if right.lval == True:
      right = self.rvalify(right)
    co.code.extend(right.code)

    if left.type != right.type:
      print("Incompatible types in binary operation!\n")

    if left.type == Scope.Type.INT:
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

    co.code.append(newcode)
    co.lval = False
    co.temp = newtemp
    co.type = left.type

    return co



  def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:

    co = CodeObject()  # Step 0

    if expr.lval:
      expr = self.rvalify(expr)

    co.code.extend(expr.code)

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

    address = self.generateAddrFromVariable(left)
    temp = self.generateTemp(Scope.Type.INT)
    co.code.append(La(temp, address))

    if right.lval:
      right = self.rvalify(right)
    co.code.extend(right.code)

    if left.type is Scope.Type.INT:
      co.code.append(Sw(right.temp, temp, '0'))
    elif left.type is Scope.Type.FLOAT:
      co.code.append(Fsw(right.temp, temp, '0'))
    else:
      raise Exception("Bad type in assign node")

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

    if var.type is Scope.Type.INT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(GetI(temp))
      address = self.generateAddrFromVariable(var)
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp2, address))
      co.code.append(Sw(temp, temp2, '0'))
      
    elif var.type is Scope.Type.FLOAT:
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(GetF(temp))
      address = self.generateAddrFromVariable(var)
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp2, address))
      co.code.append(Fsw(temp, temp2, '0'))
      
    else: 
      raise Exception("Bad type in read Node!")

    return co


  def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:

    co = CodeObject()

    if expr.type is Scope.Type.STRING:
      address = self.generateAddrFromVariable(expr)
      temp = self.generateTemp(Scope.Type.INT)
      co.code.append(La(temp, address))
      co.code.append(PutS(temp))

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
    temp1 = self.generateTemp(Scope.Type.INT)
    co.code.append(La(temp1, address, '0'))

    if lco.type is Scope.Type.INT:
      temp2 = self.generateTemp(Scope.Type.INT)
      co.code.append(Lw(temp2, address, '0'))

    elif lco.type is Scope.Type.FLOAT:
      temp2 = self.generateTemp(Scope.Type.FLOAT)
      co.code.append(Flw(temp2, temp1, '0'))

    else:
      raise Exception("Bad type rvalify!")
    
    co.type = lco.type 
    co.lval = False
    co.temp = temp2


    return co






  def generateAddrFromVariable(self, lco: CodeObject) -> CodeObject:

    assert(lco.isVar() is True)


    symbol = lco.getSTE()
    address = str(symbol.getAddress())


    return address
  
def _incrnumCtrlStruct(self):
  self.numCtrlStructs += 1

def _getnumCtrlStruct(self) -> int:
  return self.numCtrlStructs


def _generateThenLabel(self, num: int) -> str:
  return "then" + str(num)

def generateElseLabel(self, num: int) -> str:
  return "else" + str(num)

def generateLoopLabel(self, num: int) -> str:
  return "loop" + str(num)

def generateDoneLabel(self, num: int) -> str:
  return "done" + str(num)