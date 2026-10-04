#!/usr/bin/env python3
"""
generate_diagrams.py
====================
Generates every diagram in diagrams/ from the data in design_data.py:

  diagrams/kmaps/Lk_kmap.svg            K-map with groups, k = 1..10
  diagrams/circuits/Lk_circuit.svg      circuit for one output, k = 1..10
  diagrams/circuits/complete_circuit.svg
  diagrams/circuits/ic_pin_allocation.svg
  diagrams/png/*.png                    PNG copies (needs `pip install cairosvg`)

The circuit drawings are built from real geometry (gates, wires, junction
dots).  verify_design.py re-extracts a netlist from that geometry and simulates
it, so the pictures are checked, not merely decorative.

Usage:  python3 tools/generate_diagrams.py [--png]
"""
import os
import sys

from design_data import (INPUTS, KMAP_GROUPS, PDF_EXPRESSIONS, GATE_BY_ID, NETLIST,
                         IC_ALLOCATION, IC_TYPE, IC_PART, SLOT_PINS, NET_LABEL,
                         output_net, cone, driver_map, term_minterms, expected_output)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "Helvetica, Arial, sans-serif"
AND_W, OR_W, HOP = 50, 55, 5


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ==========================================================================
#  Schematic drawing + netlist extraction
# ==========================================================================
class Gate:
    """2-input gate centred vertically on y = r.  Pins: in1, in2, out."""

    def __init__(self, gid, kind, x, r):
        self.id, self.kind, self.x, self.r = gid, kind, x, r
        self.w = AND_W if kind == "AND" else OR_W
        lead = 0 if kind == "AND" else 6      # OR inputs touch the concave back
        self.in1 = (x + lead, r - 10)
        self.in2 = (x + lead, r + 10)
        self.out = (x + self.w, r)

    def body_box(self):
        """Box used for collision tests (excludes the pin lead-in zone)."""
        return (self.x + 8, self.r - 19, self.x + self.w - 1, self.r + 19)

    def svg(self):
        x, r = self.x, self.r
        if self.kind == "AND":
            d = f"M {x},{r-20} H {x+30} A 20 20 0 0 1 {x+30},{r+20} H {x} Z"
        else:
            d = (f"M {x},{r-20} C {x+30},{r-20} {x+46},{r-8} {x+55},{r} "
                 f"C {x+46},{r+8} {x+30},{r+20} {x},{r+20} Q {x+15},{r} {x},{r-20} Z")
        return (f'<path d="{d}" fill="#fff" stroke="#111" stroke-width="2" stroke-linejoin="round"/>'
                f'<text x="{x}" y="{r-25}" font-size="11" fill="#666" font-family="{FONT}">'
                f'{self.id} ({self.kind})</text>')


