from blocks import BasicBlocks


if __name__ == "__main__":
    import json, sys

    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)
        # for b in bb.blocks:
        #     # print(b)
        #     [print(i) for i in b]
        #     print()
        # print()

        # print("==== CONVERT TO SSA ==== ")
        # print(bb.n)
        # print(bb.blocks)
        bb.to_ssa()
        # for b in bb.blocks:
        #     # print(b)
        #     [print(i) for i in b]
        #     print()

        prog["functions"][i] = bb.to_func()

    print(json.dumps(prog))
