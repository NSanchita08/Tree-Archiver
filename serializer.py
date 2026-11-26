"""Lossless archive format: preorder traversal with explicit null markers.

Tokens are comma-separated. Each token is a node label or '#' for a missing
child. Example: A,B,#,D,#,#,C,#,#  is A with left child B (whose right child
is D) and right child C. An empty tree is a single '#'.
Labels: 1-16 characters from A-Z, a-z, 0-9, '_', '.', '-'.
"""
import re

from tree import MAX_NODES, Node

NULL = "#"
LABEL_RE = re.compile(r"[A-Za-z0-9_.\-]{1,16}")


class ArchiveError(Exception):
    def __init__(self, message, position=None, suggestion=None):
        super().__init__(message)
        self.message, self.position, self.suggestion = message, position, suggestion


def serialize(root):
    out, stack = [], [root]
    while stack:
        node = stack.pop()
        if node is None:
            out.append(NULL)
        else:
            out.append(node.label)
            stack.append(node.right)
            stack.append(node.left)
    return ",".join(out)


def check(text):
    """Validate archive text without changing it. Returns the token list.

    Every label needs two child slots and every '#' fills one slot, so the
    archive is complete exactly when no slots are left open.
    """
    if text is None or not text.strip():
        raise ArchiveError("The archive is empty.",
                           suggestion="Paste archive text or upload a .txt file.")
    tokens = [t.strip() for t in text.strip().split(",")]
    open_slots, nodes = 1, 0
    for pos, tok in enumerate(tokens, start=1):
        if open_slots == 0:
            raise ArchiveError(f"Extra data after the tree is complete: '{tok}'.", pos,
                               f"Delete tokens from position {pos} to the end.")
        if tok == NULL:
            open_slots -= 1
        elif LABEL_RE.fullmatch(tok):
            nodes += 1
            if nodes > MAX_NODES:
                raise ArchiveError(f"The tree has more than {MAX_NODES} nodes.", pos,
                                   "Reduce the number of nodes.")
            open_slots += 1
        else:
            raise ArchiveError(f"Invalid token '{tok}'. Use a label or '#'.", pos,
                               f"Replace token {pos} with a valid label or '#'.")
    if open_slots:
        raise ArchiveError(f"Incomplete archive: {open_slots} null marker(s) '#' are missing.",
                           len(tokens) + 1, f"Append {open_slots} '#' token(s).")
    return tokens


def restore(text):
    """Rebuild the exact tree from archive text. Validates first, never repairs."""
    tokens = check(text)
    root, slots = None, [(None, None)]  # pending (parent, side) slots, LIFO
    for tok in tokens:
        parent, side = slots.pop()
        node = None if tok == NULL else Node(tok)
        if parent is None:
            root = node
        elif side == "left":
            parent.left = node
        else:
            parent.right = node
        if node is not None:
            slots.append((node, "right"))
            slots.append((node, "left"))
    return root


def same_structure(a, b):
    """Compare two trees node by node: labels, and presence of every branch.

    Returns (identical, message). Traversal output is never used.
    """
    stack, count = [(a, b, "root")], 0
    while stack:
        x, y, path = stack.pop()
        if x is None and y is None:
            continue
        if (x is None) != (y is None):
            return False, f"Mismatch at {path}: one tree has a child there and the other has a missing branch."
        if x.label != y.label:
            return False, f"Mismatch at {path}: label '{x.label}' differs from '{y.label}'."
        count += 1
        stack.append((x.left, y.left, path + ".left"))
        stack.append((x.right, y.right, path + ".right"))
    return True, f"Structurally identical: {count} nodes, same labels, same left and right branches."