def _on_segment(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if x1 == x2:
        return x == x1 and min(y1, y2) <= y <= max(y1, y2)
    return y == y1 and min(x1, x2) <= x <= max(x1, x2)


def _on_wire(p, pts):
    return any(_on_segment(p, a, b) for a, b in zip(pts, pts[1:]))


class Schematic:
    def __init__(self, width, height, title, subtitle=""):
        self.w, self.h, self.title, self.subtitle = width, height, title, subtitle
        self.gates, self.wires, self.dots, self.terminals = {}, [], [], []
        self.texts, self.rail_names = [], {}

    # ---- construction helpers -------------------------------------------
    def add_gate(self, gid, kind, x, r):
        g = Gate(gid, kind, x, r)
        self.gates[gid] = g
        return g

    def wire(self, pts):
        self.wires.append([tuple(p) for p in pts])
        return len(self.wires) - 1

    def rail(self, name, x, y0, y1):
        idx = self.wire([(x, y0), (x, y1)])
        self.rail_names[idx] = name
        self.texts.append((x, y0 - 8, name, 'font-size="15" font-weight="bold" text-anchor="middle"'))

    def dot(self, p):
        self.dots.append(tuple(p))

    def tap(self, src_x, pin):
        """Horizontal wire from a vertical net at x=src_x to a gate pin, with junction dot."""
        self.wire([(src_x, pin[1]), pin])
        self.dot((src_x, pin[1]))

    def terminal(self, name, p, text=None):
        self.terminals.append((name, tuple(p), text or name))

    def label(self, x, y, text, anchor="start"):
        self.texts.append((x, y, text, f'font-size="11" fill="#333" font-style="italic" text-anchor="{anchor}"'))

    # ---- rendering --------------------------------------------------------
    def _path(self, pts, verticals, dots):
        d = f"M {pts[0][0]},{pts[0][1]}"
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if y1 == y2 and x1 != x2:
                lo, hi = min(x1, x2), max(x1, x2)
                xs = sorted({vx for vx, a, b in verticals
                             if lo + 0.5 < vx < hi - 0.5 and min(a, b) + 0.5 < y1 < max(a, b) - 0.5
                             and (vx, y1) not in dots}, reverse=(x2 < x1))
                for xc in xs:                      # little hop = crossing, no connection
                    right = x2 > x1
                    d += (f" L {xc-HOP if right else xc+HOP},{y1}"
                          f" A {HOP} {HOP} 0 0 {1 if right else 0} {xc+HOP if right else xc-HOP},{y1}")
            d += f" L {x2},{y2}"
        return d

    def svg(self, footer=()):
        dots = set(self.dots)
        verticals = [(a[0], a[1], b[1]) for w in self.wires for a, b in zip(w, w[1:]) if a[0] == b[0]]
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
             f'width="{self.w}" height="{self.h}" font-family="{FONT}">',
             f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>',
             f'<text x="24" y="32" font-size="20" font-weight="bold">{esc(self.title)}</text>']
        if self.subtitle:
            o.append(f'<text x="24" y="54" font-size="12" fill="#555">{esc(self.subtitle)}</text>')
        for w in self.wires:
            o.append(f'<path d="{self._path(w, verticals, dots)}" fill="none" stroke="#1a4fa0" '
                     f'stroke-width="1.8" stroke-linejoin="round"/>')
        for g in self.gates.values():
            o.append(g.svg())
        for p in dots:
            o.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="3.4" fill="#1a4fa0"/>')
        for name, p, text in self.terminals:
            o.append(f'<circle cx="{p[0]}" cy="{p[1]}" r="5" fill="#fff" stroke="#b00020" stroke-width="2"/>'
                     f'<text x="{p[0]+14}" y="{p[1]+5}" font-size="14" font-weight="bold" fill="#b00020">'
                     f'{esc(text)}</text>')
        for x, y, text, style in self.texts:
            o.append(f'<text x="{x}" y="{y}" {style}>{esc(text)}</text>')
        for i, line in enumerate(footer):
            o.append(f'<text x="24" y="{self.h-18-14*(len(footer)-1-i)}" font-size="11" fill="#444">{esc(line)}</text>')
        o.append("</svg>")
        return "\n".join(o)

    # ---- checks -------------------------------------------------------------
    def collisions(self):
        """Wire segments passing through a gate body (other than at its pins)."""
        bad = []
        for gi, w in enumerate(self.wires):
            for a, b in zip(w, w[1:]):
                for g in self.gates.values():
                    x0, y0, x1, y1 = g.body_box()
                    sx0, sx1 = sorted((a[0], b[0]))
                    sy0, sy1 = sorted((a[1], b[1]))
                    if sx1 > x0 and sx0 < x1 and sy1 > y0 and sy0 < y1:
                        bad.append((gi, g.id))
        return bad

    def extract(self):
        """
        Rebuild connectivity from the drawing.  Two wires are connected only if a
        junction dot sits on both.  Returns
            gates : {gate_id: (kind, driver_of_in1, driver_of_in2)}
            outs  : {terminal_name: driver}
        where a driver is ('in', 'A') or ('gate', 'G7').
        """
        n = len(self.wires)
        parent = list(range(n))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for dpt in self.dots:
            on = [i for i, w in enumerate(self.wires) if _on_wire(dpt, w)]
            if len(on) < 2:
                raise ValueError(f"junction dot {dpt} does not join two wires")
            for i in on[1:]:
                parent[find(i)] = find(on[0])

        def wire_at_end(p):
            hits = [i for i, w in enumerate(self.wires) if w[0] == p or w[-1] == p]
            if len(hits) != 1:
                raise ValueError(f"pin/terminal {p} touches {len(hits)} wire ends (expected 1)")
            return find(hits[0])

        drivers = {}                                    # net root -> set of drivers
        for idx, name in self.rail_names.items():
            drivers.setdefault(find(idx), set()).add(("in", name))
        for g in self.gates.values():
            drivers.setdefault(wire_at_end(g.out), set()).add(("gate", g.id))
        gates, outs = {}, {}

        def driver_of(root):
            ds = drivers.get(root, set())
            if len(ds) != 1:
                raise ValueError(f"net with drivers {ds}")
            return next(iter(ds))

        for g in self.gates.values():
            gates[g.id] = (g.kind, driver_of(wire_at_end(g.in1)), driver_of(wire_at_end(g.in2)))
        for name, p, _text in self.terminals:
            outs[name] = driver_of(wire_at_end(p))
        return gates, outs


