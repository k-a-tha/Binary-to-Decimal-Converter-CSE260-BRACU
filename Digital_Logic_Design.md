# Digital Logic Design Report
## 4-bit Binary → Decimal (0–10) Converter

This report documents the complete combinational-logic design of the converter: truth table, Boolean functions, a Karnaugh map for every output, the gate-level circuit, the IC-level implementation, the checks that were run, and the points in the source material that needed interpretation.

The primary source is the original project PDF ([`docs/original/CSE260-Project-1.pdf`](original/CSE260-Project-1.pdf)). Nothing in the logic was invented: the truth table, the printed expressions and the gate schematic come from the PDF, and everything else was derived from them and then checked by program (`tools/verify_design.py`).

---

## Contents
1. [Project overview and objectives](#1-project-overview-and-objectives)
2. [Source material and how it was used](#2-source-material-and-how-it-was-used)
3. [Binary input and decimal output](#3-binary-input-and-decimal-output)
4. [Truth table](#4-truth-table)
5. [Output definitions and Boolean functions](#5-output-definitions-and-boolean-functions)
6. [Karnaugh maps, one per output](#6-karnaugh-maps-one-per-output)
7. [Final simplified expressions](#7-final-simplified-expressions)
8. [Gate-level implementation](#8-gate-level-implementation)
9. [IC-level implementation](#9-ic-level-implementation)
10. [How each valid input is converted (walk-through)](#10-how-each-valid-input-is-converted-walk-through)
11. [Unused (invalid) input combinations](#11-unused-invalid-input-combinations)
12. [Verification](#12-verification)
13. [Ambiguities found and how they were resolved](#13-ambiguities-found-and-how-they-were-resolved)
14. [Limitations and possible improvements](#14-limitations-and-possible-improvements)

---

## 1. Project overview and objectives

The circuit takes a 4-bit binary number **ABCD** (A is the most significant bit) and drives **ten output lines L1 … L10**. For a valid input value **N** (0 to 10) exactly **N** of the output lines are on, always L1 first. In other words the decimal value is shown as a bar of N lit outputs ("unary" or "thermometer" code). The PDF does not draw the output devices; in practice each line would drive an LED (see [limitations](#14-limitations-and-possible-improvements)).

Objectives:

* derive the exact input–output behaviour for N = 0 … 10;
* write each output as a Boolean function and minimise it with a Karnaugh map;
* implement all ten functions with the smallest practical set of two-input AND/OR gates;
* check that truth table, K-maps, expressions, schematic and IC allocation all describe the same circuit.

---

## 2. Source material and how it was used

The PDF has five pages (pages 4 and 5 are rotated by 90°).

| PDF page | Content | How it was used |
|:-:|:--|:--|
| 1 | Truth table (A, B, C, D → L1 … L10) for 11 rows, plus K-maps and expressions for L1 and L2 | Transcribed row by row into `tools/design_data.py`; the L1/L2 maps and expressions were cross-checked |
| 2 | Empty K-map grids for L3 … L8 with the simplified expression written under each | Expressions transcribed; the grids were **filled in from the truth table** (see §6) |
| 3 | Empty K-map grids for L9 and L10 with expressions | Same as above |
| 4 | Gate-level schematic: four input buses A–D, outputs L1 … L10 | Read gate by gate into the netlist (§8) and redrawn |
| 5 | IC-level sketch: five 14-pin packages (three OR, two AND) with outputs highlighted | Used to fix the number of ICs, gate-to-IC grouping and the output pin of each labelled gate (§9) |

Findings that matter for the rest of the report:

* The truth table is complete, regular and consistent with a simple rule: **Lk = 1 exactly when N ≥ k**.
* K-maps were only drawn out for L1 and L2. For L3 … L10 the PDF contains blank grids and the final expression. Those maps have been completed here and every expression in the PDF was re-derived and found correct.
* Inputs 11 … 15 are marked **X (don't care)** on the two K-maps the PDF fills in (L1 and L2).
* The schematic draws **two separate OR gates for C + D** (one in the L1 branch and one in the L9 branch). That is kept as drawn; merging them is listed as an optional improvement.
* The IC sketch does not print part numbers and its hand-drawn jumpers overlap in places, so the IC pin table in §9 is a *reference allocation* that is consistent with the schematic; §9 states which items are labelled in the PDF and which are inferred.
* Input switches, output indicators and power wiring are not drawn in the PDF.

---

## 3. Binary input and decimal output

| Signal | Meaning |
|:-:|:--|
| A, B, C, D | Input bits, A = 8, B = 4, C = 2, D = 1. N = 8A + 4B + 2C + D |
| L1 … L10 | Output lines. Lk is on when N ≥ k |
| N = 0 … 10 | Valid inputs: N outputs are lit |
| N = 11 … 15 | Never applied; treated as don't-care |

Reading the display: the decimal value equals the number of lit outputs.

| N | ABCD | L1 … L10 (● = on) |
|:-:|:-:|:--|
| 0 | `0000` | `○○○○○○○○○○` |
| 1 | `0001` | `●○○○○○○○○○` |
| 2 | `0010` | `●●○○○○○○○○` |
| 3 | `0011` | `●●●○○○○○○○` |
| 4 | `0100` | `●●●●○○○○○○` |
| 5 | `0101` | `●●●●●○○○○○` |
| 6 | `0110` | `●●●●●●○○○○` |
| 7 | `0111` | `●●●●●●●○○○` |
| 8 | `1000` | `●●●●●●●●○○` |
| 9 | `1001` | `●●●●●●●●●○` |
| 10 | `1010` | `●●●●●●●●●●` |

---

## 4. Truth table

Complete table for all 16 input combinations. Rows 0–10 are copied from page 1 of the PDF; rows 11–15 are don't-cares (X). The same table is stored in [`data/truth_table.csv`](../data/truth_table.csv).

| N | A | B | C | D | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | Lines on |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| 2 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 3 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| 4 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| 5 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 5 |
| 6 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 6 |
| 7 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 7 |
| 8 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 8 |
| 9 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 9 |
| 10 | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 10 |
| 11 | 1 | 0 | 1 | 1 | X | X | X | X | X | X | X | X | X | X | X |
| 12 | 1 | 1 | 0 | 0 | X | X | X | X | X | X | X | X | X | X | X |
| 13 | 1 | 1 | 0 | 1 | X | X | X | X | X | X | X | X | X | X | X |
| 14 | 1 | 1 | 1 | 0 | X | X | X | X | X | X | X | X | X | X | X |
| 15 | 1 | 1 | 1 | 1 | X | X | X | X | X | X | X | X | X | X | X |

---

## 5. Output definitions and Boolean functions

For a valid input N the output Lk is defined by

> **Lk = 1 if N ≥ k, otherwise 0**   (k = 1 … 10)

As a sum of minterms, with the don't-cares listed separately:


* **L1** = Σm(1, 2, 3, 4, 5, 6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L2** = Σm(2, 3, 4, 5, 6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L3** = Σm(3, 4, 5, 6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L4** = Σm(4, 5, 6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L5** = Σm(5, 6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L6** = Σm(6, 7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L7** = Σm(7, 8, 9, 10) + d(11, 12, 13, 14, 15)
* **L8** = Σm(8, 9, 10) + d(11, 12, 13, 14, 15)
* **L9** = Σm(9, 10) + d(11, 12, 13, 14, 15)
* **L10** = Σm(10) + d(11, 12, 13, 14, 15)

Because the ON-set of every output is a block of consecutive values ending at 10 and the don't-cares start immediately after it (11 … 15), every function can be written **without any complemented variable**. This is the key simplification: no NOT gates are needed anywhere in the circuit. (For example, if 11–15 were forced to 0, L8 would have to be AB'C'D', which needs three inverters.)

---

## 6. Karnaugh maps, one per output

**Conventions** (identical to the PDF): rows are AB = 00, 01, 11, 10 (A'B', A'B, AB, AB'); columns are CD = 00, 01, 11, 10 (C'D', C'D, CD, CD'). The small number in each cell is its minterm index. A map entry is **1** (output on), **0** (output off) or **X** (don't care, cells 11–15). Groups are rectangles of 1, 2, 4 or 8 cells containing only 1s and Xs; X cells are used only where they make a group larger. None of the groups below needs to wrap around the edge of the map.

Method for each group: look at which variables stay constant over the whole rectangle; those variables form the product term. Variables that take both values inside the group are eliminated.

Each section shows the filled map as a table and as a picture (`diagrams/kmaps/`). Only L1 and L2 were filled in on the PDF; the other eight were completed from the truth table.


### 6.1 Output L1  (on when N ≥ 1)

![K-map L1](../diagrams/kmaps/L1_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | **1**<sub>1</sub> | **1**<sub>3</sub> | **1**<sub>2</sub> |
| **01 (A'B)** | **1**<sub>4</sub> | **1**<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10. OFF cells: 0. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = B** (octet, cells 4, 5, 6, 7, 12, 13, 14, 15). B = 1 in every cell of the group; A, C, D take both values and are eliminated, so the group contributes the term **B**. Don't-care cells used: 12, 13, 14, 15.
3. **Group 3 = C** (octet, cells 2, 3, 6, 7, 10, 11, 14, 15). C = 1 in every cell of the group; A, B, D take both values and are eliminated, so the group contributes the term **C**. Don't-care cells used: 11, 14, 15.
4. **Group 4 = D** (octet, cells 1, 3, 5, 7, 9, 11, 13, 15). D = 1 in every cell of the group; A, B, C take both values and are eliminated, so the group contributes the term **D**. Don't-care cells used: 11, 13, 15.

**Simplified result:** L1 = **A + B + C + D**

**Why:** The only valid input that keeps L1 off is 0000, so L1 is simply the OR of the four input bits.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.2 Output L2  (on when N ≥ 2)

![K-map L2](../diagrams/kmaps/L2_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | **1**<sub>3</sub> | **1**<sub>2</sub> |
| **01 (A'B)** | **1**<sub>4</sub> | **1**<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 2, 3, 4, 5, 6, 7, 8, 9, 10. OFF cells: 0, 1. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = B** (octet, cells 4, 5, 6, 7, 12, 13, 14, 15). B = 1 in every cell of the group; A, C, D take both values and are eliminated, so the group contributes the term **B**. Don't-care cells used: 12, 13, 14, 15.
3. **Group 3 = C** (octet, cells 2, 3, 6, 7, 10, 11, 14, 15). C = 1 in every cell of the group; A, B, D take both values and are eliminated, so the group contributes the term **C**. Don't-care cells used: 11, 14, 15.

**Simplified result:** L2 = **A + B + C**

**Why:** The valid inputs that keep L2 off are 0000 and 0001, i.e. A = B = C = 0. A 1 on any of A, B or C therefore means N >= 2.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.3 Output L3  (on when N ≥ 3)

![K-map L3](../diagrams/kmaps/L3_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | **1**<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | **1**<sub>4</sub> | **1**<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 3, 4, 5, 6, 7, 8, 9, 10. OFF cells: 0, 1, 2. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = B** (octet, cells 4, 5, 6, 7, 12, 13, 14, 15). B = 1 in every cell of the group; A, C, D take both values and are eliminated, so the group contributes the term **B**. Don't-care cells used: 12, 13, 14, 15.
3. **Group 3 = CD** (quad, cells 3, 7, 11, 15). C, D = 1 in every cell of the group; A, B take both values and are eliminated, so the group contributes the term **CD**. Don't-care cells used: 11, 15.

**Simplified result:** L3 = **A + B + CD**

**Why:** With A = B = 0 the valid inputs are 0-3, and only 3 (CD = 11) must light L3. If A = 1 or B = 1 then N >= 4, so L3 is on.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.4 Output L4  (on when N ≥ 4)

![K-map L4](../diagrams/kmaps/L4_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | **1**<sub>4</sub> | **1**<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 4, 5, 6, 7, 8, 9, 10. OFF cells: 0, 1, 2, 3. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = B** (octet, cells 4, 5, 6, 7, 12, 13, 14, 15). B = 1 in every cell of the group; A, C, D take both values and are eliminated, so the group contributes the term **B**. Don't-care cells used: 12, 13, 14, 15.

**Simplified result:** L4 = **A + B**

**Why:** N >= 4 exactly when A = 1 or B = 1 (values 4-7 have B = 1, values 8-10 have A = 1).

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.5 Output L5  (on when N ≥ 5)

![K-map L5](../diagrams/kmaps/L5_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | **1**<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 5, 6, 7, 8, 9, 10. OFF cells: 0, 1, 2, 3, 4. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = BC** (quad, cells 6, 7, 14, 15). B, C = 1 in every cell of the group; A, D take both values and are eliminated, so the group contributes the term **BC**. Don't-care cells used: 14, 15.
3. **Group 3 = BD** (quad, cells 5, 7, 13, 15). B, D = 1 in every cell of the group; A, C take both values and are eliminated, so the group contributes the term **BD**. Don't-care cells used: 13, 15.

**Simplified result:** L5 = **A + BC + BD**

**Why:** A covers 8-10. Inside the B = 1 half (4-7), L5 is on for 5, 6, 7 but off for 4 (0100), so C or D must also be 1: B(C + D) = BC + BD.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.6 Output L6  (on when N ≥ 6)

![K-map L6](../diagrams/kmaps/L6_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | 0<sub>5</sub> | **1**<sub>7</sub> | **1**<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 6, 7, 8, 9, 10. OFF cells: 0, 1, 2, 3, 4, 5. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = BC** (quad, cells 6, 7, 14, 15). B, C = 1 in every cell of the group; A, D take both values and are eliminated, so the group contributes the term **BC**. Don't-care cells used: 14, 15.

**Simplified result:** L6 = **A + BC**

**Why:** A covers 8-10. Inside 4-7, L6 is on only for 6 and 7, which are the entries with C = 1: BC.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.7 Output L7  (on when N ≥ 7)

![K-map L7](../diagrams/kmaps/L7_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | 0<sub>5</sub> | **1**<sub>7</sub> | 0<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 7, 8, 9, 10. OFF cells: 0, 1, 2, 3, 4, 5, 6. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.
2. **Group 2 = BCD** (pair, cells 7, 15). B, C, D = 1 in every cell of the group; A take both values and are eliminated, so the group contributes the term **BCD**. Don't-care cells used: 15.

**Simplified result:** L7 = **A + BCD**

**Why:** A covers 8-10. Inside 4-7 only 7 (0111) lights L7, giving BCD. Don't-care 15 lets BCD be drawn as a pair {7, 15}.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.8 Output L8  (on when N ≥ 8)

![K-map L8](../diagrams/kmaps/L8_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | 0<sub>5</sub> | 0<sub>7</sub> | 0<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | **1**<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 8, 9, 10. OFF cells: 0, 1, 2, 3, 4, 5, 6, 7. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = A** (octet, cells 8, 9, 10, 11, 12, 13, 14, 15). A = 1 in every cell of the group; B, C, D take both values and are eliminated, so the group contributes the term **A**. Don't-care cells used: 11, 12, 13, 14, 15.

**Simplified result:** L8 = **A**

**Why:** N >= 8 exactly when A = 1. The don't-cares 11-15 let the three ON cells 8, 9, 10 grow into the full octet A = 1.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.9 Output L9  (on when N ≥ 9)

![K-map L9](../diagrams/kmaps/L9_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | 0<sub>5</sub> | 0<sub>7</sub> | 0<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | 0<sub>8</sub> | **1**<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 9, 10. OFF cells: 0, 1, 2, 3, 4, 5, 6, 7, 8. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = AC** (quad, cells 10, 11, 14, 15). A, C = 1 in every cell of the group; B, D take both values and are eliminated, so the group contributes the term **AC**. Don't-care cells used: 11, 14, 15.
2. **Group 2 = AD** (quad, cells 9, 11, 13, 15). A, D = 1 in every cell of the group; B, C take both values and are eliminated, so the group contributes the term **AD**. Don't-care cells used: 11, 13, 15.

**Simplified result:** L9 = **A(C + D)** (= AC + AD)

**Why:** Inside A = 1, input 8 (1000) must stay off while 9 (1001) and 10 (1010) are on, so L9 = A and (C or D) = AC + AD. Don't-care 11 sits in both pairs.

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


### 6.10 Output L10  (on when N ≥ 10)

![K-map L10](../diagrams/kmaps/L10_kmap.svg)

| AB \ CD | 00 (C'D') | 01 (C'D) | 11 (CD) | 10 (CD') |
|:--:|:--:|:--:|:--:|:--:|
| **00 (A'B')** | 0<sub>0</sub> | 0<sub>1</sub> | 0<sub>3</sub> | 0<sub>2</sub> |
| **01 (A'B)** | 0<sub>4</sub> | 0<sub>5</sub> | 0<sub>7</sub> | 0<sub>6</sub> |
| **11 (AB)** | X<sub>12</sub> | X<sub>13</sub> | X<sub>15</sub> | X<sub>14</sub> |
| **10 (AB')** | 0<sub>8</sub> | 0<sub>9</sub> | X<sub>11</sub> | **1**<sub>10</sub> |

* ON cells: 10. OFF cells: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9. Don't-care cells: 11–15.

**Grouping**

1. **Group 1 = AC** (quad, cells 10, 11, 14, 15). A, C = 1 in every cell of the group; B, D take both values and are eliminated, so the group contributes the term **AC**. Don't-care cells used: 11, 14, 15.

**Simplified result:** L10 = **AC**

**Why:** Inside A = 1 only 10 (1010) lights L10. Since 11 never occurs, C alone separates 10 from 8 and 9: AC (cells 10, 11, 14, 15).

*Check:* no group contains an OFF cell, every ON cell is covered, each group is a prime implicant (dropping any literal would cover an OFF cell) and each group covers an ON cell that no other group covers, so the expression is minimal. The result is identical to the expression printed in the PDF.


---

## 7. Final simplified expressions

| Output | Lit when | Simplified expression | Gates in its own cone |
|:-:|:-:|:--|:-:|
| L1 | N ≥ 1 | **A + B + C + D** | 3 |
| L2 | N ≥ 2 | **A + B + C** | 2 |
| L3 | N ≥ 3 | **A + B + CD** | 3 |
| L4 | N ≥ 4 | **A + B** | 1 |
| L5 | N ≥ 5 | **A + BC + BD** | 4 |
| L6 | N ≥ 6 | **A + BC** | 2 |
| L7 | N ≥ 7 | **A + BCD** | 3 |
| L8 | N ≥ 8 | **A** | wire (no gate) |
| L9 | N ≥ 9 | **A(C + D)** | 2 |
| L10 | N ≥ 10 | **AC** | 1 |

Cross-check against the PDF: all ten expressions written under the PDF's K-maps are identical to the ones derived above (L9 is printed as A(C + D), which equals AC + AD).

Every expression is built only from AND and OR of uncomplemented inputs. Each output with a smaller N threshold is "contained in" the next one (L10 ⊂ L9 ⊂ … ⊂ L1), which is why the expressions share so many terms (A + B, BC, …).

---

## 8. Gate-level implementation

### 8.1 Shared signals

Several sub-expressions appear in more than one output and are built once:

* **A + B** is used by L1, L2, L3 and is itself output **L4**;
* **BC** is used by L5 (through BC + BD), L6 and L7 (through BCD);
* **L8 is simply input A** (a wire, no gate).

Building each output separately would need 21 gates; with the sharing above the circuit uses **16 gates (10 OR + 6 AND)**.

### 8.2 Gate table

| Gate | Type | Input 1 | Input 2 | Output net | Purpose | IC / slot | Pins (in, in → out) |
|:-:|:-:|:-:|:-:|:-:|:--|:-:|:-:|
| G1 | OR | A | B | A+B | A+B (also output L4) | U1 / 1 | 1, 2 → 3 |
| G2 | OR | C | D | C+D | C+D for L1 | U1 / 2 | 4, 5 → 6 |
| G3 | OR | A+B | C+D | L1 | L1 | U1 / 3 | 9, 10 → 8 |
| G4 | OR | A+B | C | L2 | L2 | U1 / 4 | 12, 13 → 11 |
| G5 | AND | C | D | CD | CD for L3 | U4 / 1 | 1, 2 → 3 |
| G6 | OR | CD | A+B | L3 | L3 | U2 / 2 | 4, 5 → 6 |
| G7 | AND | B | C | BC | BC (shared by L5, L6, L7) | U4 / 3 | 9, 10 → 8 |
| G8 | AND | B | D | BD | BD for L5 | U4 / 4 | 12, 13 → 11 |
| G9 | OR | BC | BD | BC+BD | BC+BD for L5 | U3 / 1 | 1, 2 → 3 |
| G10 | OR | BC+BD | A | L5 | L5 | U3 / 2 | 4, 5 → 6 |
| G11 | OR | BC | A | L6 | L6 | U3 / 3 | 9, 10 → 8 |
| G12 | AND | D | BC | BCD | BCD for L7 | U5 / 1 | 1, 2 → 3 |
| G13 | OR | A | BCD | L7 | L7 | U3 / 4 | 12, 13 → 11 |
| G14 | OR | C | D | C+D | C+D for L9 (second copy) | U2 / 1 | 1, 2 → 3 |
| G15 | AND | C+D | A | L9 | L9 | U5 / 2 | 4, 5 → 6 |
| G16 | AND | C | A | L10 | L10 | U5 / 3 | 9, 10 → 8 |

Notes: the order of the two inputs of a gate is logically irrelevant. The PDF's schematic has two separate C + D gates (G2 for L1, G14 for L9); they are kept as drawn.

### 8.3 Depth

| Output | Gate levels (longest path) | Gates in cone |
|:-:|:-:|:--|
| L1 | 2 | G3, G1, G2 |
| L2 | 2 | G4, G1 |
| L3 | 2 | G6, G5, G1 |
| L4 | 1 | G1 |
| L5 | 3 | G10, G9, G7, G8 |
| L6 | 2 | G11, G7 |
| L7 | 3 | G13, G12, G7 |
| L8 | 0 | none (wire from A) |
| L9 | 2 | G15, G14 |
| L10 | 1 | G16 |

The longest path is **3 gate levels** (L5 and L7), so the output settles after three gate delays.

### 8.4 Individual circuits

Each output is drawn on its own with the same gate IDs as the complete circuit. Inputs run on vertical lines on the left; a dot means a connection.

**L1 = A + B + C + D**

![L1 circuit](../diagrams/circuits/L1_circuit.svg)

**L2 = A + B + C**

![L2 circuit](../diagrams/circuits/L2_circuit.svg)

**L3 = A + B + CD**

![L3 circuit](../diagrams/circuits/L3_circuit.svg)

**L4 = A + B**

![L4 circuit](../diagrams/circuits/L4_circuit.svg)

**L5 = A + BC + BD**

![L5 circuit](../diagrams/circuits/L5_circuit.svg)

**L6 = A + BC**

![L6 circuit](../diagrams/circuits/L6_circuit.svg)

**L7 = A + BCD**

![L7 circuit](../diagrams/circuits/L7_circuit.svg)

**L8 = A**

![L8 circuit](../diagrams/circuits/L8_circuit.svg)

**L9 = A(C + D)**

![L9 circuit](../diagrams/circuits/L9_circuit.svg)

**L10 = AC**

![L10 circuit](../diagrams/circuits/L10_circuit.svg)


### 8.5 Complete circuit

![Complete circuit](../diagrams/circuits/complete_circuit.svg)

A dot is a connection; a wire that crosses another with a small hop is *not* connected to it. The A feed that runs along the middle of the drawing (and down the right-hand side) is the same wire as input A on the left.

---

## 9. IC-level implementation

The PDF's IC sketch shows **five 14-pin packages: three OR (quad 2-input, 74xx32 pin-out) and two AND (quad 2-input, 74xx08 pin-out)**. The part numbers are not printed; the OR/AND labels and the highlighted output pins 3, 6, 8 and 11 identify the standard quad-gate pin-out:

| Gate slot | Input pins | Output pin |
|:-:|:-:|:-:|
| 1 | 1, 2 | 3 |
| 2 | 4, 5 | 6 |
| 3 | 9, 10 | 8 |
| 4 | 12, 13 | 11 |

GND is pin 7 and VCC is pin 14 on every package. 16 gates fit in 5 packages (20 slots, 4 unused).

**IC naming used in this repository:** U1 = the OR package carrying L1/L2 (top-right in the PDF sketch), U2 = the OR package carrying L3 (top-left), U3 = OR package carrying L5–L7 (bottom-right), U4 = AND package carrying BC/BD (top-centre), U5 = AND package carrying L9/L10 (bottom-left).

| IC | Slot | Gate | Function | Output pin | What the PDF sketch shows |
|:-:|:-:|:-:|:--|:-:|:--|
| U1 (OR) | 1 | G1 | A+B (also output L4) | 3 | Inferred; its output is the wire that feeds L4 |
| U1 (OR) | 2 | G2 | C+D for L1 | 6 | Inferred from schematic |
| U1 (OR) | 3 | G3 | L1 | 8 | **L1 labelled at pin 8** |
| U1 (OR) | 4 | G4 | L2 | 11 | **L2 labelled at pin 11** |
| U2 (OR) | 1 | G14 | C+D for L9 (second copy) | 3 | Output wire runs to the lower AND chip (L9 path) |
| U2 (OR) | 2 | G6 | L3 | 6 | **L3 labelled at pin 6** |
| U3 (OR) | 1 | G9 | BC+BD for L5 | 3 | Inferred from schematic |
| U3 (OR) | 2 | G10 | L5 | 6 | L5 labelled near pin 6 (marker partly covers it) |
| U3 (OR) | 3 | G11 | L6 | 8 | **L6 labelled at pin 8** |
| U3 (OR) | 4 | G13 | L7 | 11 | **L7 labelled at pin 11** |
| U4 (AND) | 1 | G5 | CD for L3 | 3 | Inferred (inputs C, D enter pins 1, 2) |
| U4 (AND) | 3 | G7 | BC (shared by L5, L6, L7) | 8 | **BC labelled at pin 8** |
| U4 (AND) | 4 | G8 | BD for L5 | 11 | **BD labelled at pin 11** |
| U5 (AND) | 1 | G12 | BCD for L7 | 3 | Inferred; output wire runs to the L7 OR gate |
| U5 (AND) | 2 | G15 | L9 | 6 | **L9 labelled at pin 6** |
| U5 (AND) | 3 | G16 | L10 | 8 | **L10 labelled at pin 8** |

**Reading the evidence column.** *Labelled* entries are output labels that are legible in the PDF's sketch at that package and pin. *Inferred* entries are gates whose package membership follows from the schematic and from the way the labelled gates fill the packages. The exact choice of slot among identical gates is not important electrically.

![IC pin allocation](../diagrams/circuits/ic_pin_allocation.svg)

Unused gate inputs (U2 slots 3–4, U4 slot 2, U5 slot 4) should be tied to GND so that they do not float.

---

## 10. How each valid input is converted (walk-through)

The table shows the value of every internal signal for each valid input. The outputs are then read straight off the last stage.

| N | ABCD | A+B | C+D | CD | BC | BD | BC+BD | BCD | L1 … L10 | Lines on |
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:--|:-:|
| 0 | `0000` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | `0000000000` | 0 |
| 1 | `0001` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | `1000000000` | 1 |
| 2 | `0010` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | `1100000000` | 2 |
| 3 | `0011` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | `1110000000` | 3 |
| 4 | `0100` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | `1111000000` | 4 |
| 5 | `0101` | 1 | 1 | 0 | 0 | 1 | 1 | 0 | `1111100000` | 5 |
| 6 | `0110` | 1 | 1 | 0 | 1 | 0 | 1 | 0 | `1111110000` | 6 |
| 7 | `0111` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | `1111111000` | 7 |
| 8 | `1000` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | `1111111100` | 8 |
| 9 | `1001` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | `1111111110` | 9 |
| 10 | `1010` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | `1111111111` | 10 |

Examples:

* **0 = 0000.** Every input is 0, so every gate output is 0 and no line is lit.
* **1 = 0001.** Only D is 1: C + D = 1, hence L1 = (A + B) + (C + D) = 1. A + B = 0, C = 0, CD = 0, so L2 and L3 stay 0.
* **5 = 0101.** B = 1 and D = 1: A + B = 1 turns on L1–L4; BD = 1 turns on BC + BD and therefore L5. BC = 0 keeps L6 off.
* **7 = 0111.** BC = BD = 1 and BCD = 1, so L5, L6 and L7 turn on together with L1–L4. A = 0 keeps L8–L10 off.
* **8 = 1000.** A = 1: A + B = 1 and the "A + …" gates (G10, G11, G13) turn on L5–L7, L8 follows A directly. C = 0 and D = 0 keep L9 (A(C + D)) and L10 (AC) off.
* **10 = 1010.** A = 1 and C = 1: C + D = 1 so L9 = A(C + D) = 1, and AC = 1 gives L10. All ten lines are on.

---

## 11. Unused (invalid) input combinations

Inputs 11 … 15 (1011 … 1111) are never meant to be applied. They were treated as don't-cares so the expressions could be minimal, so the circuit's response to them is whatever the simplified gates produce:

| N | ABCD | L1 … L10 | Lines on | Looks like |
|:-:|:-:|:--|:-:|:-:|
| 11 | `1011` | `1111111111` | 10 | 10 |
| 12 | `1100` | `1111111100` | 8 | 8 |
| 13 | `1101` | `1111111110` | 9 | 9 |
| 14 | `1110` | `1111111111` | 10 | 10 |
| 15 | `1111` | `1111111111` | 10 | 10 |

Observations:

* 11, 14 and 15 light all ten lines, 13 lights nine and 12 lights eight. These patterns are **not** a decimal conversion and are not flagged.
* The behaviour is deterministic and was confirmed by simulation, but it is a by-product of the minimisation, not a designed feature.
* If the application needs to reject invalid inputs, an error flag can be added cheaply: **E = A(B + CD) = AB + ACD** is 1 exactly for 11 … 15 and 0 for 0 … 10 (checked exhaustively). It can reuse the existing CD gate G5, so it costs two extra gates (one OR, one AND).

---

## 12. Verification

`python3 tools/verify_design.py` (standard library only) performs the following checks; its output is saved in [`verification_log.txt`](verification_log.txt).

| # | Check | Result |
|:-:|:--|:-:|
| 1 | PDF truth table has the 11 valid rows; every entry equals the rule *Lk = 1 ⇔ N ≥ k* (110 entries); number of lit lines = N; CSV file identical to the table | Pass |
| 2 | Each of the 10 PDF expressions reproduces the truth table for N = 0 … 10 | Pass |
| 3 | K-map groups: only ON/don't-care cells, all ON cells covered, prime, irredundant, and equal to the PDF expression on all 16 inputs | Pass (10/10 outputs) |
| 4 | Gate netlist simulated for all 16 inputs; inputs 0 … 10 match the table; 10 OR + 6 AND, no NOT gates | Pass |
| 5 | **Netlist re-extracted from the drawn SVG geometry** (wires and junction dots) for the complete circuit and the 10 individual circuits, compared gate by gate with the netlist, simulated, and tested for wires passing through gate bodies | Pass (11/11 drawings) |
| 6 | IC allocation: every gate in exactly one legal slot, outputs on pins 3/6/8/11, pin-level simulation reproduces all 11 valid rows | Pass |

Check 5 means the circuit pictures in this repository are not merely illustrations: the connectivity that is drawn is the connectivity that was simulated.

To reproduce: `python3 tools/verify_design.py` (exit status 0 = all passed) and `python3 tools/generate_diagrams.py --png` to regenerate every diagram (PNG output needs `pip install cairosvg`; SVG needs nothing).

---

## 13. Ambiguities found and how they were resolved

| # | Observation in the source | Resolution |
|:-:|:--|:--|
| 1 | K-map grids for L3 … L10 are blank in the PDF | Filled from the truth table; groups derived and proven prime/irredundant; each result equals the expression the PDF prints |
| 2 | "Decimal output 0–10" is not shown on any display in the PDF; the table uses ten lines L1–L10 | Interpreted from the table itself as a bar of N lit lines (thermometer code) |
| 3 | The PDF draws two identical C + D OR gates | Kept as drawn (preserves the original design); noted as an optimisation |
| 4 | IC sketch: no part numbers; some jumpers overlap and are hard to follow pin by pin | Part type taken from the OR/AND labels and the highlighted pins 3/6/8/11. The pin table is a reference allocation consistent with the schematic; only labelled pins are claimed as taken from the PDF. The hand-drawn jumper from the CD gate to the L3 OR gate is the least clear part of the sketch |
| 5 | Input switches, output indicators, resistors and power are not drawn | Not invented; listed as unspecified in the README |
| 6 | Behaviour for 11–15 is not specified | Documented from simulation (§11); error-flag improvement proposed |

---

## 14. Limitations and possible improvements

**Limitations**

* The display is a bar of lit lines, not a digit; reading "10" means counting ten lit lines.
* Inputs 11–15 produce unflagged, meaningless patterns (§11).
* Purely combinational: no latch, enable or debounce for the input switches.
* Output current limiting (e.g. LED resistors) and the exact output devices are outside the supplied material.
* Three levels of logic means three gate delays at the slowest outputs (relevant only at high speed).
* The IC pin table is a reference allocation, not a transcription of every hand-drawn jumper.

**Possible improvements**

* Share one C + D gate between L1 and L9 (saves one OR gate; package count stays at 5).
* Add the error flag E = A(B + CD) for invalid inputs (two gates, reusing G5).
* Add a 7-segment/BCD output stage if a decimal digit display is wanted.
* Add input buffering or debouncing if mechanical switches are used.
* Provide a simulator file (for example Logisim-evolution or a Verilog model) so the circuit can be run without hardware.
