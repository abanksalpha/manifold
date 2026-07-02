# Graph theory — GRE problem types

Scope: recognition-level graph-theory patterns on the GRE Mathematics Subject Test — a small slice of the Discrete Mathematics strand inside the ~25% "additional topics" — grouped by sub-skill: terminology & degree/handshake facts, edge counts in complete/bipartite graphs, trees & connectivity, planarity/coloring/Euler's formula, and Euler/Hamiltonian traversals.

> **Orientation & honesty notes.** Explicit graph-theory questions are _infrequent_ on this exam: graph theory is one item in the ETS outline's Discrete Mathematics list ("logic, set theory, combinatorics, graph theory, and algorithms"), and the topic sits at the **recognize** tier — questions reward a known definition, a small formula, or a parity/counting observation rather than a proof. Difficulty and frequency below are therefore **graph-theory-relative** qualitative judgments, not shares of the whole test. The counting patterns (complete-graph edges, handshakes/round-robins) are marked _common_ only because they overlap heavily with the combinatorics that the exam tests often; the genuinely graph-specific recognition items (Euler's formula, coloring, Euler/Hamiltonian criteria, Cayley's formula) are _occasional_ to _rare_. Two real conventions apply: **no calculator** (numbers are engineered to stay clean), and answers often use the "which of I, II, III is true" format. Frequencies are qualitative reads of the released forms (GR0568, GR8767, GR9367, GR9768, GR1268, GR3768) plus standard prep, **not** counted statistics; no specific question numbers are cited because they are not verifiable here.

---

## Graph terminology, degree sequences & the handshake lemma

### 1. Handshake lemma: edges from the degree sum

- **What it asks:** Given the degrees of the vertices (a list, or "every vertex has degree `d`"), find the number of edges.
- **Solve approach:** The sum of all vertex degrees equals `2·|E|` (each edge contributes 2), so `|E| = (Σ deg)/2`. For a `d`-regular graph on `n` vertices, `|E| = n·d/2`.
- **Difficulty & frequency:** Easy; occasional.
- **Example stem:** _"A graph has six vertices with degrees 4, 4, 3, 3, 2, 2. How many edges does it have?"_

### 2. Degree-sequence feasibility (parity)

- **What it asks:** Decide whether a graph with a stated degree sequence or a `d`-regular graph on `n` vertices can exist.
- **Solve approach:** The degree sum must be even (handshake lemma), so the **number of odd-degree vertices is always even**; a `d`-regular graph on `n` vertices requires `n·d` even. If the sum is odd, no such graph exists — no further work needed.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"Does there exist a simple graph with exactly five vertices, each of degree 3?"_

### 3. Terminology & isomorphism-invariant recognition

- **What it asks:** Identify which statement correctly uses a graph definition (simple graph, regular, complement, subgraph, connected) or which properties two isomorphic graphs must share.
- **Solve approach:** Match definitions directly; for isomorphism, recall that the **degree sequence, edge count, connectivity, cycle structure, and planarity are invariants**, whereas a specific vertex labeling is not. Eliminate options that describe non-invariants.
- **Difficulty & frequency:** Easy; occasional/rare.
- **Example stem:** _"Which of the following must be identical for two isomorphic graphs? I. the degree sequence, II. the number of edges, III. the labels on the vertices."_

---

## Counting edges in complete & bipartite graphs

### 4. Edges of the complete graph (the handshake count)

- **What it asks:** Count the edges of `Kₙ`, or the total number of pairwise interactions among `n` objects.
- **Solve approach:** Every pair of the `n` vertices is joined, so `|E| = C(n, 2) = n(n−1)/2`. Recognize "each pair meets exactly once" as `Kₙ`.
- **Difficulty & frequency:** Easy; common (overlaps directly with combinatorics).
- **Example stem:** _"At a gathering of `n` people, each person shakes hands exactly once with every other person. In terms of `n`, how many handshakes occur?"_

### 5. Disguised `C(n, 2)` counts (round-robins, segments, diagonals)

- **What it asks:** A word problem that is secretly "count the edges of `Kₙ`": games in a round-robin, line segments determined by points, diagonals of a polygon, pairwise intersections.
- **Solve approach:** Reduce to `C(n, 2)`, then adjust for the specific object: a convex `n`-gon has `C(n, 2) − n` diagonals (subtract the sides); `n` points with no three collinear determine `C(n, 2)` lines. Watch for what to subtract.
- **Difficulty & frequency:** Easy–medium; common.
- **Example stem:** _"In a league of 8 teams in which each team plays every other team exactly once, how many games are scheduled?"_

### 6. Edges of a complete bipartite graph

- **What it asks:** Count the edges of `K_{m,n}`, or recognize a bipartite structure.
- **Solve approach:** Every one of the `m` vertices on one side joins every one of the `n` on the other, so `|E| = m·n`. Recall a graph is bipartite iff it has **no odd-length cycle**, and `K_{m,n}` contains no triangle.
- **Difficulty & frequency:** Easy–medium; occasional/rare.
- **Example stem:** _"How many edges does the complete bipartite graph `K_{3,4}` have?"_

### 7. Counting triangles / complete subgraphs in `Kₙ`

