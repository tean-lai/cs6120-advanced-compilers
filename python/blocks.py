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
        if not visited[i]:
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
        self.fun_args = []
        if "args" in func:
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

    def _gen_dom_graph(self):
        succ, pred = self.succ, self.pred
        assert len(succ) == len(pred)
        dom = [{i for i in range(self.n)} for i in range(self.n)]
        dom[0] = {0}
        changing = True
        while changing:
            changing = False
            # for v in _gen_reverse_postorder(succ, 0):
            for v in range(self.n):
                if v == 0:
                    continue

                if pred[v]:
                    update = set.intersection(*(dom[p] for p in pred[v]))
                else:
                    update = set()
                update.add(v)

                if update != dom[v]:
                    dom[v] = update
                    changing = True

                # for v2 in update
                #     if v2 not in dom[v]:
                #         changing = True
                #         dom[v].add(v2)
        return dom

    def _is_strictly_dom(self, a, b):
        return a in self.dom[b] and a != b

    def _is_imm_dom(self, a, b):
        for c in range(self.n):
            if self._is_strictly_dom(a, c) and self._is_strictly_dom(c, b):
                return False
        return self._is_strictly_dom(a, b)

    def _gen_dom_tree(self):
        edges = set()
        visited = set()

        def dfs(i):
            children = []
            if i in visited:
                assert False, "repeating"
            visited.add(i)
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
                # last.get("op", None) not in ["jmp", "br"]
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

    def get_unreachable_blocks(self):
        unreachable_blocks = []
        for i in range(1, self.n):
            if not self.pred[i]:
                unreachable_blocks.append(i)
        return unreachable_blocks

    def del_unreachable_blocks(self):
        unreachable_blocks = self.get_unreachable_blocks()

        for i in unreachable_blocks:
            new_instrs = []
            for instr in self.blocks[i]:
                if "label" in instr:
                    new_instrs.append(instr)
            self.blocks[i] = new_instrs

    def assert_reachable_in_dt(self):
        unreachable = self.get_unreachable_blocks()

        visited = set()
        def dfs(dt):
            if dt[0] in visited:
                return

            visited.add(dt[0])
            for j in dt[1]:
                dfs(j)
        dfs(self.dom_tree)

        for i in range(self.n):
            if i not in unreachable:
                assert i in visited, f"block {i} was not in dt"
            # else:
            #     print("succ:", self.pred)
            #     print("dom_tree:", self.dom_tree)
            #     assert i not in visited, f"block {i} is unreachable but is in dt"

    def to_ssa(self):
        return self._to_ssa2()

    def _to_ssa2(self):
        # unreachable = self.get_unreachable_blocks()
        # self.del_unreachable_blocks()


        # print(f"deleted {len(unreachable)}")

        """
        FIRST PASS. Find blocks where each var is assigned
        """
        defs = {}  # blocks where v is assigned
        # for v in self.fun_args:
        #     defs[v] = [0]
        for i, b in enumerate(self.blocks):
            for instr in b:
                if "dest" not in instr:
                    continue
                dest = instr["dest"]
                if dest not in defs:
                    defs[dest] = []

                if i not in defs[dest]:
                    defs[dest].append(i)

        """
        SECOND PASS: INSERT PHI NODES
        """
        df = [self.compute_dom_frontier(i) for i in range(self.n)]
        phi_nodes = [{} for _ in range(self.n)]

        counts = {}
        for v in defs:
            for d in defs[v]:
                for b in df[d]:
                    if v not in phi_nodes[b]:
                        counts[v] = 1 + counts.get(v, -1)
                        phi_nodes[b][v] = v + "." + str(counts[v])
                    if b not in defs[v]:
                        defs[v].append(b)

        """
        THIRD PASS: rename
        """
        visited = set()
        def rename(dt, stack):
            b = dt[0]
            if b in visited:
                assert False, "revisiting b???"
            visited.add(b)

            stack = stack.copy()

            get_instrs = []
            for v in phi_nodes[b]:
                get_instrs.append({"dest": phi_nodes[b][v], "op": "get"})
                stack[v] = phi_nodes[b][v]
            if "label" in self.blocks[b][0]:
                self.blocks[b] = [self.blocks[b][0]] +  get_instrs + self.blocks[b][1:]
            else:
                self.blocks[b] = get_instrs + self.blocks[b]

            for instr in self.blocks[b]:
                if instr.get("op", None) == "get":
                    continue

                if "args" in instr:
                    # print("stack:", stack)
                    for v in instr["args"]:
                        if v not in stack:
                            print(f"FAILED: instr = {instr}, v = {v}")
                            assert False
                    instr["args"] = [stack[v] for v in instr["args"]]
                if "dest" in instr:
                    dest = instr["dest"]
                    counts[dest] = counts.get(dest, -1) + 1
                    instr["dest"] = f"{dest}.{counts[dest]}"
                    stack[dest] = instr["dest"]

            set_instrs = []
            for s in self.succ[b]:
                for p in phi_nodes[s]:
                    if b not in defs[p]:
                        continue
                    if p not in stack:
                        print(f"FAILED: stack = {stack}, p = {p}, s = {s}, phi_nodes[{s}] = {phi_nodes[s]}")
                        assert False
                    set_instrs.append({"op": "set", "args": [phi_nodes[s][p], stack[p]]})
            if self.blocks[b][-1].get("op", None) in ["jmp", "br"]:
                self.blocks[b].extend(set_instrs)
            else:
                self.blocks[b] = self.blocks[b][:-1] + set_instrs + [self.blocks[b][-1]]

            for dt2 in dt[1]:
                rename(dt2, stack)

        rename(self.dom_tree, {v: v for v in self.fun_args})

        """
        ADD A BUNCH OF UNDEFS
        """
        undef_instrs = []
        for i in range(self.n):
            for v in phi_nodes[i]:
                if v not in self.fun_args:
                    undef_instrs.append({"dest": v, "op": "undef"})
                undef_instrs.append({"op": "set", "args": [phi_nodes[i][v], v]})
        self.blocks[0] = undef_instrs + self.blocks[0]




    def _to_ssa1(self):
        count = {}

        dfs = [self.compute_dom_frontier(i) for i in range(self.n)]
        sets = [{} for _ in range(self.n)]  # sets[i]["name"] = "name.3" means we need to set "name" name.3
        phi_nodes = [{} for _ in range(self.n)]

        all_vars = {}
        for b in self.blocks:
            for instr in b:
                if "dest" in instr:
                    assert "type" in instr, instr
                    if instr["dest"] not in self.fun_args:
                        all_vars[instr["dest"]] = instr["type"]

        # prepend = [{"dest": "undef", "op": "undef"}
        prepend = []
        for var in all_vars:
            prepend.append({"dest": var, "op": "undef", "type": all_vars[var]})


        for i, b in enumerate(self.blocks):
            sets = {}
            for instr in b:
                if "dest" not in instr:
                    continue

                dest = instr["dest"]
                count[dest] = count.get(dest, -1) + 1
                instr["dest"] += "." + str(count[dest])
                sets[dest] = instr

            for j in dfs[i]:
                for dest in sets:
                    if dest not in phi_nodes[j]:
                        count[dest] = count.get(dest, -1) + 1
                        phi_nodes[j][dest] = { "dest": dest + "." + str(count[dest]), "args": [] }
                    phi_nodes[j][dest]["args"].append(sets[dest]["dest"])
                    if "type" in sets[dest]:
                        phi_nodes[j][dest]["type"] = sets[dest]["type"]

                    set_instr = {"op": "set", "args": [phi_nodes[j][dest]["dest"], sets[dest]["dest"]]}
                    if b and b[-1].get("op", None) in ["br", "jmp"]:
                        b.insert(-1, set_instr)

                    else:
                        b.append(set_instr)


        for i in range(self.n):
            for dest in phi_nodes[i]:
                prepend.append({"op": "set", "args": [phi_nodes[i][dest]["dest"], dest]})


        for i, b in enumerate(self.blocks):
            get_instrs = []
            # defined = set()
            for dest in phi_nodes[i]:
                get_dest = phi_nodes[i][dest]
                # if get_dest not in defined:
        #             get_instrs.append({"op": "set", "args": [get_dest, "undefundefundefundefundef"]})
                get_instr = {"dest": get_dest["dest"], "op": "get"}
                if "type" in get_dest:
                    get_instr["type"] = get_dest["type"]
                get_instrs.append(get_instr)
        #         defined.add(get_dest)
        #     for instr in b:
        #         if "dest" in instr:
        #             defined.add(instr["dest"])

            if self.blocks[i]:
                if "label" in self.blocks[i][0]:
                    self.blocks[i] = [self.blocks[i][0]] + get_instrs + self.blocks[i][1:]
                else:
                    self.blocks[i] = get_instrs + self.blocks[i]
        #     self.blocks[i].insert(0, {"dest": "undefundefundefundefundef", "op": "undef"})

        # if debug_mode:
        #     print(phi_nodes)
        #     for i in range(self.n):
        #         for j in phi_nodes[i]:
        #             print(phi_nodes[i][j]["dest"])
        #             # print(j, j["dest"])


        def find(arg, var_stack):
            for d in reversed(var_stack):
                # print(d)
                # print("d:", d, "arg:", arg)
                if arg in d:
                    return d[arg]
            assert False, f"{arg} not found in {var_stack}"
            # return arg


        def trim(s):
            for i in range(len(s) - 1, -1, -1):
                if s[i] == ".":
                    return s[:i]
            # if s in ["undefundefundefundefundef"] + [self.fun_args]:
            #     return s
            assert s in self.fun_args, f"{s}, {self.fun_args}"
            return s
            # assert False, f"failed trim on {s}"

        visited = set()
        def rename_args(i, var_stack=None):
            if i in visited:
                return
            visited.add(i)

            if var_stack is None:
                var_stack = []

            if debug_mode:
                print("var_stack: ", var_stack)

            var_stack.append({})
            # print(f"\nBlock {i}: ")
            for instr in self.blocks[i]:
                # print("instr:", instr)
                # print("var_stack:", var_stack)
                if "args" in instr:
                    if instr.get("op", None) == "set":
                        continue
                    instr["args"] = [find(arg, var_stack) for arg in instr["args"]]
                if "dest" in instr:
                    var_stack[-1][trim(instr["dest"])] = instr["dest"]
        #     if debug_mode:
        #         print("var_stack: ", var_stack)

            for child in self.succ[i]:
                rename_args(child, var_stack)
            var_stack.pop()

        # # print(self._func["args"])
        # var_stack = [None]
        # # print(self.fun_args)
        # var_stack[-1] = {i: i for i in self.fun_args}
        # print(f"fun_args: {self.fun_args}")
        var_stack = [{i: i for i in self.fun_args}]

        # for i in self._func["args"]:
        # #     var_stack[-1][i["name"]] = i["name"]
        # # print(var_stack)
        for i in range(self.n):
            rename_args(i, var_stack)

        self.blocks[0] = prepend + self.blocks[0]
        # print(self.dom_tree, visited)
        # for i in range(self.n):
        #     if i not in visited:
        #         assert False, f"block {i} not visited"


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
        print("dfs:", dfs)
        print()
        # bb.debug_print()
