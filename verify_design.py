#!/usr/bin/env python3
"""
verify_design.py
================
Exhaustive self-check of the whole design.  Standard library only.

  1. truth table      : PDF transcription == "Lk = [N >= k]" == data/truth_table.csv
  2. expressions      : each PDF expression reproduces the truth table for N = 0..10
  3. K-map groups     : every group only covers ON/don't-care cells, is prime,
                        is irredundant, and the groups OR together to the PDF expression
  4. gate netlist     : simulation for all 16 inputs (0..10 must match the table)
  5. drawn circuits   : netlist is re-extracted from the SVG geometry (wires + junction
                        dots) of the complete circuit and of each per-output circuit,
                        compared with the netlist and simulated
  6. IC allocation    : every gate sits in exactly one legal 74xx08/74xx32 slot and the
                        pin-level netlist reproduces the outputs

Exit status 0 = everything passed.   Usage:  python3 tools/verify_design.py
"""
import csv
import os
import sys

from design_data import (INPUTS, OUTPUTS, VALID, DONT_CARE, PDF_TRUTH_TABLE, PDF_EXPRESSIONS,
                         KMAP_GROUPS, NETLIST, GATE_BY_ID, IC_ALLOCATION, IC_TYPE, SLOT_PINS,
                         bits, term_minterms, eval_expr, expected_output, evaluate_netlist,
                         driver_map, output_net, cone)
import generate_diagrams as gd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
failures = []


