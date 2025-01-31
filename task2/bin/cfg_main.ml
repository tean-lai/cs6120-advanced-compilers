open Bril
open Task2
module StringMap = Map.Make (String)

type leader =
  | Init
  | Label of string
  | None

type block = {
  leader : leader;
  instrs : Instr.t list;
}

module IntSet = Set.Make (Int)
(* module StringMap = Map.Make (String) *)

let form_blocks (func : Func.t) =
  (* let helper (instrs : Instr.t list) acc = match instrs with | [] -> acc | h
     :: t -> ( match h with | Label label -> helper t ({ leader = Label label;
     instrs = [ h ] } :: acc) ) in *)
  let instrs = Func.instrs func |> Array.of_list in
  (* let leaders = ref (IntSet.of_list [ 1 ]) in *)
  let leaders = ref IntSet.empty in
  let label_to_index =
    let map = ref StringMap.empty in
    Array.iteri
      (fun i (instr : Instr.t) ->
        match instr with
        | Label label -> map := StringMap.add label i !map
        | _ -> ())
      instrs;
    !map
  in
  Array.iteri
    (fun i (instr : Instr.t) ->
      match instr with
      | Br (_, l1, l2) ->
          leaders := IntSet.add (StringMap.find l1 label_to_index) !leaders;
          leaders := IntSet.add (StringMap.find l2 label_to_index) !leaders;
          leaders := IntSet.add (i + 1) !leaders
      | Jmp l ->
          leaders := IntSet.add (StringMap.find l label_to_index) !leaders;
          leaders := IntSet.add (i + 1) !leaders
      | _ -> ())
    instrs;
  let leaders = !leaders in

  let blocks = ref [] in
  let curr = ref [] in
  Array.iteri
    (fun i instr ->
      if IntSet.mem i leaders then (
        blocks := List.rev !curr :: !blocks;
        curr := [ instr ])
      else curr := instr :: !curr)
    instrs;
  if !curr <> [] then blocks := List.rev !curr :: !blocks;
  !blocks

let form_cfg func = failwith "todo"

let prog =
  In_channel.input_all In_channel.stdin
  |> Yojson.Basic.from_string |> Bril.from_json

let functions_blocks = List.map form_blocks prog

let print_blocks blocks =
  print_endline "==start_func==";
  blocks
  |> List.iter (fun x ->
         print_endline "==start_block==";
         x |> List.map Instr.to_string |> List.map print_endline |> ignore;
         print_endline "==end_block==");
  print_endline "==end_end==\n"

let () = functions_blocks |> List.iter print_blocks
