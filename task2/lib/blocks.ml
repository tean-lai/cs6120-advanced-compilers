open Yojson

type t = {
  leader : string option;
  instrs : Yojson.Basic.t list;
}
