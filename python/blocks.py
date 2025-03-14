from copy import deepcopy
from collections import deque

debug_mode = False


def _get_used_labels(instrs: list[dict]):
    used = set()
    for instr in instrs:
        if instr.get("op", None) in ["jmp", "br"]:
            used.update(instr["labels"])
    return used


def _gen_reverse_postorder(adj, i):

    visited = [False] * len(adj)
    def dfs(i, path) -> list:
        if visited[i]:
            return path

        visited[i] = True

        for j in adj[i]:
            dfs(j, path)

        path.append(i)

        return path

    path = []
    for i in range(len(adj)):
        if i not in visited:
            path.extend(dfs(i, []))

    return reversed(path)


class BasicBlocks:
    """
    Basic Blocks!

    self.blocks is list of instructions chunked up in blocks. it preserves its
    order.

    self.succ is cfg, self.pred contains the predecessors of the each node in
    cfg. both self.succ and self.pred is in the form of an adjacency list.

    self.succ may look like [[1], [0, 1]], which means block 0 flows to block 1,
    and block 1 flows to block 0 and 1.

    self.dom is the dominance frontier
    """

    def __init__(self, func):
        self._func = deepcopy(func)
        self.fun_args = [i["name"] for i in func["args"]]
        self.instrs = self._func["instrs"]
        self.blocks = []
        self.succ = []
        self.pred = []
        self._gen_blocks()
        self.n = len(self.blocks)
        assert len(self.blocks) == len(self.succ) == len(self.pred)

        self.dom = self._gen_dom_graph()
        # self.dom_frontier = self._gen_dom_frontier()
        self.dom_tree = self._gen_dom_tree()

    # def _gen_dom_graph(self):
    #     succ, pred = self.succ, self.pred
    #     assert len(succ) == len(pred)
    #     dom = [{i} for i in range(self.n)]
    #     changing = True
    #     while changing:
    #         for v in range(self.n):
    #             if v == 0:
    #                 continue
    #             pred_dom = [dom[p] for p in pred[v]]
    #             if pred_dom:
    #                 update = pred_dom[0].copy()
    #                 for i in range(1, len(pred_dom))


    def _gen_dom_graph(self):
        succ, pred = self.succ, self.pred
        assert len(succ) == len(pred)
        dom = [{i} for i in range(self.n)]
        changing = True
        while changing:
            changing = False
            for v in _gen_reverse_postorder(succ, 0):
                if v == 0:
                    continue

                pred_dom = [dom[p] for p in pred[v]]
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
        for c in range(self.n):
            if self._is_strictly_dom(c, b) and self._is_strictly_dom(a, c):
                return False
        return self._is_strictly_dom(a, b)

    def _gen_dom_tree(self):

        edges = set()

        def dfs(i):
            children = []
            for j in range(self.n):
                if self._is_imm_dom(i, j):
                    edges.add((i, j))
                    assert (j, i) not in edges, "not a tree, has cycle"
                    children.append(dfs(j))
            return (i, children)

        return dfs(0)

    def compute_dom_frontier(self, a: int):
        """
        a is the index that the block corresponds to
        """
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
            if (
                last.get("op", None) not in ["jmp", "br", "ret"]
                and i < len(self.succ) - 1
            ):
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

    def to_ssa(self):
        count = {}

        dfs = [self.compute_dom_frontier(i) for i in range(self.n)]
        # gets = [set() for _ in range(self.n)]  # gets[i] is a set of variables we need get "get" at block i
        sets = [{} for _ in range(self.n)]  # sets[i]["name"] = "name.3" means we need to set "name" name.3
        phi_nodes = [{} for _ in range(self.n)]
        # in_df = [False] * self.n

        for i, b in enumerate(self.blocks):

            sets = {}
            for instr in b:
                if "dest" not in instr:
                    continue

                dest = instr["dest"]
                count[dest] = count.get(dest, -1) + 1
                instr["dest"] += "." + str(count[dest])
                sets[dest] = instr["dest"]

            for j in dfs[i]:
                # in_df[j] = True
                for dest in sets:
                    if dest not in phi_nodes[i]:
                        count[dest] = count.get(dest, -1) + 1
                        phi_nodes[i][dest] = { "dest": dest + "." + str(count[dest]), "args": [] }
                    phi_nodes[i][dest]["args"].append(sets[dest])
                    b.append({"op": "set", "args": [phi_nodes[i][dest]["dest"], sets[dest]]})

        for i, b in enumerate(self.blocks):
            get_instrs = []
            defined = set()
            for dest in phi_nodes[i]:
                get_dest = phi_nodes[i][dest]["dest"]
                if get_dest not in defined:
                    get_instrs.append({"op": "set", "args": [get_dest, "undefundefundefundefundef"]})
                get_instrs.append({"dest": get_dest, "op": "get"})
                defined.add(get_dest)
            for instr in b:
                if "dest" in instr:
                    defined.add(instr["dest"])

            self.blocks[i] = get_instrs + self.blocks[i]
            self.blocks[i].insert(0, {"dest": "undefundefundefundefundef", "op": "undef"})

        if debug_mode:
            print(phi_nodes)
            for i in range(self.n):
                for j in phi_nodes[i]:
                    print(phi_nodes[i][j]["dest"])
                    # print(j, j["dest"])


        def find(arg, var_stack):
            for d in reversed(var_stack):
                # print(d)
                if arg in d:
                    return d[arg]
            assert False, f"{arg} not found in var_stack"
            # return arg


        def trim(s):
            for i in range(len(s) - 1, -1, -1):
                if s[i] == ".":
                    return s[:i]
            if s in ["undefundefundefundefundef"] + [self.fun_args]:
                return s
            assert False, f"failed trim on {s}"

        visited = set()
        def rename_args(dt, var_stack=None):
            i = dt[0]

            if i in visited:
                return

            if var_stack is None:
                var_stack = []

            if debug_mode:
                print("var_stack: ", var_stack)

            var_stack.append({})
            for instr in self.blocks[i]:
                if "args" in instr:
                    if instr.get("op", None) == "set":
                        continue
                    instr["args"] = [find(arg, var_stack) for arg in instr["args"]]
                        # for instr in self.blocks[i]:
                        #     print(instr)
                        # assert False
                if "dest" in instr:
                    var_stack[-1][trim(instr["dest"])] = instr["dest"]
            if debug_mode:
                print("var_stack: ", var_stack)

            for child in dt[1]:
                rename_args(child, var_stack)
            var_stack.pop()

        # print(self._func["args"])
        var_stack = [None]
        # print(self.fun_args)
        var_stack[-1] = {i: i for i in self.fun_args}

        # for i in self._func["args"]:
        #     var_stack[-1][i["name"]] = i["name"]
        # print(var_stack)
        rename_args(self.dom_tree, var_stack)


    def from_ssa(self):
        for i, b in enumerate(self.blocks):
            self.blocks[i] = [instr for instr in b if instr.get("op", None) != "get"]
            assert all("get" not in instr for instr in b)

            # print("hello:", self.blocks[i])
            # print(self.blocks[i])
            for instr in self.blocks[i]:
                if "op" not in instr:
                    continue
                if instr["op"] == "set":
                    instr["op"] = "id"
                    instr["dest"] = instr["args"][0]
                    instr["args"] = [instr["args"][1]]


    def to_ssa_archive(self):
        count = {}
        # gets[3]["name"] = "name.v1" means

        dfs = [self.compute_dom_frontier(i) for i in range(self.n)]  # dominance frontiers

        for i, b in enumerate(self.blocks):
            df = dfs[i]

            for instr in b:
                if "dest" not in instr:
                    continue

                dest = instr["dest"]

                count[dest] = count.get(dest, -1) + 1
                instr["dest"] += "." + str(count[dest])

                # if dest not in sets[i]:
                #     sets[i][dest] = instr["dest"]
                sets[i][dest] = instr["dest"]

                for j in df:
                    if dest not in gets[j]:
                        count[dest] += 1
                        gets[j][dest] = dest + "." + str(count[dest])

        # for i in range(self.n):
        #     print(f"block {i}")
        #     print(f"  df {dfs[i]}")
        #     print(f"  gets = {gets[i]}")
        #     print(f"  succ = {self.succ[i]}")
        #     print(f"  pred = {self.pred[i]}")
        #     print(f"  instrs = ")
        #     for j in self.blocks[i]:
        #         print(f"    {j}")
        # print(self.blocks[i])

        def trim(s):
            for i in range(len(s) - 1, -1, -1):
                if s[i] == ".":
                    return s[:i]
            assert False, "failed trim"

        q = deque([0])
        visited = [False] * self.n
        # for i, b in enumerate(self.blocks):
        env = {x["name"]: x["name"] for x in self._func["args"]}
        while q:
            i = q.popleft()
            if visited[i]:
                continue
            visited[i] = True

            for j in self.succ[i]:
                q.append(j)

            b = self.blocks[i]

            df = dfs[i]

            new_instrs = []
            for k, v in gets[i].items():
                new_instrs.append({"dest": v, "op": "get"})
                env[k] = v

            # print(env)

            for instr in b:
                new_instrs.append(instr)
                if "args" in instr:
                    instr["args"] = [env[x] for x in instr["args"]]

                if "dest" not in instr:
                    continue

                dest = instr["dest"]
                orig = trim(dest)
                env[orig] = dest
                # print(orig, dest)

                if sets[i][orig] == dest:
                    for j in df:
                        new_instrs.append({"op": "set", "args": [gets[j][orig], dest]})

            self.blocks[i] = new_instrs

    # def from_ssa(self):
    #     pass


if __name__ == "__main__":
    import json, sys

    prog = json.load(sys.stdin)

    for i, func in enumerate(prog["functions"]):
        bb = BasicBlocks(func)
        print("succ:", bb.succ)
        print("pred:", bb.pred)
        print("dom:", bb.dom)
        for j, b in enumerate(bb.blocks):
            print(f"block {j}")
            for instr in b:
                print(f"  {instr}")

        # print("dom tree:", bb.dom_tree)
        # bb.pp_dom_tree()
        print(bb.dom_tree)
        dfs = [bb.compute_dom_frontier(i) for i in range(bb.n)]
        print(dfs)
        print()
        # bb.debug_print()
