type 'a t = {
  mutable backing : 'a array;
  mutable size : int;
}

let empty () = { backing = [||]; size = 0 }

let grow lst =
  let size' = lst.size * 2 in
  let backing' = Array.make size' lst.backing.(0) in
  Array.blit lst.backing 0 backing' 0 lst.size;
  lst.backing <- backing'

let append x lst =
  if Array.length lst.backing = 0 then (
    lst.backing <- Array.make 8 x;
    lst.size <- 1)
  else (
    if Array.length lst.backing = lst.size then grow lst;
    lst.backing.(lst.size) <- x;
    lst.size <- lst.size + 1)
