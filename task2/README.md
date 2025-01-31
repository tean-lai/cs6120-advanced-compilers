Implemented Task 2 things in OCaml.

In bin/, I have two basic program analyses. 
- Running `dune exec bin/count.exe < prog.json` will count the number of each different instructions and output it in the console.
- Running `dune exec bin/dup.exe < prog.json` will output a program with each instruction in the original program duplicated.

In benchmark/, I wrote a binary-exponentiation Bril program, which is close to a recursive implementation of the algorithm. This benchmark aims to measure tail-recursive optimizations.