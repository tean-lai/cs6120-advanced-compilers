from blocks import BasicBlocks


if __name__ == "__main__":
    import json, sys

    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)
        bb.to_ssa()
        bb.from_ssa()

        prog["functions"][i] = bb.to_func()

    print(json.dumps(prog))
