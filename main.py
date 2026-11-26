
from collections import deque


# =====================================
# 1. BINARY TREE NODE
# =====================================

class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None


# =====================================
# 2. CREATE TREE FROM LEVEL ORDER INPUT
# =====================================

def create_tree(values):

    if not values:
        return None

    if values[0] == "#":
        if len(values) != 1:
            raise ValueError("Invalid tree: root is empty")
        return None

    nodes = []

    for value in values:
        if value == "#":
            nodes.append(None)
        else:
            if "," in value or "#" in value:
                raise ValueError("Invalid node label")
            nodes.append(Node(value))

    for i in range(len(nodes)):

        if nodes[i] is None:
            continue

        left_index = 2 * i + 1
        right_index = 2 * i + 2

        if left_index < len(nodes):
            nodes[i].left = nodes[left_index]

        if right_index < len(nodes):
            nodes[i].right = nodes[right_index]

    # A child cannot exist without its parent
    for i in range(1, len(nodes)):
        parent_index = (i - 1) // 2

        if nodes[i] is not None and nodes[parent_index] is None:
            raise ValueError("Invalid tree: child has no parent")

    return nodes[0]


# =====================================
# 3. SERIALIZATION (TREE TO TEXT)
# =====================================

def serialize(root):

    result = []

    def preorder(node):

        if node is None:
            result.append("#")
            return

        result.append(node.data)

        preorder(node.left)
        preorder(node.right)

    preorder(root)

    return ",".join(result)


# =====================================
# 4. DESERIALIZATION (TEXT TO TREE)
# =====================================

def deserialize(text):

    if not text:
        raise ValueError("Empty export data")

    values = text.split(",")

    if any(value == "" for value in values):
        raise ValueError("Invalid empty token")

    index = 0

    def build():

        nonlocal index

        if index >= len(values):
            raise ValueError("Incomplete export data")

        value = values[index]
        index += 1

        if value == "#":
            return None

        if any(ch.isspace() for ch in value) or "#" in value:
            raise ValueError("Invalid node label")

        node = Node(value)

        node.left = build()
        node.right = build()

        return node

    root = build()

    if index != len(values):
        raise ValueError("Extra data found in export")

    return root


# =====================================
# 5. PREORDER TRAVERSAL
# =====================================

def preorder(root):

    result = []

    def visit(node):

        if node is None:
            return

        result.append(node.data)

        visit(node.left)
        visit(node.right)

    visit(root)

    return result


# =====================================
# 6. INORDER TRAVERSAL
# =====================================

def inorder(root):

    result = []

    def visit(node):

        if node is None:
            return

        visit(node.left)

        result.append(node.data)

        visit(node.right)

    visit(root)

    return result


# =====================================
# 7. DISPLAY TREE
# =====================================

def display_tree(root, level=0, position="Root"):

    if root is None:
        return

    print("   " * level + position + ": " + root.data)

    display_tree(root.left, level + 1, "Left")
    display_tree(root.right, level + 1, "Right")


# =====================================
# 8. COMPARE TWO TREES
# =====================================

def same_tree(a, b):

    if a is None and b is None:
        return True

    if a is None or b is None:
        return False

    return (
        a.data == b.data
        and same_tree(a.left, b.left)
        and same_tree(a.right, b.right)
    )


# =====================================
# 9. MAIN APPLICATION
# =====================================

def main():

    print("\n===== TREE ARCHIVING SYSTEM =====")

    print("\nEnter tree in level-order format.")
    print("Use # for missing nodes.")
    print("Example: A B C # D")

    user_input = input("\nEnter nodes: ").strip()

    try:

        values = user_input.split()

        # Create original tree
        original = create_tree(values)

        print("\n--- ORIGINAL TREE ---")
        display_tree(original)

        # Export
        saved_text = serialize(original)

        print("\n--- EXPORTED TEXT ---")
        print(saved_text)

        # Restore
        restored = deserialize(saved_text)

        print("\n--- RESTORED TREE ---")
        display_tree(restored)

        # Traversals
        print("\n--- TRAVERSAL COMPARISON ---")

        print("Original Preorder:", preorder(original))
        print("Restored Preorder:", preorder(restored))

        print("Original Inorder:", inorder(original))
        print("Restored Inorder:", inorder(restored))

        # Structural verification
        print("\n--- VERIFICATION ---")

        if same_tree(original, restored):
            print("SUCCESS: Original and restored trees are identical!")
        else:
            print("ERROR: Trees are different!")

        # Damaged data test
        print("\n--- DAMAGED INPUT TEST ---")

        damaged = ",".join(saved_text.split(",")[:-1])

        print("Damaged text:", damaged)

        try:
            deserialize(damaged)
            print("Unexpectedly accepted damaged data!")

        except ValueError as error:
            print("Damaged data rejected:", error)

    except ValueError as error:
        print("\nERROR:", error)


if __name__ == "__main__":
    main()
