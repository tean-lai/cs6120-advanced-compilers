open Bril
open Task2
module StringMap = Map.Make (String)
module IntSet = Set.Make (Int)

let form_blocks (func : Func.t) =
  let instrs = Func.instrs func |> Array.of_list in
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

module Cfg = struct
  type block = {
    instrs : Instr.t array;
    next : int list;
  }

  type t = block array

  let init func =
    let basic_blocks =
      form_blocks func |> List.map Array.of_list |> Array.of_list
    in
    let label_to_index =
      let map = ref StringMap.empty in
      Array.iteri
        (fun i (instrs : Instr.t array) ->
          match instrs.(0) with
          | Label label -> map := StringMap.add label i !map
          | _ -> if i = 0 then map := StringMap.add "" 0 !map)
        basic_blocks;
      !map
    in

    let cfg =
      let last_i = Array.length basic_blocks - 1 in

      let help l = StringMap.find l label_to_index in
      Array.mapi
        (fun i (block : Instr.t array) : block ->
          let next =
            match block.(Array.length block - 1) with
            | Br (_, l1, l2) ->
                [ l1; l2 ] |> List.map help |> List.sort_uniq Int.compare
            | Jmp l -> [ help l ]
            | _ when i == last_i -> []
            | _ -> [ i + 1 ]
          in
          { instrs = block; next })
        basic_blocks
    in
    cfg
end

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

let print_cfg (cfg : Cfg.t) =
  print_endline "NEW FUNCTION";
  Array.iteri
    (fun i (block : Cfg.block) ->
      Printf.printf "Block %d\n" i;
      block.instrs |> Array.map Instr.to_string |> Array.iter print_endline;
      print_string "It connects to blocks: ";
      block.next |> List.iter (Printf.printf "%d ");
      print_endline "\n")
    cfg

(* let () = functions_blocks |> List.iter print_blocks *)

let () = prog |> List.map Cfg.init |> List.iter print_cfg
