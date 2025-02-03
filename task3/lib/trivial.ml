(* TODO could revisit for branch and jump shenanigans *)
let rec used_before_rename var instrs =
  match instrs with
  | [] -> false
  | h :: t -> (
      match h with
      | Bril.Instr.Const ((var1, _), _) ->
          if var = var1 then false else used_before_rename var t
      | Bril.Instr.Unary ((var1, _), _, var2) ->
          if var = var2 then true
          else if var = var1 then false
          else used_before_rename var t
      | Bril.Instr.Binary ((var1, _), _, var2, var3) ->
          if var = var2 || var = var3 then true
          else if var = var1 then false
          else used_before_rename var t
      | Bril.Instr.Br (var1, _, _) ->
          if var = var1 then true else used_before_rename var t
      | _ -> used_before_rename var t)

let rec one_pass (instrs : Bril.Instr.t list) : Bril.Instr.t list =
  match instrs with
  | [] -> []
  | (Bril.Instr.Const ((var, _), _) as h) :: t when used_before_rename var t ->
      h :: one_pass t
  | _ :: t -> one_pass t

let rec iterate instrs =
  let instrs' = one_pass instrs in
  if instrs = instrs' then instrs else iterate instrs'

let trivial_elim prog =
  let instrs = Bril.Func.instrs prog in
  let instrs' = iterate instrs in
  Bril.Func.set_instrs prog instrs
