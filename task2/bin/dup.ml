open Bril

let duplicate_instrs prog : Bril.t =
  let help func =
    let instrs = Func.instrs func in
    let instrs' =
      List.fold_left (fun acc instr -> instr :: instr :: acc) [] instrs
      |> List.rev
    in
    Func.set_instrs func instrs'
  in
  List.map help prog

let prog =
  In_channel.input_all In_channel.stdin
  |> Yojson.Basic.from_string |> Bril.from_json

let () =
  prog |> duplicate_instrs |> Bril.to_json |> Yojson.Basic.pretty_to_string
  |> print_endline

(* let () = print_endline (Yojson.pretty_to_string (duplicate_instrs prog)) *)
