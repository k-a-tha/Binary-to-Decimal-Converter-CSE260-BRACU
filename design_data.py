"""
design_data.py
==============
Single source of truth for the 4-bit binary -> 10-line (0..10) converter.

Everything here is transcribed from, or derived from, the original project PDF
(docs/original/CSE260-Project-1.pdf).  generate_diagrams.py and
verify_design.py both import this module, so the truth table, K-map groups,
Boolean expressions, gate netlist and IC allocation are always checked against
one common description.

Conventions
-----------
* Inputs   : A (MSB), B, C, D (LSB);  N = 8A + 4B + 2C + D
* Outputs  : L1 ... L10;  Lk = 1  <=>  N >= k   (unary / "thermometer" code)
* Valid N  : 0..10.  N = 11..15 never occurs and is treated as don't-care.
"""
import re

INPUTS = ("A", "B", "C", "D")
OUTPUTS = tuple(f"L{k}" for k in range(1, 11))
VALID = tuple(range(0, 11))
DONT_CARE = tuple(range(11, 16))

# --------------------------------------------------------------------------
# 1. Truth table, transcribed row by row from page 1 of the PDF.
#    Key = decimal value of ABCD, value = string of L1..L10 (left to right).
# --------------------------------------------------------------------------
PDF_TRUTH_TABLE = {
    0: "0000000000",
    1: "1000000000",
    2: "1100000000",
    3: "1110000000",
    4: "1111000000",
    5: "1111100000",
    6: "1111110000",
    7: "1111111000",
    8: "1111111100",
    9: "1111111110",
    10: "1111111111",
}

# --------------------------------------------------------------------------
# 2. Simplified expressions exactly as written under each K-map in the PDF.
#    (Juxtaposition = AND, '+' = OR.  No complemented literal appears.)
# --------------------------------------------------------------------------
PDF_EXPRESSIONS = {
    1: "A+B+C+D",
    2: "A+B+C",
    3: "A+B+CD",
    4: "A+B",
    5: "A+BC+BD",
    6: "A+BC",
    7: "A+BCD",
    8: "A",
    9: "A(C+D)",
    10: "AC",
}

# K-map groups (prime implicants) chosen for each output, written as product
# terms.  These are *derived* here (the PDF only draws groups for L1 and L2)
# and are checked against PDF_EXPRESSIONS by verify_design.py.
KMAP_GROUPS = {
    1: ["A", "B", "C", "D"],
    2: ["A", "B", "C"],
    3: ["A", "B", "CD"],
    4: ["A", "B"],
    5: ["A", "BC", "BD"],
    6: ["A", "BC"],
    7: ["A", "BCD"],
    8: ["A"],
    9: ["AC", "AD"],
    10: ["AC"],
}


def bits(n):
    """Return (A, B, C, D) for decimal n."""
    return (n >> 3) & 1, (n >> 2) & 1, (n >> 1) & 1, n & 1


def term_minterms(term):
    """Minterms (0..15) covered by a product term of uncomplemented literals."""
    idx = [INPUTS.index(v) for v in term]
    return [m for m in range(16) if all(bits(m)[i] for i in idx)]


def eval_expr(expr, a, b, c, d):
    """Evaluate an expression such as 'A+BC+BD' or 'A(C+D)' (AND binds tighter)."""
    py = re.sub(r"(?<=[ABCD)])(?=[ABCD(])", "&", expr.replace(" ", ""))
    py = py.replace("+", "|")
    return int(eval(py, {"__builtins__": {}}, {"A": a, "B": b, "C": c, "D": d}))


def expected_output(n, k):
    """Value of Lk for valid input n according to the PDF truth table."""
    return int(PDF_TRUTH_TABLE[n][k - 1])


