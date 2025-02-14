from copy import deepcopy


def _get_used_labels(instrs: list[dict]):
    used = set()
    for instr in instrs:
        if instr.get("op", None) in ["jmp", "br"]:
            used.update(instr["labels"])
    return used


class BasicBlocks:

    def _add_block(self, block):
        self.blocks.append(block)
        self.succ.append(set())
        self.pred.append(set())

    def __init__(self, func):
        # print(func)
        # print("hi")
        self._func = deepcopy(func)
        self.instrs = self._func["instrs"]
        self.blocks = []
        self.succ: list[set] = []
        self.pred = []
        self._label_to_idx = {}

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
                self._label_to_idx[instr["label"]] = len(self.blocks)
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
                k = self._label_to_idx[j]
                new.add(k)
                self.pred[k].add(i)
            self.succ[i] = new

    def debug_print(self):
        import json

        print(json.dumps(self.blocks, indent=2))
        print(self.succ)
        print(self.pred)
        print()

    def to_func(self):
        new_instrs = []
        for block in self.blocks:
            for i in block:
                new_instrs.append(i)

        new_func = deepcopy(self._func)
        new_func["instrs"] = new_instrs
        return new_func
