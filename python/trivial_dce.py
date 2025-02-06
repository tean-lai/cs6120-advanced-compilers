import json
import sys

from blocks import *

if __name__ == "__main__":
    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        blocks = BasicBlocks(func)

        print("new function:")
        blocks.debug_print()
        print()

    print(json.dumps(prog))