- **What it asks:** Count how many triangles (or `k`-cliques) appear among `n` mutually adjacent vertices or `n` points in general position.
- **Solve approach:** A triangle is any choice of 3 vertices, so the count is `C(n, 3)`; more generally a `Kₖ` subgraph count is `C(n, k)`. Compute the binomial coefficient by cancellation.
- **Difficulty & frequency:** Medium; rare/occasional.
- **Example stem:** _"How many triangles are determined by 8 points in the plane, no three of which are collinear?"_

---

## Trees, spanning trees & connectivity

### 8. Tree edge count & characterization

- **What it asks:** Use the defining count of a tree — find its edges/vertices, or identify which description forces a graph to be a tree.
- **Solve approach:** A tree on `n` vertices has exactly `n − 1` edges; equivalently it is **connected and acyclic**, with a unique path between any two vertices. Any two of {connected, acyclic, `n − 1` edges} imply the third.
- **Difficulty & frequency:** Easy; occasional.
- **Example stem:** _"A tree has 15 vertices. How many edges does it have?"_

### 9. Minimum edges for connectivity / counting components

- **What it asks:** Find the fewest edges that can connect `n` vertices, or the number of edges in a forest with a given number of components.
- **Solve approach:** A connected graph on `n` vertices needs at least `n − 1` edges (a spanning tree); a graph with fewer than `n − 1` edges must be disconnected. A forest with `n` vertices and `c` components has `n − c` edges.
- **Difficulty & frequency:** Easy–medium; occasional/rare.
- **Example stem:** _"What is the least number of edges a connected graph on 10 vertices can have?"_

### 10. Cayley's formula (labeled trees / spanning trees of `Kₙ`)

- **What it asks:** Count the labeled trees on `n` vertices, i.e. the spanning trees of `Kₙ`.
- **Solve approach:** Apply Cayley's formula: there are `n^{n−2}` labeled trees on `n` vertices (equivalently `Kₙ` has `n^{n−2}` spanning trees). Keep `n` small so the power is computable by hand.
- **Difficulty & frequency:** Medium; rare.
- **Example stem:** _"How many distinct labeled trees can be formed on 4 vertices?"_

---

## Planar graphs, coloring & Euler's formula

### 11. Euler's formula `V − E + F = 2`

- **What it asks:** For a connected planar graph, find one of vertices/edges/faces given the other two, or count the regions a plane graph creates.
- **Solve approach:** Use `V − E + F = 2` (the outer/unbounded region counts as a face). Solve for the missing quantity; for "regions of the plane," `F` is the answer.
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"A connected planar graph has 10 vertices and 15 edges. Into how many regions does it divide the plane?"_

### 12. Planarity recognition & the edge bound

- **What it asks:** Decide whether a given graph is planar, or identify the standard nonplanar graph.
- **Solve approach:** Remember the two Kuratowski obstructions: `K₅` and `K_{3,3}` are **not** planar. A quick necessary test for a simple connected planar graph with `V ≥ 3` is `E ≤ 3V − 6` (and `E ≤ 2V − 4` if triangle-free); a graph exceeding the bound cannot be planar.
- **Difficulty & frequency:** Medium; rare/occasional.
- **Example stem:** _"Which of the following graphs is NOT planar: a 6-vertex tree, `K_4`, or `K_5`?"_

### 13. Chromatic number basics

- **What it asks:** Find the least number of colors for a proper vertex (or map) coloring of a small named graph.
- **Solve approach:** Use known values: `χ(Kₙ) = n`; a cycle is 2-colorable if even, 3 if odd; any bipartite graph (including trees) needs 2; every planar graph needs at most 4 (Four Color Theorem). Adjacent vertices must differ.
- **Difficulty & frequency:** Medium; rare.
- **Example stem:** _"What is the least number of colors needed to properly color the vertices of `K_5`?"_

---

## Euler & Hamiltonian paths & circuits

### 14. Euler path / circuit existence (even-degree criterion)

- **What it asks:** Decide whether a connected graph can be traced using **every edge exactly once**, as a circuit or an open path (Königsberg-style).
- **Solve approach:** A connected graph has an **Euler circuit** iff every vertex has even degree, and an **Euler path** (open) iff exactly two vertices have odd degree. Just count odd-degree vertices. (Example: `Kₙ` has all degrees `n − 1`, so it is Eulerian exactly when `n` is odd.)
- **Difficulty & frequency:** Easy–medium; occasional.
- **Example stem:** _"A connected graph has exactly two vertices of odd degree. Which of the following must be true?"_

### 15. Hamiltonian path / circuit recognition & counting

- **What it asks:** Recognize a Hamiltonian route (**every vertex once**) versus an Eulerian one, or count Hamiltonian circuits in a complete graph.
- **Solve approach:** Distinguish the definitions — Euler uses each _edge_ once, Hamilton each _vertex_ once — since there is no simple degree test for Hamiltonicity. In `Kₙ` the number of distinct Hamiltonian circuits is `(n − 1)!/2` (fix a start, divide by 2 for direction).
- **Difficulty & frequency:** Medium; rare.
- **Example stem:** _"How many distinct Hamiltonian circuits does the complete graph `K_5` have?"_
