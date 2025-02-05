open Bril
module StringMap = Map.Make (String)
module StringSet = Set.Make (String)

(** Return a set of labels that are used by jumps or branches within a list of
    instructions. *)
let get_used_labels instrs =
  let get_label_set = function
    | Instr.Br (_, l1, l2) -> StringSet.of_list [ l1; l2 ]
    | Instr.Jmp l -> StringSet.of_list [ l ]
    | _ -> StringSet.empty
  in
  instrs
  |> List.fold_left
       (fun acc instr -> StringSet.union acc (get_label_set instr))
       StringSet.empty

let flush curr acc = if curr = [] then acc else List.rev curr :: acc

type t = Instr.t list list

let rec chunk used_labels curr acc instrs : t =
  match instrs with
  | [] -> List.rev (flush curr acc)
  | (Instr.Label l as h) :: t when StringSet.mem l used_labels ->
      let acc' = flush curr acc in
      chunk used_labels [ h ] acc' t
  | (Br _ as h) :: t | (Jmp _ as h) :: t ->
      let curr' = h :: curr in
      let acc' = flush curr' acc in
      chunk used_labels [] acc' t
  | h :: t ->
      let curr' = h :: curr in
      chunk used_labels curr' acc t

let form_blocks (func : Func.t) : t =
  let instrs = Func.instrs func in
  let used_labels = get_used_labels instrs in
  chunk used_labels [] [] instrs

let print_blocks (blocks : t) =
  blocks
  |> List.iter (fun block ->
         print_endline "\nNew block:";
         block
         |> List.iter (fun instr -> instr |> Instr.to_string |> print_endline))
