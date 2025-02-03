open Yojson

type typ =
  | Int
  | Bool

type value =
  | Int of int
  | Bool of bool

type bril_exp =
  | Funcs of func_exp list
  | Instrs of bril_exp list

and func_exp = {
  name : string;
  instrs : instr_exp list;
  typ : typ option;
  args : (string * typ) list;
}

and instr_exp = {
  op : string;
  dest : string;
  value : value;
}

let contains_key k assoc =
  List.fold_left (fun acc (k', _) -> k = k' || acc) false assoc

let json2string (json : Yojson.Basic.t) =
  match json with
  | `String s -> s
  | _ -> raise (Invalid_argument "json not a string")

let json2list (json : Yojson.Basic.t) =
  match json with
  | `List lst -> lst
  | _ -> raise (Invalid_argument "json not a list")

let json2assoc (json : Yojson.Basic.t) =
  match json with
  | `Assoc assoc -> assoc
  | _ -> raise (Invalid_argument "json not an association list")

let json2int (json : Yojson.Basic.t) =
  match json with
  | `Int n -> n
  | _ -> raise (Invalid_argument "json not an int")

let json2bool (json : Yojson.Basic.t) =
  match json with
  | `Bool b -> b
  | _ -> raise (Invalid_argument "json not a bool")

let string2type string : typ =
  match string with
  | "int" -> Int
  | "bool" -> Bool
  | _ -> failwith "unknown type"

let rec parse_json (json : Yojson.Basic.t) =
  match json with
  | `Assoc [ ("functions", `List funcs) ] -> Funcs (List.map parse_func funcs)
  | _ -> failwith "unimplemented or invalid"

and parse_func (func : Yojson.Basic.t) =
  let assoc = json2assoc func in
  let instrs = List.assoc "instrs" assoc |> json2list |> List.map parse_instr in
  let name = json2string (List.assoc "name" assoc) in
  let args =
    json2list (List.assoc "args" assoc)
    |> List.map (fun x ->
           let assoc' = json2assoc x in
           let name = json2string (List.assoc "name" assoc') in
           let typ = List.assoc "name" assoc' |> json2string |> string2type in
           (name, typ))
  in
  let typ =
    match List.assoc_opt "type" assoc with
    | Some v -> Some (v |> json2string |> string2type)
    | None -> None
  in
  { name; instrs; args; typ }

and parse_instr (instr : Yojson.Basic.t) : instr_exp =
  let assoc = json2assoc instr in
  let op = json2string (List.assoc "op" assoc) in
  match op with
  | "const" -> parse_const_instr op assoc instr
  | "add" -> parse_value_instr op assoc instr
  | _ -> failwith "unimplemented"

and parse_const_instr op assoc instr =
  let dest = json2string (List.assoc "dest" assoc) in
  let typ = json2string (List.assoc "type" assoc) in
  let value =
    match typ with
    | "int" -> Int (json2int (List.assoc "value" assoc))
    | "bool" -> Bool (json2bool (List.assoc "value" assoc))
    | _ -> raise (Invalid_argument "not int or bool")
  in
  { op; dest; value }

and parse_value_instr op assoc instr =
  (* let dest = json2string (List.assoc "dest" assoc) in *)
  failwith "unimplemented"

(* match instr with | `Assoc assoc -> let dest = json2string (List.assoc "dest"
   assoc) *)