# --------------------------------------------------------------------------
# 3. Gate-level netlist, read from the schematic on page 4 of the PDF.
#    (id, type, input-1 net, input-2 net, output net)
#    Listed in dependency order.  Input order inside a gate is immaterial
#    logically; it follows the hand-drawn IC sketch where that was legible.
# --------------------------------------------------------------------------
NETLIST = [
    ("G1", "OR", "A", "B", "AB"),               # A+B   (shared; also output L4)
    ("G2", "OR", "C", "D", "CD_or1"),           # C+D   (for L1)
    ("G3", "OR", "AB", "CD_or1", "L1"),         # L1 = (A+B)+(C+D)
    ("G4", "OR", "AB", "C", "L2"),              # L2 = (A+B)+C
    ("G5", "AND", "C", "D", "CD_and"),          # CD
    ("G6", "OR", "CD_and", "AB", "L3"),         # L3 = CD+(A+B)
    ("G7", "AND", "B", "C", "BC"),              # BC    (shared by L5, L6, L7)
    ("G8", "AND", "B", "D", "BD"),              # BD
    ("G9", "OR", "BC", "BD", "BC_or_BD"),       # BC+BD
    ("G10", "OR", "BC_or_BD", "A", "L5"),       # L5 = (BC+BD)+A
    ("G11", "OR", "BC", "A", "L6"),             # L6 = BC+A
    ("G12", "AND", "D", "BC", "BCD"),           # BCD = D.(BC)
    ("G13", "OR", "A", "BCD", "L7"),            # L7 = A+BCD
    ("G14", "OR", "C", "D", "CD_or2"),          # C+D   (for L9; second copy)
    ("G15", "AND", "CD_or2", "A", "L9"),        # L9 = (C+D).A
    ("G16", "AND", "C", "A", "L10"),            # L10 = AC
]
GATE_BY_ID = {g[0]: g for g in NETLIST}

# Outputs that are not driven by a gate of their own.
ALIASES = {"L4": "AB",   # L4 is a tap of the A+B gate output
           "L8": "A"}    # L8 is the A input wired straight through


def output_net(name):
    return ALIASES.get(name, name)


def driver_map():
    """net name -> ('in', name) or ('gate', gate_id)."""
    d = {v: ("in", v) for v in INPUTS}
    for gid, _kind, _i1, _i2, out in NETLIST:
        d[out] = ("gate", gid)
    return d


def evaluate_netlist(a, b, c, d):
    """Simulate NETLIST; returns {net: 0/1} for every net plus L4 and L8."""
    val = {"A": a, "B": b, "C": c, "D": d}
    for _gid, kind, i1, i2, out in NETLIST:
        x, y = val[i1], val[i2]
        val[out] = (x & y) if kind == "AND" else (x | y)
    val["L4"] = val["AB"]
    val["L8"] = val["A"]
    return val


# --------------------------------------------------------------------------
# 4. IC allocation (3 quad-OR + 2 quad-AND), consistent with the IC sketch
#    on page 5 of the PDF.  Standard 74xx08 / 74xx32 pin-out:
#       gate slot 1: pins 1,2 -> 3     slot 2: pins 4,5 -> 6
#       gate slot 3: pins 9,10 -> 8    slot 4: pins 12,13 -> 11
#       GND = pin 7, VCC = pin 14
# --------------------------------------------------------------------------
IC_TYPE = {"U1": "OR", "U2": "OR", "U3": "OR", "U4": "AND", "U5": "AND"}
IC_PART = {"OR": "74xx32 (quad 2-input OR)", "AND": "74xx08 (quad 2-input AND)"}
SLOT_PINS = {1: (1, 2, 3), 2: (4, 5, 6), 3: (9, 10, 8), 4: (12, 13, 11)}

IC_ALLOCATION = [   # (IC, slot, gate id)
    ("U1", 1, "G1"), ("U1", 2, "G2"), ("U1", 3, "G3"), ("U1", 4, "G4"),
    ("U2", 1, "G14"), ("U2", 2, "G6"),
    ("U3", 1, "G9"), ("U3", 2, "G10"), ("U3", 3, "G11"), ("U3", 4, "G13"),
    ("U4", 1, "G5"), ("U4", 3, "G7"), ("U4", 4, "G8"),
    ("U5", 1, "G12"), ("U5", 2, "G15"), ("U5", 3, "G16"),
]

# Human-readable net names for diagrams and tables.
NET_LABEL = {
    "A": "A", "B": "B", "C": "C", "D": "D",
    "AB": "A+B (L4)", "CD_or1": "C+D", "CD_or2": "C+D (2nd)",
    "CD_and": "CD", "BC": "BC", "BD": "BD", "BC_or_BD": "BC+BD", "BCD": "BCD",
}
for _k in range(1, 11):
    NET_LABEL.setdefault(f"L{_k}", f"L{_k}")


def cone(net):
    """Expression tree feeding `net`: ('var', name) or ('gate', id, kind, [kids])."""
    drv = driver_map()[net]
    if drv[0] == "in":
        return ("var", net)
    _gid, kind, i1, i2, _out = GATE_BY_ID[drv[1]]
    return ("gate", drv[1], kind, [cone(i1), cone(i2)])
