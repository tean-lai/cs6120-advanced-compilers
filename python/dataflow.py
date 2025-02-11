import argparse
import json
import sys
from collections import deque

from blocks import BasicBlocks
from bril_defense import *


class _InitVar:
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

    def to_string(prop):
        if not prop:
            return "[]"
        return str(sorted(list(prop)))


def dataflow(blocks: BasicBlocks, property):
    l = len(blocks.blocks)
    in_prop = [None] * l
    in_prop[0] = property.init()
    out_prop = [property.init() for _ in range(l)]

    worklist = deque([i for i in range(l)])
    while worklist:
        b = worklist.popleft()
        in_prop[b] = property.merge(out_prop[p] for p in blocks.pred[b])
        out_prop[b], changed = property.transfer(blocks.blocks[b], in_prop[b])
        if changed:
            worklist += blocks.succ[b]

    for i in range(len(blocks.blocks)):
        b = blocks.blocks[i]
        if not b:
            continue
        if "label" in b[0]:
            print(f"  .{b[0]["label"]}:")

        print(f"    in:  {property.to_string(in_prop[i])}")
        print(f"    out: {property.to_string(out_prop[i])}")


if __name__ == "__main__":
    global debug_mode
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    debug_mode = args.debug

    prog = json.load(sys.stdin)
    init_var = _InitVar

    for func in prog["functions"]:
        blocks = BasicBlocks(func)
        print(f"func {func["name"]}:")
        dataflow(blocks, init_var)
        print()

    # print(json.dumps(prog))