# ==========================================================================
#  Complete circuit (hand-placed so shared nets are drawn once)
# ==========================================================================
def build_complete():
    S = Schematic(1330, 1050, "Complete circuit: 4-bit binary (ABCD) to 10 output lines L1-L10",
                  "Lk = 1 when the input value N >= k.  16 gates (10 OR, 6 AND), no inverters.  "
                  "Inputs A (MSB) ... D (LSB) on the left, outputs on the right.")
    xA, xB, xC, xD, xAR, xAB, xBC = 90, 130, 170, 210, 680, 420, 400
    S.rail("A", xA, 84, 450)
    S.rail("B", xB, 84, 570)
    S.rail("C", xC, 84, 920)
    S.rail("D", xD, 84, 880)
    g = {}

    def G(gid, kind, x, r):
        g[gid] = S.add_gate(gid, kind, x, r)
        return g[gid]

    # --- L1..L4 : A+B family ---------------------------------------------
    G("G1", "OR", 290, 110); S.tap(xA, g["G1"].in1); S.tap(xB, g["G1"].in2)
    G("G2", "OR", 290, 190); S.tap(xC, g["G2"].in1); S.tap(xD, g["G2"].in2)
    G("G3", "OR", 520, 190)
    G("G4", "OR", 520, 270); S.tap(xC, g["G4"].in2)
    G("G5", "AND", 290, 350); S.tap(xC, g["G5"].in1); S.tap(xD, g["G5"].in2)
    G("G6", "OR", 520, 350)
    S.wire([g["G1"].out, (xAB, 110), (xAB, 410), (1010, 410)])            # net A+B -> L4
    S.tap(xAB, g["G3"].in1); S.tap(xAB, g["G4"].in1); S.tap(xAB, g["G6"].in2)
    S.wire([g["G2"].out, (470, 190), (470, g["G3"].in2[1]), g["G3"].in2])
    S.wire([g["G5"].out, (470, 350), (470, g["G6"].in1[1]), g["G6"].in1])
    for gid, y in (("G3", 190), ("G4", 270), ("G6", 350)):
        S.wire([g[gid].out, (1010, y)])
    S.label(352, 104, "A+B"); S.label(352, 184, "C+D"); S.label(346, 344, "CD")

    # --- A feed for the right-hand gates ----------------------------------
    S.wire([(xA, 450), (xAR, 450), (xAR, 940)]); S.dot((xA, 450))

    # --- L5..L7 : BC, BD, BCD ----------------------------------------------
    G("G7", "AND", 290, 500); S.tap(xB, g["G7"].in1); S.tap(xC, g["G7"].in2)
    G("G8", "AND", 290, 580); S.tap(xB, g["G8"].in1); S.tap(xD, g["G8"].in2)
    S.wire([g["G7"].out, (xBC, 500), (xBC, 730)])                         # net BC
    G("G9", "OR", 450, 550); S.tap(xBC, g["G9"].in1)
    S.wire([g["G8"].out, (420, 580), (420, g["G9"].in2[1]), g["G9"].in2])
    G("G10", "OR", 720, 560)
    S.wire([g["G9"].out, g["G10"].in1]); S.tap(xAR, g["G10"].in2)
    G("G11", "OR", 720, 640); S.tap(xBC, g["G11"].in1); S.tap(xAR, g["G11"].in2)
    G("G12", "AND", 520, 720); S.tap(xD, g["G12"].in1); S.tap(xBC, g["G12"].in2)
    G("G13", "OR", 720, 720); S.tap(xAR, g["G13"].in1)
    S.wire([g["G12"].out, (640, 720), (640, g["G13"].in2[1]), g["G13"].in2])
    for gid, y in (("G10", 560), ("G11", 640), ("G13", 720)):
        S.wire([g[gid].out, (1010, y)])
    S.label(346, 494, "BC"); S.label(346, 574, "BD"); S.label(512, 544, "BC+BD"); S.label(578, 714, "BCD")

    # --- L8..L10 --------------------------------------------------------------
    S.wire([(xAR, 790), (1010, 790)]); S.dot((xAR, 790))
    G("G14", "OR", 290, 870); S.tap(xC, g["G14"].in1); S.tap(xD, g["G14"].in2)
    G("G15", "AND", 720, 870)
    S.wire([g["G14"].out, (600, 870), (600, g["G15"].in1[1]), g["G15"].in1]); S.tap(xAR, g["G15"].in2)
    G("G16", "AND", 720, 930); S.tap(xC, g["G16"].in1); S.tap(xAR, g["G16"].in2)
    S.wire([g["G15"].out, (1010, 870)]); S.wire([g["G16"].out, (1010, 930)])
    S.label(352, 864, "C+D")

    exprs = {1: "A+B+C+D", 2: "A+B+C", 3: "A+B+CD", 4: "A+B", 5: "A+BC+BD",
             6: "A+BC", 7: "A+BCD", 8: "A", 9: "A(C+D)", 10: "AC"}
    ys = {1: 190, 2: 270, 3: 350, 4: 410, 5: 560, 6: 640, 7: 720, 8: 790, 9: 870, 10: 930}
    for k, y in ys.items():
        pretty = exprs[k].replace("+", " + ")
        S.terminal(f"L{k}", (1010, y), f"L{k} = {pretty}")
    return S


