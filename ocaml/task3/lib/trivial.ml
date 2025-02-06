open Bril

(* TODO could revisit for branch and jump shenanigans *)

(** Precondition: [instrs] is a basic block (no jumps, branch, return except at
    end) *)
let rec used_before_rename var instrs =
  match instrs with
  | [] -> false
  | h :: t -> (
      match h with
      | Instr.Const ((var1, _), _) when var = var1 -> false
      | Instr.Const _ -> used_before_rename var t
      | Instr.Unary ((var1, _), _, var2) ->
          if var = var2 then true
          else if var = var1 then false
          else used_before_rename var t
      | Instr.Binary (_, _, var1, var2) when var = var1 || var = var2 -> true
      | Instr.Binary ((var1, _), _, _, _) when var = var1 -> false
      | Instr.Binary _ -> used_before_rename var t
      | Instr.Br (var1, _, _) -> var = var1
      | Instr.Ret None -> used_before_rename var t
      | Instr.Ret (Some var1) ->
          if var = var1 then true else used_before_rename var t
      | (Instr.Print vars | Instr.Call (_, _, vars)) when List.mem var vars ->
          true
      | Instr.Print _ | Instr.Call _ -> used_before_rename var t
      (* | _ -> used_before_rename var t *)
      | Instr.Label _ | Instr.Nop -> used_before_rename var t
      | Instr.Jmp _ -> false
      | Instr.Phi _ -> failwith "phi???"
      | Instr.Load _ -> failwith "load???"
      | Instr.Free _ -> failwith "free???"
      | Instr.Store _ -> failwith "store???"
      | Instr.PtrAdd _ -> failwith "ptradd???"
      | Speculate | Commit | Guard _ | Alloc _ ->
          failwith "speculate??? commit???"
          (* | _ -> failwith "unimplemented instructions, or precondition
             violated" *))

let rec one_pass (instrs : Instr.t list) : Instr.t list =
  match instrs with
  | [] -> []
  | (Instr.Const ((var, _), _) as h) :: t
  | (Instr.Binary ((var, _), _, _, _) as h) :: t
  | (Instr.Unary ((var, _), _, _) as h) :: t ->
      if used_before_rename var t then h :: one_pass t else one_pass t
  | h :: t -> h :: one_pass t

let rec iterate instrs =
  (* print_endline "iterate"; instrs |> List.map Instr.to_string |> List.iter
     print_endline; print_newline (); *)
  let instrs' = one_pass instrs in
  if instrs = instrs' then instrs else iterate instrs'

let trivial_elim_instrs instrs = iterate instrs
(* let trivial_elim_instrs instrs = instrs *)

let trivial_elim_func func =
  let blocks = Blocks.form_blocks func in
  let blocks' = List.map trivial_elim_instrs blocks in
  Func.set_instrs func (List.concat blocks')

let trivial_elim prog = List.map trivial_elim_func prog
