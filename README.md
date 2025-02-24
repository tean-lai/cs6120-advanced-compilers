# cs6120-advanced-compilers

A bunch of mini compiler projects done for the course Cornell CS 6120: Advanced Compilers.

The structure of this repo is a little messy since I switch between using OCaml and Python for the implementations. ocaml/ contains my work in OCaml while python/ contains my work with Python, sorry!

## Task 2
I implemented basic block and conflow graph construction in OCaml.

I also implement some basic code transformations.

## Task 3
I used Python for this one. I implemented some trivial global dead code elimination. Using local value numbering, I implied common subexpression elimination, constant propagation, and constant folding.

## Task 4
I implemented a general dataflow analysis engine in Python, that supports liveness analysis, constant folding, variable declaration detection. It can modify code if necessary, eliminating dead code and folding constants. 
