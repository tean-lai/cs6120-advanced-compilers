import json, sys
from collections import deque

from blocks import BasicBlocks


def has_valid_dom(bb):
    """
    checks if the basic blocks' dominator graph is valid.
    """

    def is_dom(a, b):
        """checks if a dominates b"""
        if b == len(bb.dom) - 1:
            return True

        q = deque([a])
        visited = set()
        while q:
            curr = q.popleft()
            if curr in visited:
                continue

            visited.add(curr)
            if curr == a:
                continue

            if curr == len(bb.dom) - 1:
                assert False, len(bb.dom) - 1

            for next in bb.succ[curr]:
                q.add(next)
        return True

    for a in range(len(bb.dom)):
        for b in bb.dom[a]:
            if not is_dom(b, a):
                return False

    return True


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)

        assert has_valid_dom(bb)

    print(json.dumps(prog))
