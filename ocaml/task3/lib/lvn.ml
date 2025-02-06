open Bril

module LVNTable = struct
  type value =
    | Const of Const.t
    | Binary of Op.Binary.t * int * int
    | Unary of Op.Unary.t * int
    | Print of int list
    | Br of int
    | Ret of int option

  type t = {
    env : (string * int) list;
    table : (value * string list) list;
  }

  let empty = { env = []; table = [] }

  let find_opt (v : value) (lvn_tab : t) : int option =
    match List.find_index (fun x -> fst x = v) lvn_tab.table with
    | None -> None
    | Some i -> Some (List.length lvn_tab.table - 1)

  let nth (i : int) (lvn_tab : t) =
    let i' = List.length lvn_tab.table - 1 in
    List.nth lvn_tab.table i'

  let to_value lvn_tab instr : value =
    let env = lvn_tab.env in
    match instr with
    | Instr.Label _ -> failwith "shouldn't be label"
    | Instr.Const (_, c) -> Const c
    | Instr.Binary ((vd, _), op, v1, v2) ->
        let i1 = List.assoc v1 env in
        let i2 = List.assoc v2 env in
        Binary (op, i1, i2)
    | Instr.Unary ((vd, _), op, v1) ->
        let i1 = List.assoc v1 env in
        Unary (op, i1)
    | Print vs ->
        let is = vs |> List.map (fun v -> List.assoc v env) in
        Print is
    | Br (v, _, _) -> Br (List.assoc v env)
    | Ret None -> Ret None
    | Ret (Some v) -> Ret (Some (List.assoc v env))
    | _ -> failwith "unimplemented"

  let insert var_name instr lvn_tab =
    let v = to_value lvn_tab instr in
    match find_opt v lvn_tab with
    | Some i -> { lvn_tab with env = (var_name, i) :: lvn_tab.env }
    | None ->
        let env = (var_name, List.length lvn_tab.table) :: lvn_tab.env in
        let table = (v, [ var_name ]) :: lvn_tab.table in
        { env; table }

  let process_instr (instr : Instr.t) (lvn_tab : t) : Instr.t * t =
    match instr with
    | Label _ | Jmp _ -> (instr, lvn_tab)
    | Const ((var, _), const) -> (instr, insert var instr lvn_tab)
    | _ -> failwith "todo"
end

let lvn_instrs (block : Instr.t list) =
  List.fold_left
    (fun (instrs, lvn_tab) instr ->
      let instr, lvn_tab' = LVNTable.process_instr instr lvn_tab in
      (instr :: instrs, lvn_tab'))
    ([], LVNTable.empty) block
  |> fst |> List.rev

let lvn_func func =
  let blocks = Blocks.form_blocks func in
  let blocks' = List.map lvn_instrs blocks in
  Func.set_instrs func (List.concat blocks')

let lvn prog = List.map lvn_func prog
