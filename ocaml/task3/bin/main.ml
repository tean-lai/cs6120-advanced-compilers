open Bril
open Task3
open Task3.Trivial

let prog =
  In_channel.input_all In_channel.stdin
  |> Yojson.Basic.from_string |> Bril.from_json

(* let _ = prog |> List.map Blocks.form_blocks |> List.iter
   Blocks.print_blocks *)

let () =
  Trivial.trivial_elim prog |> Bril.to_json |> Yojson.Basic.to_string
  |> print_endline

(* let () = Trivial.trivial_elim prog |> Bril.to_string |> print_endline *)
(* let () = prog |> Bril.to_string |> print_endline *)
(* let () = prog |> List.map (fun (x : Bril.Func.t) -> x.order |> List.map
   print_endline |> ignore; print_newline ()) |> ignore *)