def check(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        failures.append(msg)


def section(title):
    print(f"\n== {title}")


# ---------------------------------------------------------------- 1
section("1. Truth table")
check(sorted(PDF_TRUTH_TABLE) == list(VALID), "PDF table has exactly the 11 valid rows 0..10")
check(all(len(v) == 10 for v in PDF_TRUTH_TABLE.values()), "every row has 10 output bits (L1..L10)")
rule_ok = all(int(PDF_TRUTH_TABLE[n][k - 1]) == int(n >= k) for n in VALID for k in range(1, 11))
check(rule_ok, "every entry equals the rule  Lk = 1 iff N >= k  (110 entries)")
check(all(PDF_TRUTH_TABLE[n].count("1") == n for n in VALID), "number of lit outputs equals N for every row")
csv_path = os.path.join(ROOT, "data", "truth_table.csv")
if os.path.exists(csv_path):
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    ok = len(rows) == 16
    for r in rows:
        n = int(r["N"])
        ok &= (int(r["A"]), int(r["B"]), int(r["C"]), int(r["D"])) == bits(n)
        for k in range(1, 11):
            want = PDF_TRUTH_TABLE[n][k - 1] if n in VALID else "X"
            ok &= r[f"L{k}"] == want
    check(ok, "data/truth_table.csv matches the PDF table (16 rows, X for 11..15)")
else:
    check(False, "data/truth_table.csv exists")

# ---------------------------------------------------------------- 2
section("2. PDF expressions vs truth table (valid inputs 0..10)")
for k in range(1, 11):
    ok = all(eval_expr(PDF_EXPRESSIONS[k], *bits(n)) == expected_output(n, k) for n in VALID)
    check(ok, f"L{k} = {PDF_EXPRESSIONS[k]:<9} reproduces all 11 valid rows")

# ---------------------------------------------------------------- 3
section("3. K-map groups")
for k in range(1, 11):
    on = {n for n in VALID if expected_output(n, k)}
    off = {n for n in VALID if not expected_output(n, k)}
    terms = KMAP_GROUPS[k]
    covers = {t: set(term_minterms(t)) for t in terms}
    ok_valid = all(not (covers[t] & off) for t in terms)
    ok_cover = set().union(*covers.values()) >= on
    prime = True
    for t in terms:                                  # dropping any literal must hit an OFF cell
        for i in range(len(t)):
            shorter = t[:i] + t[i + 1:]
            if shorter and not (set(term_minterms(shorter)) & off):
                prime = False
    irredundant = all(covers[t] & on - set().union(*[covers[u] for u in terms if u != t]) for t in terms)
    sop = "+".join(terms)
    same = all(eval_expr(sop, *bits(m)) == eval_expr(PDF_EXPRESSIONS[k], *bits(m)) for m in range(16))
    check(ok_valid and ok_cover and prime and irredundant and same,
          f"L{k}: groups {terms}: no OFF cell, all ON cells, prime, irredundant, == PDF expression (16/16)")

# ---------------------------------------------------------------- 4
section("4. Gate netlist simulation")
ok_all = True
for n in VALID:
    v = evaluate_netlist(*bits(n))
    got = "".join(str(v[f"L{k}"]) for k in range(1, 11))
    if got != PDF_TRUTH_TABLE[n]:
        ok_all = False
        print(f"     mismatch N={n}: got {got}, want {PDF_TRUTH_TABLE[n]}")
check(ok_all, "all 11 valid inputs 0..10 give the table output")
gates = {k: sum(1 for g in NETLIST if g[1] == k) for k in ("AND", "OR")}
check(gates == {"AND": 6, "OR": 10}, f"gate count: {gates['OR']} OR + {gates['AND']} AND = {len(NETLIST)}")
check(all("'" not in x for g in NETLIST for x in g[2:4]), "no complemented signals: no NOT gates required")
print("     behaviour for unspecified inputs (11..15):")
for n in DONT_CARE:
    v = evaluate_netlist(*bits(n))
    out = "".join(str(v[f"L{k}"]) for k in range(1, 11))
    print(f"       N={n:2d} ({n:04b}) -> L1..L10 = {out}  ({out.count('1')} lines on)")

# ---------------------------------------------------------------- 5
section("5. Netlist extracted from the drawn schematics")
drv = driver_map()


def netlist_driver(net):
    return drv[net]


def check_schematic(S, label, wanted_outputs, gate_ids):
    ok = True
    try:
        ex_gates, ex_outs = S.extract()
    except ValueError as e:
        check(False, f"{label}: extraction failed: {e}")
        return
    ok &= set(ex_gates) == set(gate_ids)
    for gid in gate_ids:                              # structure identical to NETLIST
        _g, kind, i1, i2, _o = GATE_BY_ID[gid]
        want = (kind, netlist_driver(i1), netlist_driver(i2))
        if ex_gates.get(gid) != want:
            ok = False
            print(f"     {label}: gate {gid} drawn as {ex_gates.get(gid)}, netlist says {want}")

    def value(d, inp, memo):
        if d[0] == "in":
            return inp[d[1]]
        if d not in memo:
            kind, a, b = ex_gates[d[1]]
            x, y = value(a, inp, memo), value(b, inp, memo)
            memo[d] = (x & y) if kind == "AND" else (x | y)
        return memo[d]

    for n in range(16):
        inp = dict(zip(INPUTS, bits(n)))
        memo = {}
        sim = evaluate_netlist(*bits(n))
        for name in wanted_outputs:
            if value(ex_outs[name], inp, memo) != sim[name]:
                ok = False
                print(f"     {label}: output {name} wrong for N={n}")
            if n in VALID and value(ex_outs[name], inp, memo) != expected_output(n, int(name[1:])):
                ok = False
    ok &= not S.collisions()
    if S.collisions():
        print(f"     {label}: wire passes through gate body: {S.collisions()}")
    check(ok, f"{label}: structure == netlist, outputs == truth table, no wire through a gate")


def walk(node, acc):
    if node[0] == "gate":
        acc.append(node[1])
        for c in node[3]:
            walk(c, acc)
    return acc


check_schematic(gd.build_complete(), "complete circuit", OUTPUTS, [g[0] for g in NETLIST])
for k in range(1, 11):
    net = output_net(f"L{k}")
    S = gd.build_output(k)
    ids = walk(cone(net), [])               # gates in the cone of this output
    check_schematic(S, f"L{k} circuit", [f"L{k}"], ids)

# ---------------------------------------------------------------- 6
section("6. IC allocation (3 x 74xx32, 2 x 74xx08)")
used = [(ic, s) for ic, s, _g in IC_ALLOCATION]
check(len(used) == len(set(used)), "no gate slot used twice")
check(sorted(g for _i, _s, g in IC_ALLOCATION) == sorted(g[0] for g in NETLIST), "every gate allocated exactly once")
check(all(IC_TYPE[ic] == GATE_BY_ID[g][1] for ic, _s, g in IC_ALLOCATION), "gate type matches IC type")
check(all(SLOT_PINS[s][2] in (3, 6, 8, 11) for _i, s, _g in IC_ALLOCATION), "all gate outputs on pins 3, 6, 8 or 11")
pin_net = gd.ic_pin_nets()
ok = True
for n in VALID:                                       # simulate using only the pin table
    val = dict(zip(INPUTS, bits(n)))
    for gid, kind, _i1, _i2, out in NETLIST:          # dependency order
        ic, slot = next((i, s) for i, s, g in IC_ALLOCATION if g == gid)
        p1, p2, po = SLOT_PINS[slot]
        a, b = val[pin_net[ic][p1]], val[pin_net[ic][p2]]
        val[pin_net[ic][po]] = (a & b) if IC_TYPE[ic] == "AND" else (a | b)
    val["L4"], val["L8"] = val["AB"], val["A"]
    ok &= "".join(str(val[f"L{k}"]) for k in range(1, 11)) == PDF_TRUTH_TABLE[n]
check(ok, "pin-level simulation reproduces all 11 valid rows")
ics = {}
for ic, _s, _g in IC_ALLOCATION:
    ics[ic] = ics.get(ic, 0) + 1
print("     gates used per package:", ics)

# ---------------------------------------------------------------- summary
print("\n" + "=" * 60)
if failures:
    print(f"RESULT: {len(failures)} check(s) FAILED")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