COMPLETE_FOOTER = (
    "Blue dot = connection.  A wire that crosses another with a small hop (or no dot) is NOT connected.",
    "Gate IDs (G1-G16) match the gate table in docs/Digital_Logic_Design.md.  Net labels (italic) name internal signals.",
)


# ==========================================================================
#  Per-output circuits (tree layout generated from the netlist)
# ==========================================================================
def _hh(node):
    """Half-height of the drawing of a gate sub-tree."""
    if node[0] == "var":
        return 0
    kids = [c for c in node[3] if c[0] == "gate"]
    return 20 if not kids else max(20, max(_hh(c) + 30 + _hh(c) for c in kids))


def _depth(node):
    return 0 if node[0] == "var" else 1 + max(_depth(c) for c in node[3])


def build_output(k):
    """Per-output circuit.  Laid out twice: the first pass measures the drawing,
    the second pass re-centres it so the canvas has no dead space."""
    S = _layout_output(k, 200)
    if len(S.gates) == 0:
        return S
    top = min(y for _x, y, _t, _s in S.texts if _t in INPUTS) - 16
    bottom = max(max(g.r + 22 for g in S.gates.values()),
                 max(y for w in S.wires for _x, y in w))
    S = _layout_output(k, 200 - (top - 70))
    S.h = int(bottom - (top - 70) + 40)
    return S


