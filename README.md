# XOR-Clause-Generator
Generates XOR clauses in dimacs format given order (variable count), cutting size (how long each XOR chain should be), cutting style (Linear or Pooled; how chains are created), and if we are looking for solutions (True or False; Default is true).
After generating clauses, it exhaustively searches through every solution, producing 2^(order - 1) solutions and their binary representation.

Cutting styles based on the paper "XOR Local Search for Boolean Brent Equations" by Wojciech Nawrocki, Zhenjun Liu, Andreas Frohlich, Marijn J.H. Heule, and Armin Biere.
