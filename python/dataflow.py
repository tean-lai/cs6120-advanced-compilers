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
        return set2, set1 == set2, []

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

    def transfer(b: list[dict], prop1: dict, optimize=False):

        new_b = []
        out_prop = prop1.copy()
        for instr in b:

            if optimize:
                new_b.append(instr.copy())

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

                if optimize:
                    new_b[-1]["op"] = "const"
                    new_b[-1].pop("args")
                    new_b[-1]["value"] = out_prop[dest]

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

                if optimize:
                    new_b[-1]["op"] = "const"
                    new_b[-1].pop("args")
                    new_b[-1]["value"] = out_prop[dest]

        return out_prop, new_b

    def is_equal(prop1, prop2):
        return prop1 == prop2

    def is_forward():
        return True

    def to_string(prop):
        prop = prop.copy()
        for i in prop:
            if prop[i] is None:
                prop[i] = "??"
        return str(prop)


class Interval(_AbstractProp):

    def init():
        return {}

    def merge(b, props):
        pass

    def transfer(b, prop):
        pass

    def to_string(prop):
        return str(prop)


class Reaching(_AbstractProp):

    def init():
        return {}

    def merge(b, props):
        pass

    def transfer(b, prop):
        pass

    def is_forward(b, prop):
        return True


class Liveness(_AbstractProp):

    def init() -> set:
        return set()

    def merge(props: Iterable[set]):
        out = set()
        props = list(props)
        for prop in props:
            assert prop is not None, props
            out.update(prop)
        return out

    def transfer(b: list, prop: set, optimize=False):
        if optimize:
            keep = [True] * len(b)

        in_prop = prop.copy()
        for i in range(len(b) - 1, -1, -1):

            instr = b[i]

            if "dest" in instr:
                dest = instr["dest"]
                if dest in in_prop:
                    in_prop.remove(dest)
                elif optimize:
                    keep[i] = False
                    continue

            if "args" in instr:
                for arg in instr["args"]:
                    in_prop.add(arg)

                # in_prop.update(instr["args"])

        if optimize:
            new_b = [b[i] for i in range(len(b)) if keep[i]]
        else:
            new_b = []
        return in_prop, new_b

    def is_forward():
        return False

    def is_equal(prop1, prop2):
        return prop1 == prop2

    def to_string(p):
        if not p:
            return "{}"
        return str(p)


def df_interval(blocks):
    blocks, pred, succ = blocks.blocks, blocks.pred, blocks.succ
    l = len(blocks)
    prop = {}
    for i in succ:
        for j in succ[i]:
            prop[(i, j)] = Interval.init()
    pred, succ = blocks.pred, blocks.succ

    worklist = deque([i for i in range(l)])
    while worklist:
        b = worklist.popleft()
        in_prop = Interval.merge(prop)


def dataflow(blocks: BasicBlocks, property: _AbstractProp, optimize=False):
    l = len(blocks.blocks)
    in_prop = [None] * l
    in_prop[0] = property.init()
    out_prop = [property.init() for _ in range(l)]
    pred, succ = blocks.pred, blocks.succ

    if not property.is_forward():
        pred, succ = succ, pred

    worklist = deque([i for i in range(l - 1, -1, -1)])
    while worklist:
        i = worklist.popleft()
        in_prop[i] = property.merge(out_prop[j] for j in pred[i])
        new_out_prop, new_b = property.transfer(
            blocks.blocks[i], in_prop[i], optimize=optimize
        )

        if not property.is_equal(out_prop[i], new_out_prop):
            worklist += succ[i]
            out_prop[i] = new_out_prop

    if optimize:
        for i in range(l):
            _, new_b = property.transfer(blocks.blocks[i], in_prop[i], optimize=True)
            blocks.blocks[i] = new_b
            if debug_mode:
                print(new_b)

    if not property.is_forward():
        in_prop, out_prop = out_prop, in_prop

    if debug_mode:
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
    global debug_mode
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    debug_mode = args.debug

    prog = json.load(sys.stdin)

    optimize = True

    for i, func in enumerate(prog["functions"]):
        blocks = BasicBlocks(func)
        if debug_mode:
            print(f"func {func["name"]}:")
        # for j in blocks.blocks:
        #     print(j)
        # print()
        dataflow(blocks, ConstProp, optimize=optimize)
        # dataflow(blocks, Liveness, optimize=False)
        if debug_mode:
            print()

        if optimize:
            prog["functions"][i] = blocks.to_func()

    if not debug_mode:
        print(json.dumps(prog))
