"""Binary tree model: level-order construction, view layout, and traversals."""
from collections import deque

MAX_NODES = 2000


class Node:
    __slots__ = ("label", "left", "right")

    def __init__(self, label):
        self.label, self.left, self.right = label, None, None


def build_level_order(items):
    """Build from a level-order list where None marks a missing node.

    A null keeps its slot, but its children are not stored, so each entry
    maps to exactly one position. Expects items[0] to be a label.
    Returns (root, entries_used).
    """
    root = Node(items[0])
    queue, i = deque([root]), 1
    while queue and i < len(items):
        node = queue.popleft()
        for side in ("left", "right"):
            if i < len(items):
                if items[i] is not None:
                    child = Node(items[i])
                    setattr(node, side, child)
                    queue.append(child)
                i += 1
    return root, i


def preorder(root):
    out, stack = [], [root]
    while stack:
        n = stack.pop()
        if n:
            out.append(n.label)
            stack.append(n.right)
            stack.append(n.left)
    return out


def inorder(root):
    out, stack, cur = [], [], root
    while stack or cur:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        out.append(cur.label)
        cur = cur.right
    return out


def postorder(root):
    out, stack = [], [(root, False)]
    while stack:
        n, done = stack.pop()
        if n is None:
            continue
        if done:
            out.append(n.label)
        else:
            stack.append((n, True))
            stack.append((n.right, False))
            stack.append((n.left, False))
    return out


def layout(root):
    """Flatten the tree for the SVG view.

    x is the in-order rank, so every left child sits left of its parent and
    every right child sits right of it. y is the depth. Child fields are
    indexes into the nodes list, or None for a missing branch.
    """
    if root is None:
        return {"nodes": [], "count": 0, "height": 0}
    rank, stack, cur = {}, [], root
    while stack or cur:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        rank[id(cur)] = len(rank)
        cur = cur.right

    order, depth, i = [root], {id(root): 0}, 0
    while i < len(order):
        n = order[i]
        i += 1
        for c in (n.left, n.right):
            if c is not None:
                depth[id(c)] = depth[id(n)] + 1
                order.append(c)

    index = {id(n): k for k, n in enumerate(order)}

    def ref(c):
        return index[id(c)] if c is not None else None

    nodes = [
        {"label": n.label, "x": rank[id(n)], "y": depth[id(n)],
         "left": ref(n.left), "right": ref(n.right)}
        for n in order
    ]
    return {"nodes": nodes, "count": len(order), "height": max(depth.values()) + 1}
