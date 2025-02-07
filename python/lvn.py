import json
import sys
from copy import deepcopy

from blocks import BasicBlocks


def _reconstruct_args(instr, table, var2num):
    new_instr = deepcopy(instr)
    # print("reconstruct, instr:", instr)
    if instr["op"] == "const":
        return new_instr
    else:
        for i, arg in enumerate(instr.get("args", [])):
            num = var2num[arg]
            new_var = table[num][1]
            new_instr["args"][i] = new_var
    return new_instr


def _fresh():
    count = 0
    while True:
        yield f"v{count}"
        count += 1


def lvn(instrs, const_prop=False):
    """Takes in list of instructions, returns a list of optimized instructions."""
    table = []
    var2num = {}

    output = []

    for instr in instrs:
        if "label" in instr:
            output.append(instr)
            continue

        assert "op" in instr

        # print("instr:", instr)
        should_exist_already = ["print", "id", "nop", "ret", "call", "br", "jmp"]
        value = [instr["op"]]
        for arg in instr.get("args", ()):
            if arg not in var2num:
                i = len(table)
                table.append((arg, arg))  # first arg just has to be "fresh"
                var2num[arg] = i

            value.append(var2num[arg])
        if "value" in instr:
            value.append(instr["value"])
        value = tuple(value)

        if instr["op"] in should_exist_already:
            output.append(_reconstruct_args(instr, table, var2num))
            continue

        # assert not ((instr.get("value", None)) and (not instr.get("args", None))), instr

        assert "dest" in instr, instr
        in_table = False
        for i in range(len(table)):
            if value == table[i][0] and not (
                table[i][0][0] == "const" and type(value[1]) != type(table[i][0][1])
            ):
                instr = _reconstruct_args(instr, table, var2num)
                instr["op"] = "id"
                instr["args"] = [table[i][1]]
                var2num[instr["dest"]] = i
                in_table = True
                output.append(instr)
                break
        if in_table:
            continue

        # assert instr["op"] != "const", value
        dest = instr["dest"]
        if dest in var2num:
            curr_num = var2num[dest]
            replacement = None
            for i in var2num:
                if var2num[i] == curr_num and i != dest:
                    replacement = i
                    table[curr_num] = (table[curr_num][0], replacement)
                    break
            if not replacement:
                table[curr_num] = (None, None)

        var2num[dest] = len(table)
        table.append((value, dest))

        output.append(_reconstruct_args(instr, table, var2num))

    return output


if __name__ == "__main__":
    prog = json.load(sys.stdin)

    for func in prog["functions"]:
        blocks = BasicBlocks(func)
        new_instrs = []

        for instrs in blocks.blocks:
            new_instrs += lvn(instrs)

        func["instrs"] = new_instrs

    print(json.dumps(prog))
