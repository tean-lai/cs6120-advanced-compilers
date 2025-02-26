from copy import deepcopy


def _get_used_labels(instrs: list[dict]):
    used = set()
    for instr in instrs:
        if instr.get("op", None) in ["jmp", "br"]:
            used.update(instr["labels"])
    return used


def _gen_reverse_postorder(adj, i):

    def dfs(i, path=None, visited=None) -> list:
        if path is None:
            path = []

        if visited is None:
            visited = [False] * len(adj)

        if visited[i]:
            return

        visited[i] = True
        path.append(i)

        for j in adj[i]:
            dfs(j, path, visited)

        return path

    return reversed(dfs(i))


class BasicBlocks:

    def __init__(self, func):
        self._func = deepcopy(func)
        self.instrs = self._func["instrs"]
        self.blocks = []
        self.succ = []
        self.pred = []
        self._gen_blocks()

        self.dom = self._gen_dom_graph()
        # self.dom_frontier = self._gen_dom_frontier()
        self.dom_tree = self._gen_dom_tree()

    def _gen_dom_graph(self):
        succ, pred = self.succ, self.pred
        assert len(succ) == len(pred)
        dom = [{i} for i in range(len(succ))]
        # print("dom:", dom)
        changing = True
        while changing:
            changing = False
            for v in _gen_reverse_postorder(succ, 0):
                pred_dom = list(dom[p] for p in pred[v])
                if pred_dom:
                    update = pred_dom[0].copy()
                    for i in range(1, len(pred_dom)):
                        update.intersection_update(pred_dom[i])
                else:
                    update = set()

                for v2 in update:
                    if v2 not in dom[v]:
                        changing = True
                        dom[v].add(v2)
        return dom

    def _is_strictly_dom(self, a, b):
        return a in self.dom[b] and a != b

    def _is_imm_dom(self, a, b):
        for c in range(len(self.dom)):
            if self._is_strictly_dom(c, b) and self._is_strictly_dom(a, c):
                return False
        return self._is_strictly_dom(a, b)

    def _gen_dom_tree(self):

        def dfs(i):
            children = []
            for j in range(len(self.dom)):
                if self._is_imm_dom(i, j):
                    children.append(dfs(j))
            return (i, children)

        return dfs(0)

    def compute_dom_frontier(self, a):
        frontier = set()
        for b in range(len(self.dom)):
            if a == b:
                continue
            for pred in self.pred[b]:
                if a in self.dom[pred] and not self._is_strictly_dom(a, b):
                    frontier.add(b)
        return frontier

    def _add_block(self, block):
        self.blocks.append(block)
        self.succ.append(set())
        self.pred.append(set())

    def _gen_blocks(self):
        label_to_idx = {}
        used_labels = set()
        for instr in self.instrs:
            if "op" in instr and instr["op"] in ["jmp", "br"]:
                used_labels.update(instr["labels"])

        curr = []
        for instr in self.instrs:
            if "label" in instr and instr["label"] in used_labels:
                if curr:
                    self._add_block(curr)
                    curr = []
                label_to_idx[instr["label"]] = len(self.blocks)
                curr.append(instr)
            elif "op" in instr and instr["op"] in ["jmp", "br"]:
                curr.append(instr)
                i = len(self.blocks)

                self._add_block(curr)
                self.succ[i].update(instr["labels"])

                curr = []
            else:
                curr.append(instr)
        if curr:
            self._add_block(curr)

        for i in range(len(self.succ)):
            new = set()

            last = self.blocks[i][-1]
            if last.get("op", None) not in ["jmp", "br"] and i < len(self.succ) - 1:
                new.add(i + 1)
                self.pred[i + 1].add(i)

            for j in self.succ[i]:
                k = label_to_idx[j]
                new.add(k)
                self.pred[k].add(i)
            self.succ[i] = new

    def debug_print(self):
        import json

        print(json.dumps(self.blocks, indent=2))
        print(self.succ)
        print(self.pred)
        print()

    def pp_dom_tree(self):
        def dfs(tree, depth):
            padding = "  " * depth
            print(f"{padding}{tree[0]}")
            for child in tree[1]:
                dfs(child, depth + 1)

        dfs(self.dom_tree, 0)

    def to_func(self):
        new_instrs = []
        for block in self.blocks:
            for i in block:
                new_instrs.append(i)

        new_func = deepcopy(self._func)
        new_func["instrs"] = new_instrs
        return new_func


if __name__ == "__main__":
    import json, sys

    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)
        print(bb.succ)
        print(bb.pred)
        print("dom:", bb.dom)
        # print("dom tree:", bb.dom_tree)
        bb.pp_dom_tree()
        print()
        # bb.debug_print()
