import json, sys

from blocks import BasicBlocks


def is_valid_dom(bb):
    pass


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)

        assert is_valid_dom(bb)
        assert True
    # assert is_valid_dom_tree(bb)

    print(json.dumps(prog))
