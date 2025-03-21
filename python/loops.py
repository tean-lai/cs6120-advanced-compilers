from blocks import BasicBlocks
from dataflow import dataflow, Reaching, dataflow_dce


def find_natural_loops(bb):
    natural_loops = {}

    for b in range(bb.n):
        for a in bb.pred[b]:  # a -> b
            if b in bb.dom[a]:  # b dominates a
                natural_loops[(a, b)] = set()

    for a, b in natural_loops:
        q = [a, b]
        while q:
            n = q.pop()
            if n in natural_loops[(a, b)]:
                continue
            natural_loops[(a, b)].add(n)
            if n == b:
                continue
            for c in bb.pred[n]:
                q.append(c)

    return natural_loops


def try_fresh(labels, attempt=None):
    # labels = set()
    # for b in bb.blocks:
    #     if len(b) == 0:
    #         continue
    #     if "label" not in b[0]:
    #         continue
    #     labels.add(b[0]["label"])

    if attempt is None or attempt in labels:
        for i in range(len(labels) + 1):
            if str(i) not in labels:
                return str(i)
    else:
        return attempt


def licm(bb, loop, in_reach, out_reach, a, b, labels):
    changing = True
    loop_inv = {a: set() for a in loop}
    loop_vars = set()
    for a in loop:
        for instr in bb.blocks[a]:
            if "dest" in instr:
                loop_vars.add(instr["dest"])

    while changing:
        changing = False
        for a in loop:
            for instr in bb.blocks[a]:
                if "dest" not in instr:
                    continue
                if instr.get("op", None) in ["call"]:
                    continue
                dest = instr["dest"]
                for arg in instr.get("args", []):
                    if arg in loop_vars and arg not in loop_inv[a]:
                        break
                else:
                    if dest not in loop_inv[a]:
                        changing = True
                        print(f"marking {dest} something as LI!", file=sys.stderr)
                        loop_inv[a].add(dest)

    assert "label" in bb.blocks[b][0]

    old_header = bb.blocks[b][0]["label"]
    preheader = [{"label": old_header}]

    new_header = try_fresh(labels, old_header + ".header")
    bb.blocks[b][0]["label"] = new_header
    labels.add(new_header)

    print("loop:", loop, file=sys.stderr)
    for a in loop:
        new_instrs = []
        for instr in bb.blocks[a]:
            if instr.get("dest", None) in loop_inv[a]:
                preheader.append(instr)
                print("preheader:", instr, file=sys.stderr)
            else:
                new_instrs.append(instr)
                if instr.get("op", None) in ["jmp", "br"]:
                    print("labels:", instr.get("labels", []), file=sys.stderr)
                    for i in range(len(instr.get("labels", []))):
                        if instr["labels"][i] == old_header:
                            instr["labels"][i] = new_header
        bb.blocks[a] = new_instrs

    bb.blocks[b] = preheader + bb.blocks[b]


if __name__ == "__main__":
    import sys, json

    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)
        # bb.to_ssa()
        # dataflow_dce(bb)

        print("Basic Blocks:", file=sys.stderr)

        print("succ:", bb.succ, file=sys.stderr)
        print("pred:", bb.pred, file=sys.stderr)

        natural_loops = find_natural_loops(bb)
        print("natural loops:", natural_loops, file=sys.stderr)

        in_reaching, out_reaching = dataflow(bb, Reaching)

        labels = set()
        for b in bb.blocks:
            if len(b) == 0:
                continue
            if "label" not in b[0]:
                continue
            labels.add(b[0]["label"])

        for a, b in natural_loops:
            licm(bb, natural_loops[(a, b)], in_reaching, out_reaching, a, b, labels)

        # bb.from_ssa()
        # dataflow_dce(bb)
        prog["functions"][i] = bb.to_func()

        # print("in_reaching:", in_reaching)
        # print("out_reaching:", out_reaching)

        print(file=sys.stderr)

    print(json.dumps(prog))
