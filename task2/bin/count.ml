open Bril
module StringMap = Map.Make (String)

let i_types =
  [|
    "label";
    "const";
    "binary";
    "unary";
    "jump";
    "branch";
    "call";
    "return";
    "print";
    "nop";
    "phi";
    "speculate";
    "commit";
    "guard";
    "alloc";
    "free";
    "store";
    "load";
    "pointer_add";
  |]

let init_count () =
  let map = ref StringMap.empty in
  Array.iter (fun i_type -> map := StringMap.add i_type 0 !map) i_types;
  !map

let count_instrs prog =
  prog |> List.fold_left (fun acc f -> acc + List.length (Func.instrs f)) 0

let instr_to_string (instr : Instr.t) =
  match instr with
  | Label _ -> "label"
  | Const _ -> "const"
  | Binary _ -> "binary"
  | Unary _ -> "unary"
  | Jmp _ -> "jump"
  | Br _ -> "branch"
  | Call _ -> "call"
  | Ret _ -> "return"
  | Print _ -> "print"
  | Nop -> "nop"
  | Phi _ -> "phi"
  | Speculate -> "speculate"
  | Commit -> "commit"
  | Guard _ -> "guard"
  | Alloc _ -> "alloc"
  | Free _ -> "free"
  | Store _ -> "store"
  | Load _ -> "load"
  | PtrAdd _ -> "pointer_add"

let count_instrs_verbose prog =
  let help count func =
    let count = ref count in
    let instrs = Func.instrs func in
    List.iter
      (fun instr ->
        let instr = instr_to_string instr in
        count := StringMap.add instr (StringMap.find instr !count + 1) !count)
      instrs;
    !count
  in
  prog |> List.fold_left help (init_count ())

let prog =
  In_channel.input_all In_channel.stdin
  |> Yojson.Basic.from_string |> Bril.from_json

let () =
  let count = count_instrs_verbose prog in
  Array.iter
    (fun i_type ->
      Printf.printf "%s instructions: %d\n" i_type (StringMap.find i_type count))
    i_types
