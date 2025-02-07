import json
import sys
from collections import defaultdict, deque

from blocks import *


def _one_pass(instrs):
    unused_vars = set()
    output = []
    changed = False
    for i in range(len(instrs) - 1, -1, -1):
        # print("loop")
        # print(unused_vars)
        instr = instrs[i]

        if "dest" in instr:
            dest = instr["dest"]
            if dest in unused_vars:
                changed = True
                continue
            else:
                unused_vars.add(dest)
        # print(unused_vars)

        output.append(instr)

        for arg in instr.get("args", ()):
            if arg in unused_vars:
                unused_vars.remove(arg)
        # print(unused_vars)
        # print()
        # print(used_vars)
    # print()

    return output[::-1], changed


def local_dce(instrs):
    changed = True
    limit = float("inf")
    while changed and limit:
        instrs, changed = _one_pass(instrs)
        limit -= 1
    return instrs


def global_dce(instrs):
    used = set()
    for _, instr in enumerate(instrs):
        for arg in instr.get("args", ()):
            used.add(arg)

    output = []
    for instr in instrs:
        if "dest" in instr and instr["dest"] not in used:
            continue
        output.append(instr)
    return output


def global_dce2(instrs):
    def_loc = defaultdict(set)
    use_loc = defaultdict(set)
    for i, instr in enumerate(instrs):
        if "dest" in instr:
            def_loc[instr["dest"]].add(i)
        for arg in instr.get("args", ()):
            use_loc[arg].add(i)

        # print(unused_vars)
    queue = deque()
    for i, instr in enumerate(instrs):
        if "dest" in instr and not use_loc[instr["dest"]]:
            queue.append(i)

    removed = set()
    while queue:
        j = queue.popleft()
        instr = instrs[j]
        # print("hi", len(queue), instr)
        if "dest" not in instrs[j]:
            continue

        removed.add(j)
        if instr["op"] == "const":
            continue

        var = instrs[j]["dest"]
        used = False
        # assert False, type(use_loc)
        for i in use_loc[var]:
            if i not in removed:
                used = True
        if used:
            continue

        for i in def_loc[var]:
            for arg in instr.get("args", ()):
                queue.append(i)
    output = []
    for i, instr in enumerate(instrs):
        if i not in removed:
            output.append(instr)
    return output


if __name__ == "__main__":
    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):

        blocks = BasicBlocks(func)
        instrs = []
        for block in blocks.blocks:
            instrs += local_dce(block)

        func["instrs"] = global_dce(instrs)

    print(json.dumps(prog))
