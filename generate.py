# input: variable count, cutting size, cutting type
# output: clauses required for xor chain and variable count

import os
import subprocess
import sys
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
clauses_path = os.path.join(script_dir, "clauses.cnf")

solutions_path = os.path.join(script_dir, "solutions.txt")
sat_solver_path = os.path.join(os.path.dirname(script_dir), "kissat-rel-4.0.2", "build", "kissat") # update this to your sat solver's location 

clauses = []

if len(sys.argv) < 4:
    print("Usage: python3 generate.py <order> <cutting_size> <cutting_type> [solutions_only]\n")
    sys.exit(1)

order = int(sys.argv[1]) # >= 1, the amount of variables
cutting_size = int(sys.argv[2]) # >= 3 as defined in the paper this is based on, an idea to get around this is to add hard coded support for cutting_size = 2, this would be equivalent naive xor implementation
cutting_type = str(sys.argv[3]) # "Linear" | "Pooled", determines how clauses are made but these two forms are equivalent

solutionsOnly = True
if len(sys.argv) > 4:
    solutionsOnly = sys.argv[4].lower() == "true" or sys.argv[4].lower() == "1"

exhaustive_search = True # Requires a valid solutions_path and sat_solver_path

auxiliary_variables = 0
variable_list = [] 
chains = []

def updateClauses(): # update the clauses.cnf file
    with open(clauses_path, "w") as f:
        f.write(f"p cnf {order + auxiliary_variables} {len(clauses)}\n")
        for clause in clauses:
            f.write(" ".join(str(var) for var in clause) + " 0\n")

def getCombinations(totalList, array, n, currentRemovals): # n >= 0, generate all possible combinations from n choices
    if n == 0:
        totalList.append(currentRemovals)
    else: 
        for i in range(len(array)):
            tmpList = array[i + 1 : len(array)]
            removals = currentRemovals.copy()
            removals.append(array[i])
            getCombinations(totalList, tmpList, n - 1, removals)

def add_xor_clauses(chain): # create XOR clauses for given chain, should add 2^(len(chain) - 1) clauses for XOR
    for notCount in range(0, len(chain) + 1, 2):
        total = []
        getCombinations(total, list(range(len(chain))), notCount, [])
        for i in range(len(total)):
            tmpChain = chain.copy()
            for j in range(len(total[i])):
                tmpChain[total[i][j]] = -tmpChain[total[i][j]]
            clauses.append(tmpChain) 
            print("    Added clause:", tmpChain)

def recursive_xor(): # create XOR chains
    global auxiliary_variables
    if len(variable_list) <= cutting_size:
        if solutionsOnly == False:
            variable_list[0] = -variable_list[0]
        chains.append(variable_list)
    else:
        tempList = []
        for i in range(cutting_size):
            if i + 1 == cutting_size:
                auxiliary_variables += 1
                auxiliary = order + auxiliary_variables
                tempList.append(-auxiliary)
                if cutting_type == "Pooled":
                    variable_list.append(auxiliary)
                else:
                    variable_list.insert(0, auxiliary)
            else:
                tempList.append(variable_list.pop(0))
        chains.append(tempList)
        recursive_xor()

for i in range(order):
    variable_list.append(i + 1)

recursive_xor()
print(f"Input parameters: order {order}, cutting size {cutting_size}, cutting style \"{cutting_type}\", only solutions \"{solutionsOnly}\".")
print("\nXOR Chains:",chains)
for i in range(len(chains)):
    add_xor_clauses(chains[i])

updateClauses()

print(f"\nGenerated {len(clauses)} XOR clauses by introducing {auxiliary_variables} auxiliary variable(s).")
print(f"Wrote clauses to: {clauses_path}")

if exhaustive_search == True:
    print("\nStarting exhaustive search...")
    not_unsat = True
    solutions = []
    commands = [sat_solver_path, clauses_path] 
    while not_unsat == True:
        result = subprocess.run(commands,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT, 
            universal_newlines = True
        )
        solution = []
        # check current sat solver output
        for line in result.stdout.splitlines():
            if line.startswith("s "):
                if "UNSATISFIABLE" in line:
                    not_unsat = False
                    if len(solutions) > 0:
                        print("No more solutions found, terminating.")
                    else:
                        print("No solution found, terminating.")
                    break
            elif line.startswith("v "):
                values = line[2:].strip().split()
                for val in values:
                    if val == '0': # end of variables
                        continue
                    val = int(val)
                    if abs(val) <= order:
                        solution.append(val)
        if not_unsat == True and len(solution) > 0:
            solutions.append(solution)
            blocker = []
            for i in range(order):
                blocker.append(-solution[i])
            clauses.append(blocker)
            print("    Found solution:",solution,"\n        Block clause:",blocker)
            updateClauses()
    # output solutions
    with open(solutions_path, "w") as f:
        f.write(f"Input: order {order}, cutting size {cutting_size}, cutting type \"{cutting_type}\", only solutions \"{solutionsOnly}\"\n")

        f.write(f"\n{solutionsOnly and "Correct" or "Incorrect"} Solutions:\n")
        for solution in solutions:
            f.write(" ".join(str(var) for var in solution) + "\n")

        f.write("\nBinary Representation:\n")
        for solution in solutions:
            f.write("".join((var <= 0 and "0" or "1") for var in solution) + "\n")
            
        print(f"\nOutputted {len(solutions)} solutions to {solutions_path}") # we should have 2^(order-1) solutions

# cd /mnt/g/Code/sat\ solver\ stuff/xor\ clause\ generator