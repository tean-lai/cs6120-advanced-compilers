Implemented Task 2 things in OCaml.

In bin/, I have two basic program analyses. 
- Running `dune exec bin/count.exe < prog.json` will count the number of each different instructions and output it in the console.
- Running `dune exec bin/dup.exe < prog.json` will output a program with each instruction in the original program duplicated.

In benchmark/, I wrote a binary-exponentiation Bril program, which is close to a recursive implementation of the algorithm. This benchmark aims to measure tail-recursive optimizations.

In lib/json_parser.ml, I've begun writing a (parser?) to convert json into an AST that I can use. I didn't want to rely on the bril-ocaml one and build one from scratch, but I may be wasting too much time on this. I wanted to get this done before implementing a CFG algorithm with it.

I implement basic blocks and cfgs in bin/cfg_main.ml. It'll find the CFGs of each function in a Bril program and print them to the console, which each node being a basic block. 