import argparse
import json
import sys
from collections import deque
from typing import Iterable

from blocks import BasicBlocks

uop = ["not", "id"]
binop = ["add", "sub", "mul", "div", "and", "or", "eq", "lt", "gt", "le", "ge"]


class _AbstractProp:

    def init():
        raise "Init not implemented"

    def merge(sets):
        raise "Merge not implemented"

    def transfer(b, iter):
        raise "Transfer not implemented"

    def is_forward() -> bool:
        raise "IDK"

    def to_string(prop) -> str:
        return prop


class InitVar(_AbstractProp):

    def init():
        return set()

    def merge(sets):
        sets = list(sets)

        if not sets:
            return set()
        assert len(sets) > 0

        acc: set = sets[0]
        for i in sets:
            acc.intersection_update(i)
        return acc

    def transfer(b, set1: set):
        set2 = set1.copy()
        for instr in b:
            if "dest" in instr:
                set2.add(instr["dest"])
        return set2, set1 == set2

    def is_forward():
        return True

    def to_string(prop):
        if not prop:
            return "[]"
        return str(sorted(list(prop)))


class ConstProp(_AbstractProp):

    def init():
        return {}

    def merge(props):
        out_prop = {}
        for prop in props:
            for i in prop:
                if i not in out_prop:
                    out_prop[i] = prop[i]
                else:
                    if out_prop[i] != prop[i]:
                        out_prop[i] = None
        return out_prop

    def transfer(b, prop1: dict):
        out_prop = prop1.copy()
        for instr in b:
            # print(out_prop)

            if "dest" not in instr:
                continue
            dest = instr["dest"]
            op = instr["op"]

            if op == "const":
                value = instr["value"]
                out_prop[dest] = value

            elif op in uop:
                a = instr["args"][0]
                a = out_prop.get(a, None)

                if a is None:
                    out_prop[dest] = None
                    continue

                if op == "not":
                    out_prop[dest] = not a
                elif op == "id":
                    out_prop[dest] = a
                else:
                    raise "????"

            elif op in binop:
                a, b = instr["args"]
                a, b = out_prop.get(a, None), out_prop.get(b, None)

                if a is None or b is None:
                    out_prop[dest] = None
                    continue

                if op == "add":
                    # print("adding", dest, a, b)
                    out_prop[dest] = a + b
                elif op == "sub":
                    out_prop[dest] = a - b
                elif op == "mul":
                    out_prop[dest] = a * b
                elif op == "div":
                    out_prop[dest] = a // b
                elif op == "and":
                    out_prop[dest] = a and b
                elif op == "or":
                    out_prop[dest] = a or b
                elif op == "eq":
                    out_prop[dest] = a == b
                elif op == "lt":
                    out_prop[dest] = a < b
                else:
                    raise "not implemented"

        changed = False
        for i in prop1:
            if i in out_prop[i] != prop1[i]:
                changed = True
                break
        return out_prop, changed

    def is_forward():
        return True

    def to_string(prop):
        prop = prop.copy()
        for i in prop:
            if prop[i] is None:
                prop[i] = "??"
        return str(prop)


class IntAnalysis(_AbstractProp):

    def init():
        return {}

    def merge(b, props):
        pass

    def transfer(b, prop):
        pass

    def to_string(prop):
        return str(prop)


class Liveness(_AbstractProp):

    def init() -> set:
        return set()

    def merge(props: Iterable[set]):
        out = set()
        for prop in props:
            out.update(prop)
        return out

    def transfer(b, prop: set):
        out = prop.copy()
        for i in range(len(b) - 1, -1, -1):
            instr = b[i]
            # print("instr:", instr)
            # print("old:", out)
            if "dest" in instr:
                out.difference_update({instr["dest"]})
            if "args" in instr:
                out.update(instr["args"])
            # print("new:", out)
            # print()
        return out, out == prop

    def is_forward():
        return False

    def to_string(p):
        if not p:
            return "{}"
        return str(p)


def dataflow(blocks: BasicBlocks, property: _AbstractProp):
    l = len(blocks.blocks)
    in_prop = [None] * l
    in_prop[0] = property.init()
    out_prop = [property.init() for _ in range(l)]
    pred, succ = blocks.pred, blocks.succ

    if not property.is_forward():
        in_prop, out_prop = out_prop, in_prop
        pred, succ = succ, pred

    worklist = deque([i for i in range(l)])
    while worklist:
        b = worklist.popleft()
        in_prop[b] = property.merge(out_prop[p] for p in blocks.pred[b])
        out_prop[b], changed = property.transfer(blocks.blocks[b], in_prop[b])
        if changed:
            worklist += blocks.succ[b]

    if not property.is_forward():
        in_prop, out_prop = out_prop, in_prop
        pred, succ = succ, pred

    if __name__ == "__main__":
        for i in range(len(blocks.blocks)):
            b = blocks.blocks[i]
            if not b:
                continue
            if "label" in b[0]:
                print(f"  .{b[0]["label"]}:")

            print(f"    in:  {property.to_string(in_prop[i])}")
            print(f"    out: {property.to_string(out_prop[i])}")

    return in_prop, out_prop


if __name__ == "__main__":
    # global debug_mode
    # parser = argparse.ArgumentParser()
    # parser.add_argument("-d", "--debug", action="store_true")
    # args = parser.parse_args()
    # debug_mode = args.debug

    prog = json.load(sys.stdin)
    # init_var = InitVar
    # init_var = ConstProp
    # init_var = IntAnalysis
    init_var = Liveness

    for func in prog["functions"]:
        blocks = BasicBlocks(func)
        print(f"func {func["name"]}:")
        dataflow(blocks, init_var)
        print()

    # print(json.dumps(prog))
