"""
PA 9: The Garbage Collector -- starter.

Complete GCHeap below. See the assignment, Part B,
for the full requirements.

Use gc_heap.py as specified in the assignment and imported by the harness.

Design note: GCHeap.allocate(obj) takes exactly one argument per the
spec, so an allocated object that references OTHER heap handles must
expose them itself for decref's cascade to find -- via a
get_child_handles() -> list[int] method. HeapNode below is a given
example object shaped this way, used by the cyclic-structure test.
"""

from typing import Any, Dict, List


class HeapNode:
    """
    Given: a minimal heap object whose fields may hold OTHER handles
    (ints). get_child_handles() is what GCHeap.decref's cascade calls
    to find them -- it must reflect the CURRENT field values, not a
    snapshot taken at creation time.
    """

    def __init__(self, **fields: Any) -> None:
        self.fields = fields

    def get_child_handles(self) -> List[int]:
        return [v for v in self.fields.values() if isinstance(v, int)]


class GCHeap:
    """
    A reference-counting heap. Each live handle maps to [obj, refcount].
    Freed handles are removed and never reused, so a stale handle can't
    accidentally point at a newer object.

    Known limitation (on purpose, see Part A Q2): pure reference counting
    cannot reclaim cycles. This class does NOT run any mark-and-sweep or
    cycle-detection pass, so an unreachable cycle stays alive.
    """

    def __init__(self) -> None:
        self._objects: Dict[int, List[Any]] = {}  # handle -> [obj, refcount]
        self._next_handle = 1

    def allocate(self, obj: Any) -> int:
        """Store obj, return a new handle. Initial refcount is 1 (the creating reference)."""
        handle = self._next_handle
        self._next_handle += 1
        self._objects[handle] = [obj, 1]
        return handle

    def _entry(self, handle: int) -> List[Any]:
        try:
            return self._objects[handle]
        except KeyError:
            raise ValueError(f"handle {handle} is not alive (never allocated or already freed)") from None

    def get(self, handle: int) -> Any:
        """Return the object stored at a live handle."""
        return self._entry(handle)[0]

    def refcount(self, handle: int) -> int:
        """Current refcount of a live handle (0 if freed)."""
        entry = self._objects.get(handle)
        return entry[1] if entry else 0

    def incref(self, handle: int) -> None:
        self._entry(handle)[1] += 1

    def decref(self, handle: int) -> None:
        """
        Decrement the refcount. When it hits 0: free the object, AND
        cascade-decref every handle returned by the freed object's
        get_child_handles() (if it has that method), recursively.
        """
        # A worklist instead of real recursion, so a very long chain
        # can't hit Python's recursion limit. Same result as recursion.
        pending = [handle]
        while pending:
            h = pending.pop()
            entry = self._entry(h)
            entry[1] -= 1
            if entry[1] > 0:
                continue
            # Count hit zero: free it, then drop every reference it held.
            obj = entry[0]
            del self._objects[h]
            children = obj.get_child_handles() if hasattr(obj, "get_child_handles") else []
            pending.extend(children)

    def is_alive(self, handle: int) -> bool:
        return handle in self._objects

    def live_count(self) -> int:
        """Number of currently-alive (refcount > 0) handles."""
        return len(self._objects)


# ---------------------------------------------------------------------
# Interpreter hooks (Part B requirements 5 and 6).
# Call these from the earlier stages wherever a handle is stored or a
# frame is popped, so every store/overwrite/scope-exit updates counts.
# ---------------------------------------------------------------------

def store_handle(heap: GCHeap, old_value: Any, new_value: Any) -> None:
    """
    Use for every variable assignment, parameter binding, and field write.
    Incref the new handle FIRST, then decref the overwritten one, so that
    assigning a variable to itself (x = x) can't free the object mid-write.
    """
    if isinstance(new_value, int):
        heap.incref(new_value)
    if isinstance(old_value, int):
        heap.decref(old_value)


def set_field(heap: GCHeap, node: HeapNode, field: str, new_value: Any) -> None:
    """Object field write: obj.field = new_value, with refcounts updated."""
    old_value = node.fields.get(field)
    store_handle(heap, old_value, new_value)
    node.fields[field] = new_value


def release_frame(heap: GCHeap, record: Any) -> None:
    """
    Call right after CallStack.pop(): going out of scope drops every
    handle held in the popped frame's locals (Cells are unwrapped).
    """
    names = getattr(record.locals_env, "_names", {})
    for value in names.values():
        value = getattr(value, "value", value)  # unwrap a PA 7 Cell
        if isinstance(value, int):
            heap.decref(value)