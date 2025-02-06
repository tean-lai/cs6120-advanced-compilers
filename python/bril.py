import json
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, assert_never
from enum import Enum, auto

binop = ""
# class Type(Enum):
#     INT: str = "int"
#     BOOL: str = "bool"


# class Op(Enum):
#     ADD: str = "add"
#     MUL: str = "mul"
#     SUB: str = "sub"
#     DIV: str = "div"
#     EQ = "eq"
#     LT = "lt"
#     GT = "gt"
#     LE = "le"
#     GE = "ge"
#     NOT = "not"
#     AND = "and"
#     OR = "or"
#     JMP = "jmp"
#     BR = "br"
#     CALL = "call"
#     RET = "ret"
#     ID = "id"
#     PRINT = "print"
#     NOP = "nop"


# @dataclass
# class Label:
#     label: str


# @dataclass
# class Instruction:
#     op: str
#     dest: Optional[str]
#     type: Optional[Type]
#     args: Optional[List[str]]
#     funcs: Optional[List[str]]
#     labels: Optional[List[str]]


# Literal = int | str


# @dataclass
# class Constant(Instruction):
#     op: Op
#     dest: str
#     type: Type
#     value: Literal


# class Value(Instruction):
#     op: Op
#     dest: str
#     type: Type


# @dataclass
# class FunctionArg:
#     name: str
#     type: Type


# @dataclass
# class Function:
#     name: str
#     args: Optional[List[FunctionArg]]
#     type: Optional[Type]
#     instrs: List[Instruction | Label]


# class Bril:
#     functions: List[Function]


# def from_json(d):
#     assert False, "todo"


# def to_json(s):
#     assert False, "todo"
