"""TreeVault Flask API. The server keeps no tree between requests; archive text is the source of truth."""
import json

from flask import Flask, jsonify, render_template, request

from serializer import LABEL_RE, ArchiveError, check, restore, same_structure, serialize
from tree import MAX_NODES, build_level_order, inorder, layout, postorder, preorder

app = Flask(__name__)


def fail(err):
    return jsonify(error=err.message, position=err.position, suggestion=err.suggestion), 400


def parse_level_order(text):
    """Accept a JSON array like ["A", null, "B"] or plain text like: A B null C."""
    text = (text or "").strip()
    if text.startswith("["):
        try:
            items = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ArchiveError(f"The array is not valid JSON ({exc.msg}).",
                               suggestion='Use double quotes and commas, e.g. ["A", "B", null].')
        if not isinstance(items, list):
            raise ArchiveError("Expected a list of labels.")
    else:
        items = text.replace(",", " ").split()
    if not items:
        raise ArchiveError("Enter at least one label. Use null for a missing child.")
    items = [None if x is None or (isinstance(x, str) and x.lower() == "null") else x for x in items]
    if items[0] is None:
        raise ArchiveError("The root cannot be null.", 1, "Put the root label first.")
    for pos, item in enumerate(items, start=1):
        if item is not None and (not isinstance(item, str) or not LABEL_RE.fullmatch(item)):
            raise ArchiveError(f"Invalid label {item!r} at position {pos}.", pos,
                               "Labels are text using letters, digits, _ . - (max 16 characters).")
    if sum(x is not None for x in items) > MAX_NODES:
        raise ArchiveError(f"The tree has more than {MAX_NODES} nodes.", suggestion="Reduce the tree size.")
    root, used = build_level_order(items)
    if used < len(items):
        raise ArchiveError(f"Extra entries after the tree is complete, starting at position {used + 1}.",
                           used + 1, f"Delete entries from position {used + 1} onward.")
    return root


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/tree/create")
def create():
    body = request.get_json(silent=True) or {}
    try:
        root = parse_level_order(body.get("text", ""))
    except ArchiveError as err:
        return fail(err)
    return jsonify(serialized=serialize(root), view=layout(root))


@app.post("/api/tree/serialize")
def serialize_route():
    # Trees travel as archive text, so serialize is a pass-through check.
    body = request.get_json(silent=True) or {}
    try:
        root = restore(body.get("serialized"))
    except ArchiveError as err:
        return fail(err)
    return jsonify(serialized=serialize(root))


@app.post("/api/tree/deserialize")
def deserialize():
    body = request.get_json(silent=True) or {}
    try:
        root = restore(body.get("serialized"))
    except ArchiveError as err:
        return fail(err)
    return jsonify(view=layout(root))


@app.post("/api/tree/validate")
def validate():
    body = request.get_json(silent=True) or {}
    try:
        tokens = check(body.get("serialized"))
    except ArchiveError as err:
        return jsonify(valid=False, error=err.message, position=err.position, suggestion=err.suggestion)
    return jsonify(valid=True, nodes=sum(t != "#" for t in tokens))


@app.post("/api/tree/verify")
def verify():
    body = request.get_json(silent=True) or {}
    try:
        original = restore(body.get("original"))
        restored = restore(body.get("restored"))
    except ArchiveError as err:
        return fail(err)
    identical, message = same_structure(original, restored)
    return jsonify(identical=identical, message=message)


@app.post("/api/tree/traversals")
def traversals():
    body = request.get_json(silent=True) or {}
    try:
        root = restore(body.get("serialized"))
    except ArchiveError as err:
        return fail(err)
    return jsonify(preorder=preorder(root), inorder=inorder(root), postorder=postorder(root))


if __name__ == "__main__":
    app.run(debug=True)