def _layout_output(k, r0):
    name = f"L{k}"
    expr = PDF_EXPRESSIONS[k].replace("+", " + ")
    sub = f"Lit when N >= {k}.  Gate IDs match the complete circuit."
    net = output_net(name)
    if net in INPUTS:                                # L8: straight wire from A
        S = Schematic(520, 170, f"{name} = {expr}", f"Lit when N >= {k}: the output is simply input A (no gate).")
        S.rail("A", 70, 90, 120)
        S.wire([(70, 120), (330, 120)]); S.dot((70, 120))
        S.terminal(name, (330, 120), f"{name} = {expr}")
        return S
    root = cone(net)
    used = sorted({n for n in _leaves(root)})
    rails_x = {v: 70 + 40 * i for i, v in enumerate(used)}
    x0 = 70 + 40 * len(used) + 60
    colw = 150
    maxd = _depth(root)
    W = int(x0 + (maxd - 1) * colw + 55 + 80 + 190)
    S = Schematic(W, 700, f"{name} = {expr}", sub)
    taps = []

    def place(node, depth, r):
        _t, gid, kind, kids = node
        gate = S.add_gate(gid, kind, x0 + (maxd - 1 - depth) * colw, r)
        for kid, pin, side in zip(kids, (gate.in1, gate.in2), (-1, 1)):
            if kid[0] == "var":
                taps.append((kid[1], pin))
            else:
                cr = r + side * (_hh(kid) + 30)
                cg = place(kid, depth + 1, cr)
                mx = (cg.out[0] + pin[0]) // 2
                S.wire([cg.out, (mx, cr), (mx, pin[1]), pin])
        return gate

    rg = place(root, 0, r0)
    endx = rg.out[0] + 70
    S.wire([rg.out, (endx, r0)])
    S.terminal(name, (endx, r0), f"{name} = {expr}")
    ys = {v: [] for v in used}
    for v, pin in taps:
        ys[v].append(pin[1])
    for v in used:
        S.rail(v, rails_x[v], min(ys[v]) - 20, max(ys[v]))
    for v, pin in taps:
        S.tap(rails_x[v], pin)
    return S


def _leaves(node):
    if node[0] == "var":
        return [node[1]]
    return [x for c in node[3] for x in _leaves(c)]


# ==========================================================================
#  IC pin allocation drawing
# ==========================================================================
def ic_pin_nets():
    """{ic: {pin: net or None}} derived from IC_ALLOCATION and NETLIST."""
    res = {ic: {p: None for p in range(1, 15)} for ic in IC_TYPE}
    for ic, slot, gid in IC_ALLOCATION:
        _g, _kind, i1, i2, out = GATE_BY_ID[gid]
        p1, p2, po = SLOT_PINS[slot]
        res[ic][p1], res[ic][p2], res[ic][po] = i1, i2, out
    for ic in res:
        res[ic][7], res[ic][14] = "GND", "VCC"
    return res


