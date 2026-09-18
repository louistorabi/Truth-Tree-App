"""
main.py

FastAPI backend for the Truth Table + Truth Tree (semantic tableau) generator.

Supported syntax:
- Variables: p, q, r, A, foo, x1
- NOT: ~ or !
- AND: & or ^
- OR: | or v
- IMPLIES: ->
- IFF: <->

Spaces are ignored.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Set, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =============================
# FastAPI setup
# =============================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TruthTableRequest(BaseModel):
    formula: str

class TruthTreeRequest(BaseModel):
    formula: str

@app.get("/health")
def health():
    return {"ok": True}

# =============================
# Tokenizer
# =============================

Token = Tuple[str, str]  # (type, value)

def tokenize(s: str) -> List[Token]:
    i = 0
    tokens: List[Token] = []

    while i < len(s):
        c = s[i]

        if c.isspace():
            i += 1
            continue

        if s.startswith("<->", i):
            tokens.append(("OP", "<->"))
            i += 3
            continue

        if s.startswith("->", i):
            tokens.append(("OP", "->"))
            i += 2
            continue

        if c == "(":
            tokens.append(("LPAREN", c))
            i += 1
            continue

        if c == ")":
            tokens.append(("RPAREN", c))
            i += 1
            continue

        if c in ("~", "!", "&", "|", "^", "v"):
            if c == "^":
                tokens.append(("OP", "&"))
            elif c == "v":
                tokens.append(("OP", "|"))
            else:
                tokens.append(("OP", c))
            i += 1
            continue

        if c.isalpha() or c == "_":
            j = i + 1
            while j < len(s) and (s[j].isalnum() or s[j] == "_"):
                j += 1
            tokens.append(("IDENT", s[i:j]))
            i = j
            continue

        raise ValueError(f"Unexpected character: {c}")

    tokens.append(("EOF", "EOF"))
    return tokens

# =============================
# AST Nodes
# =============================

@dataclass(frozen=True)
class Node:
    pass

@dataclass(frozen=True)
class Var(Node):
    name: str

@dataclass(frozen=True)
class Not(Node):
    child: Node

@dataclass(frozen=True)
class Bin(Node):
    op: str
    left: Node
    right: Node

# =============================
# Parser
# =============================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def eat(self, ttype: str, value: Optional[str] = None):
        tok = self.peek()
        if tok[0] != ttype or (value and tok[1] != value):
            raise ValueError(f"Expected {ttype} {value}, got {tok}")
        self.pos += 1
        return tok

    def parse(self) -> Node:
        node = self.parse_iff()
        self.eat("EOF")
        return node

    def parse_iff(self):
        node = self.parse_implies()
        while self.peek() == ("OP", "<->"):
            self.eat("OP", "<->")
            node = Bin("<->", node, self.parse_implies())
        return node

    def parse_implies(self):
        node = self.parse_or()
        if self.peek() == ("OP", "->"):
            self.eat("OP", "->")
            node = Bin("->", node, self.parse_implies())
        return node

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == ("OP", "|"):
            self.eat("OP", "|")
            node = Bin("|", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.peek() == ("OP", "&"):
            self.eat("OP", "&")
            node = Bin("&", node, self.parse_not())
        return node

    def parse_not(self):
        if self.peek()[1] in ("~", "!"):
            self.eat("OP")
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok[0] == "IDENT":
            self.eat("IDENT")
            return Var(tok[1])
        if tok[0] == "LPAREN":
            self.eat("LPAREN")
            node = self.parse_iff()
            self.eat("RPAREN")
            return node
        raise ValueError("Expected variable or '('")

def parse_formula(s: str) -> Node:
    return Parser(tokenize(s)).parse()

# =============================
# Truth Table
# =============================

def collect_vars(node: Node, acc=None):
    if acc is None:
        acc = set()
    if isinstance(node, Var):
        acc.add(node.name)
    elif isinstance(node, Not):
        collect_vars(node.child, acc)
    elif isinstance(node, Bin):
        collect_vars(node.left, acc)
        collect_vars(node.right, acc)
    return acc

def eval_node(node: Node, env: Dict[str, bool]) -> bool:
    if isinstance(node, Var):
        return env[node.name]
    if isinstance(node, Not):
        return not eval_node(node.child, env)
    if isinstance(node, Bin):
        a = eval_node(node.left, env)
        b = eval_node(node.right, env)
        if node.op == "&":
            return a and b
        if node.op == "|":
            return a or b
        if node.op == "->":
            return (not a) or b
        if node.op == "<->":
            return a == b
    raise ValueError("Bad AST")

@app.post("/truth-table")
def truth_table(req: TruthTableRequest):
    ast = parse_formula(req.formula)
    vars_ = sorted(collect_vars(ast))
    rows = []

    for values in product([False, True], repeat=len(vars_)):
        env = dict(zip(vars_, values))
        rows.append({
            "assignment": env,
            "value": eval_node(ast, env)
        })

    return {"variables": vars_, "rows": rows}

# =============================
# Truth Tree (Tableau)
# =============================

def ast_to_str(n: Node) -> str:
    if isinstance(n, Var):
        return n.name
    if isinstance(n, Not):
        return f"~{ast_to_str(n.child)}"
    if isinstance(n, Bin):
        return f"({ast_to_str(n.left)} {n.op} {ast_to_str(n.right)})"

def eliminate_implications(n: Node) -> Node:
    if isinstance(n, Var):
        return n
    if isinstance(n, Not):
        return Not(eliminate_implications(n.child))
    if isinstance(n, Bin):
        a = eliminate_implications(n.left)
        b = eliminate_implications(n.right)
        if n.op == "->":
            return Bin("|", Not(a), b)
        if n.op == "<->":
            return Bin("|", Bin("&", a, b), Bin("&", Not(a), Not(b)))
        return Bin(n.op, a, b)

def to_nnf(n: Node) -> Node:
    n = eliminate_implications(n)

    if isinstance(n, Var):
        return n
    if isinstance(n, Not):
        if isinstance(n.child, Var):
            return n
        if isinstance(n.child, Not):
            return to_nnf(n.child.child)
        if isinstance(n.child, Bin):
            op = "|" if n.child.op == "&" else "&"
            return Bin(op, to_nnf(Not(n.child.left)), to_nnf(Not(n.child.right)))
    if isinstance(n, Bin):
        return Bin(n.op, to_nnf(n.left), to_nnf(n.right))

def expand(formulas, lits):
    if not formulas:
        return {"label": ", ".join(sorted(lits)), "children": []}

    f, *rest = formulas

    if isinstance(f, Var):
        if f.name in lits:
            return {"label": "× closed", "children": []}
        return expand(rest, lits | {f.name})

    if isinstance(f, Not) and isinstance(f.child, Var):
        if f.child.name in lits:
            return {"label": "× closed", "children": []}
        return expand(rest, lits | {f"~{f.child.name}"})

    if isinstance(f, Bin) and f.op == "&":
        return expand([f.left, f.right] + rest, lits)

    if isinstance(f, Bin) and f.op == "|":
        return {
            "label": ast_to_str(f),
            "children": [
                expand([f.left] + rest, lits),
                expand([f.right] + rest, lits),
            ]
        }

    return expand(rest, lits)

@app.post("/truth-tree")
def truth_tree(req: TruthTreeRequest):
    ast = parse_formula(req.formula)
    nnf = to_nnf(ast)
    tree = expand([nnf], set())
    return {
        "formula": req.formula,
        "nnf": ast_to_str(nnf),
        "tree": tree
    }

# -----------------------------
# Argument truth tree endpoint:
# premises + NOT(conclusion)
# -----------------------------

class ArgumentTreeRequest(BaseModel):
    premises: List[str]
    conclusion: str


def negate(node: Node) -> Node:
    """Wrap a node in a NOT (used for negating the conclusion)."""
    return Not(node)


def expand_tableau_with_numbering(
    formulas: List[Node],
    lits: Set[Tuple[str, bool]],
    next_line: int,
    source_label: str
) -> dict:
    """
    Very simple numbered tableau:
    Each expansion step creates a node with:
      - line: an integer (like (4))
      - label: string formula or status
      - note: short annotation like [premise], [negate conclusion], [∨], etc.
      - closed: bool
      - children: [] / [child] / [left,right]
    """

    # absorb literals into lits set
    remaining: List[Node] = []
    new_lits = set(lits)

    def lit_from_node(n: Node):
        if isinstance(n, Var):
            return (n.name, True)
        if isinstance(n, Not) and isinstance(n.child, Var):
            return (n.child.name, False)
        return None

    def is_closed(ls: Set[Tuple[str, bool]]) -> bool:
        pos = {v for (v, s) in ls if s}
        neg = {v for (v, s) in ls if not s}
        return len(pos.intersection(neg)) > 0

    for f in formulas:
        lit = lit_from_node(f)
        if lit is not None:
            new_lits.add(lit)
        else:
            remaining.append(f)

    # closed branch leaf
    if is_closed(new_lits):
        return {
            "line": next_line,
            "label": "× closed",
            "note": "",
            "closed": True,
            "children": [],
            "next_line": next_line + 1,
        }

    # open branch leaf
    if not remaining:
        lits_str = ", ".join([v if s else f"~{v}" for (v, s) in sorted(new_lits)])
        return {
            "line": next_line,
            "label": f"✓ open: {lits_str}",
            "note": "",
            "closed": False,
            "children": [],
            "next_line": next_line + 1,
        }

    # pick next formula to expand
    f = remaining[0]
    rest = remaining[1:]
    label = ast_to_str(f)

    # alpha (&): add both on same branch
    if isinstance(f, Bin) and f.op == "&":
        node = {
            "line": next_line,
            "label": label,
            "note": source_label or "[∧]",
            "closed": False,
            "children": [],
        }
        child = expand_tableau_with_numbering([f.left, f.right] + rest, new_lits, next_line + 1, "[∧]")
        node["children"] = [strip_next_line(child)]
        node["closed"] = node["children"][0]["closed"]
        node["next_line"] = child["next_line"]
        return node

    # beta (|): branch
    if isinstance(f, Bin) and f.op == "|":
        node = {
            "line": next_line,
            "label": label,
            "note": source_label or "[∨]",
            "closed": False,
            "children": [],
        }
        left = expand_tableau_with_numbering([f.left] + rest, new_lits, next_line + 1, "[∨]")
        right = expand_tableau_with_numbering([f.right] + rest, new_lits, left["next_line"], "[∨]")

        node["children"] = [strip_next_line(left), strip_next_line(right)]
        node["closed"] = node["children"][0]["closed"] and node["children"][1]["closed"]
        node["next_line"] = right["next_line"]
        return node

    # if it isn't alpha/beta (should be rare once in NNF), just skip it downward
    node = {
        "line": next_line,
        "label": label,
        "note": source_label or "",
        "closed": False,
        "children": [],
    }
    child = expand_tableau_with_numbering(rest, new_lits, next_line + 1, "")
    node["children"] = [strip_next_line(child)]
    node["closed"] = node["children"][0]["closed"]
    node["next_line"] = child["next_line"]
    return node


def strip_next_line(tree_node: dict) -> dict:
    """Remove internal 'next_line' field before sending to frontend."""
    if "next_line" in tree_node:
        tree_node = dict(tree_node)
        tree_node.pop("next_line", None)
    if "children" in tree_node and isinstance(tree_node["children"], list):
        tree_node["children"] = [strip_next_line(c) for c in tree_node["children"]]
    return tree_node


@app.post("/argument-tree")
def argument_tree(req: ArgumentTreeRequest):
    """
    Input:
      premises: ["P v Q", "P -> R", "~Q v R"]
      conclusion: "R"

    We build: premises + NOT(conclusion), convert to NNF, then expand tableau.
    """
    try:
        premises = [p.strip() for p in req.premises if p.strip()]
        if len(premises) == 0:
            return {"error": "At least 1 premise is required.", "tree": None}

        if not req.conclusion.strip():
            return {"error": "Conclusion is required.", "tree": None}

        # parse + NNF
        prem_asts = [to_nnf(parse_formula(p)) for p in premises]
        concl_ast = to_nnf(parse_formula(req.conclusion))
        neg_concl = to_nnf(negate(concl_ast))

        # initial lines for display (1..n premises, then negated conclusion)
        initial_lines = []
        line_no = 1
        for p in prem_asts:
            initial_lines.append({"line": line_no, "label": ast_to_str(p), "note": "[premise]"})
            line_no += 1

        initial_lines.append({"line": line_no, "label": ast_to_str(neg_concl), "note": "[negate conclusion]"})
        line_no += 1

        # Expand tableau starting with all initial formulas on the branch
        tree = expand_tableau_with_numbering(prem_asts + [neg_concl], set(), line_no, "[start]")

        # Return both: the numbered starting lines + the tree
        return {
            "premises": premises,
            "conclusion": req.conclusion,
            "initial": initial_lines,
            "tree": strip_next_line(tree),
        }

    except Exception as e:
        return {"error": str(e), "tree": None}
