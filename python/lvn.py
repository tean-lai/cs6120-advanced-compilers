import json
import sys
from copy import deepcopy
import argparse

from blocks import BasicBlocks


def _reconstruct_args(instr, table, var2num, active_opt):
    if active_opt is None:
        active_opt = []

    new_instr = deepcopy(instr)
    # print("reconstruct, instr:", instr)
    op = instr["op"]
    if op == "const":
        return new_instr

    # if op == "id" and "copy_prop" in active_opt:
    #     arg = instr["args"][0]
    #     num = var2num[arg]
    #     val, var = table[num]

    #     next_num = var2num[var]
    #     next_val, next_var = table[next_num]
    #     # if debug_mode:
    #     #     print("blah", instr, table, val, var, cond)
    #     if isinstance(next_val, tuple) and next_val[0] == "id":
    #         new_instr["args"][0] = next_var
    #         if debug_mode:
    #             print("recurse", instr, new_instr, table)
    #         return _reconstruct_args(new_instr, table, var2num, active_opt)

    if op == "id" and "const_prop" in active_opt:
        arg = instr["args"][0]
        num = var2num[arg]
        val, var = table[num]
        if val[0] == "constant":
            new_instr["op"] = "constant"
            new_instr["args"] = []
            new_instr["value"] = val[1]
        return new_instr

    for i, arg in enumerate(instr.get("args", [])):
        num = var2num[arg]
        val, var = table[num]
        new_instr["args"][i] = var
    return new_instr


def _fresh():
    count = 0
    while True:
        yield f"v{count}"
        count += 1


def lvn(instrs, active_opt):
    """Takes in list of instructions, returns a list of optimized instructions."""

    table = []
    var2num = {}

    output = []

    for instr in instrs:
        if "label" in instr:
            output.append(instr)
            if debug_mode:
                print(instr, "exit cuz label")
            continue

        assert "op" in instr
        op = instr["op"]

        # print("instr:", instr)
        # no_def = ["print", "nop", "ret", "br", "jmp"]
        commutative_ops = ["add", "mul", "eq"]
        value = [op]
        for arg in instr.get("args", ()):
            if arg not in var2num:
                i = len(table)
                assert arg is not None, arg
                table.append((arg, arg))  # first arg just has to be "fresh"
                var2num[arg] = i

            value.append(var2num[arg])
        if "value" in instr:
            value.append(instr["value"])
        if "commutativity" in active_opt and op in commutative_ops:
            value[1:] = sorted(value[1:])
            if debug_mode:
                print("commutative: ", value)
        value = tuple(value)

        if "dest" not in instr:
            output.append(_reconstruct_args(instr, table, var2num, active_opt))
            if debug_mode:
                print(instr, "exit cuz should_exist_already")
            continue

        # assert not ((instr.get("value", None)) and (not instr.get("args", None))), instr

        assert "dest" in instr, instr
        if op == "id" and "copy_prop" in active_opt:
            instr = deepcopy(instr)
            repeat = True
            while repeat:
                assert instr["args"][0] is not None, str(instr) + " " + str(table)
                num = var2num[instr["args"][0]]
                val, var = table[num]
                if (
                    isinstance(val, tuple)
                    and val[0] == "id"
                    and table[val[1]][1] is not None
                ):
                    instr["args"][0] = table[val[1]][1]
                    if debug_mode:
                        print("repeating", instr, val, var, table)
                else:
                    repeat = False

        in_table = False
        for i in range(len(table)):
            if (
                value == table[i][0]
                and not (
                    table[i][0][0] == "const" and type(value[1]) != type(table[i][0][1])
                )
                and table[i][1] is not None
            ):
                instr = _reconstruct_args(instr, table, var2num, active_opt)
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
                    break
            if debug_mode:
                print("replace", instr, replacement, table)
            table[curr_num] = (table[curr_num][0], replacement)

        var2num[dest] = len(table)
        assert value is not None and dest is not None, str(value) + " " + str(dest)
        table.append((value, dest))
        if debug_mode:
            print("table")
            for i in table:
                print(i)
            print("var2num", var2num)

        output.append(_reconstruct_args(instr, table, var2num, active_opt))

    return output


if __name__ == "__main__":
    global debug_mode
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    debug_mode = args.debug

    prog = json.load(sys.stdin)

    active_opts = []
    active_opts.append("copy_prop")
    active_opts.append("commutativity")
    # active_opts.append("const_prop")
    # active_opts.append("const_fold")

    for func in prog["functions"]:
        blocks = BasicBlocks(func)
        new_instrs = []

        for instrs in blocks.blocks:
            new_instrs += lvn(instrs, active_opts)

        func["instrs"] = new_instrs

    print(json.dumps(prog))