def build_ic_svg():
    nets = ic_pin_nets()
    slots = {(ic, s): gid for ic, s, gid in IC_ALLOCATION}
    W, H, bw, bh, pitch = 1330, 700, 150, 7 * 34 + 24, 34
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>',
         '<text x="24" y="32" font-size="20" font-weight="bold">IC pin allocation (reference wiring plan)</text>',
         '<text x="24" y="54" font-size="12" fill="#555">Each pin shows the signal connected to it; pins with the same label are joined. '
         'Top view, notch up, pin 1 top-left. Unused gates: tie their inputs to GND.</text>']
    order = ["U1", "U2", "U3", "U4", "U5"]
    for n, ic in enumerate(order):
        cx = 150 + (n % 3) * 430
        cy = 100 + (n // 3) * 300
        o.append(f'<text x="{cx+bw/2}" y="{cy-12}" font-size="14" font-weight="bold" text-anchor="middle">'
                 f'{ic}: {esc(IC_PART[IC_TYPE[ic]])}</text>')
        o.append(f'<rect x="{cx}" y="{cy}" width="{bw}" height="{bh}" fill="#f4f6fa" stroke="#111" stroke-width="2"/>')
        o.append(f'<path d="M {cx+bw/2-12},{cy} A 12 12 0 0 0 {cx+bw/2+12},{cy}" fill="#fff" stroke="#111" stroke-width="2"/>')
        for pin in range(1, 15):
            left = pin <= 7
            y = cy + 22 + ((pin - 1) if left else (14 - pin)) * pitch
            x_in = cx if left else cx + bw
            x_out = cx - 16 if left else cx + bw + 16
            net = nets[ic][pin]
            o.append(f'<line x1="{x_in}" y1="{y}" x2="{x_out}" y2="{y}" stroke="#111" stroke-width="2"/>')
            o.append(f'<text x="{cx+12 if left else cx+bw-12}" y="{y+4}" font-size="11" fill="#555" '
                     f'text-anchor="{"start" if left else "end"}">{pin}</text>')
            if net is None:
                label, style = "unused", 'fill="#999" font-style="italic"'
            else:
                label = NET_LABEL.get(net, net)
                is_out = net.startswith("L") and net[1:].isdigit()
                style = 'fill="#b00020" font-weight="bold"' if is_out else ('fill="#111"' if net not in ("GND", "VCC") else 'fill="#444"')
            if net == "VCC":
                label = "VCC (+5 V)"
            o.append(f'<text x="{x_out-6 if left else x_out+6}" y="{y+4}" font-size="12" {style} '
                     f'text-anchor="{"end" if left else "start"}">{esc(label)}</text>')
        for slot, mid_pin in ((1, 2), (2, 5), (3, 9), (4, 12)):
            gid = slots.get((ic, slot))
            left = mid_pin <= 7
            y = cy + 22 + ((mid_pin - 1) if left else (14 - mid_pin)) * pitch
            txt = f"{gid}" if gid else "-"
            tx, anchor = (cx + 34, "start") if left else (cx + bw - 34, "end")   # label sits on the gate's own side
            o.append(f'<text x="{tx}" y="{y+4}" font-size="12" fill="#1a4fa0" text-anchor="{anchor}">{txt}</text>')
    o.append(f'<text x="24" y="{H-16}" font-size="11" fill="#444">Blue label inside each package = gate ID from the gate table. '
             f'Red = output lines L1-L10 (L4 is the A+B net on U1 pin 3; L8 is input A itself).</text>')
    o.append("</svg>")
    return "\n".join(o)


# ==========================================================================
#  K-maps
# ==========================================================================
GRAY = [0, 1, 3, 2]                      # 00 01 11 10 (same orientation as the PDF)
GROUP_COLORS = ["#d62728", "#2ca02c", "#1f77b4", "#ff7f0e", "#9467bd"]


def kmap_cell(m):
    return GRAY.index(m >> 2), GRAY.index(m & 3)        # (row, col)


def group_box(minterms):
    cells = [kmap_cell(m) for m in minterms]
    r0, r1 = min(c[0] for c in cells), max(c[0] for c in cells)
    c0, c1 = min(c[1] for c in cells), max(c[1] for c in cells)
    if (r1 - r0 + 1) * (c1 - c0 + 1) != len(cells):
        raise ValueError("group is not a plain rectangle")
    return r0, c0, r1, c1


def kmap_value(m, k):
    if m > 10:
        return "X"
    return str(expected_output(m, k))


def build_kmap(k):
    ox, oy, cw, ch = 170, 140, 100, 74
    terms = KMAP_GROUPS[k]
    H = oy + 4 * ch + 70 + 26 * len(terms) + 40
    W = ox + 4 * cw + 60
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="24" y="32" font-size="20" font-weight="bold">Karnaugh map for L{k}  (lit when N &gt;= {k})</text>',
         '<text x="24" y="54" font-size="12" fill="#555">1 = output on, 0 = output off, X = don\'t care (inputs 11-15 never occur). '
         'Red number in a cell = minterm index.</text>',
         f'<line x1="{ox-80}" y1="{oy-50}" x2="{ox}" y2="{oy}" stroke="#111" stroke-width="1.5"/>',
         f'<text x="{ox-30}" y="{oy-36}" font-size="14" font-weight="bold">CD</text>',
         f'<text x="{ox-72}" y="{oy-6}" font-size="14" font-weight="bold">AB</text>']
    col_names = ["C'D'", "C'D", "CD", "CD'"]
    row_names = ["A'B'", "A'B", "AB", "AB'"]
    for j, gv in enumerate(GRAY):
        o.append(f'<text x="{ox+j*cw+cw/2}" y="{oy-22}" font-size="14" text-anchor="middle">{col_names[j]}</text>')
        o.append(f'<text x="{ox+j*cw+cw/2}" y="{oy-6}" font-size="11" fill="#777" text-anchor="middle">{gv:02b}</text>')
    for i, gv in enumerate(GRAY):
        o.append(f'<text x="{ox-44}" y="{oy+i*ch+ch/2+2}" font-size="14" text-anchor="end">{row_names[i]}</text>')
        o.append(f'<text x="{ox-8}" y="{oy+i*ch+ch/2+2}" font-size="11" fill="#777" text-anchor="end">{gv:02b}</text>')
    texts = []
    for i in range(4):
        for j in range(4):
            m = (GRAY[i] << 2) | GRAY[j]
            v = kmap_value(m, k)
            fill = "#eaf6ea" if v == "1" else ("#f1f1f1" if v == "X" else "#fff")
            col = "#111" if v == "1" else "#888"
            o.append(f'<rect x="{ox+j*cw}" y="{oy+i*ch}" width="{cw}" height="{ch}" fill="{fill}" stroke="#333" stroke-width="1.5"/>')
            texts.append(f'<text x="{ox+j*cw+20}" y="{oy+i*ch+31}" font-size="11" fill="#c00">{m}</text>')
            texts.append(f'<text x="{ox+j*cw+cw/2}" y="{oy+i*ch+ch/2+10}" font-size="28" text-anchor="middle" '
                         f'fill="{col}" font-weight="{"bold" if v == "1" else "normal"}">{v}</text>')
    for gi, term in enumerate(terms):
        mts = term_minterms(term)
        r0, c0, r1, c1 = group_box(mts)
        inset = 4 + 4 * gi
        color = GROUP_COLORS[gi % len(GROUP_COLORS)]
        o.append(f'<rect x="{ox+c0*cw+inset}" y="{oy+r0*ch+inset}" width="{(c1-c0+1)*cw-2*inset}" '
                 f'height="{(r1-r0+1)*ch-2*inset}" rx="14" fill="{color}" fill-opacity="0.07" '
                 f'stroke="{color}" stroke-width="3"/>')
    o.extend(texts)
    ly = oy + 4 * ch + 36
    for gi, term in enumerate(terms):
        color = GROUP_COLORS[gi % len(GROUP_COLORS)]
        mts = ",".join(str(m) for m in sorted(term_minterms(term)))
        o.append(f'<rect x="24" y="{ly+gi*26-12}" width="26" height="14" rx="5" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="3"/>')
        o.append(f'<text x="60" y="{ly+gi*26}" font-size="13">Group {gi+1}: term {term}  (cells {mts})</text>')
    ey = ly + 26 * len(terms) + 14
    o.append(f'<text x="24" y="{ey}" font-size="17" font-weight="bold">L{k} = {esc(PDF_EXPRESSIONS[k].replace("+", " + "))}</text>')
    o.append("</svg>")
    return "\n".join(o)


# ==========================================================================
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(png=False):
    files = []
    for k in range(1, 11):
        files.append((f"diagrams/kmaps/L{k}_kmap.svg", build_kmap(k)))
        files.append((f"diagrams/circuits/L{k}_circuit.svg", build_output(k).svg()))
    files.append(("diagrams/circuits/complete_circuit.svg", build_complete().svg(COMPLETE_FOOTER)))
    files.append(("diagrams/circuits/ic_pin_allocation.svg", build_ic_svg()))
    for rel, text in files:
        write(os.path.join(ROOT, rel), text)
    print(f"wrote {len(files)} SVG files")
    if png:
        import cairosvg
        for rel, _t in files:
            out = os.path.join(ROOT, "diagrams", "png", os.path.basename(rel).replace(".svg", ".png"))
            cairosvg.svg2png(url=os.path.join(ROOT, rel), write_to=out, scale=1.6, background_color="white")
        print(f"wrote {len(files)} PNG files")


if __name__ == "__main__":
    main(png="--png" in sys.argv)
