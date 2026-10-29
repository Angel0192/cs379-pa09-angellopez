"""
PA 9: The Garbage Collector -- verification suite.

Run: python test_gc.py
Prints GC_HEAP_VERIFIED only if every check below passes.
"""

import sys

from gc_heap import GCHeap, HeapNode


def check(label: str, condition: bool, failures: list) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


def main() -> int:
    failures: list = []

    print("Replaying the Part A, Question 1 alias/reassignment trace...\n")
    heap = GCHeap()

    # let a = Dog();
    d1 = heap.allocate(HeapNode(kind="Dog"))
    check("after 'let a = Dog();': live_count == 1", heap.live_count() == 1, failures)

    # let b = a;  (alias -- b now also references D1)
    heap.incref(d1)
    check("after 'let b = a;': D1 alive, live_count still 1", heap.is_alive(d1) and heap.live_count() == 1, failures)

    # let c = Dog();
    d2 = heap.allocate(HeapNode(kind="Dog"))
    check("after 'let c = Dog();': live_count == 2", heap.live_count() == 2, failures)

    # b = c;  (b drops its D1 reference, gains a D2 reference)
    heap.decref(d1)
    heap.incref(d2)
    check("after 'b = c;': D1 still alive (a still holds it), live_count == 2", heap.is_alive(d1) and heap.live_count() == 2, failures)

    # a = null;  (a drops its D1 reference -- this is D1's LAST reference)
    heap.decref(d1)
    check("after 'a = null;': D1 is freed", not heap.is_alive(d1), failures)
    check("after 'a = null;': live_count == 1 (only D2 remains)", heap.live_count() == 1, failures)

    if failures:
        print(f"\n{len(failures)} check(s) failed -- fix these before the cascade/cycle tests. No token issued.")
        return 1

    print("\nTesting cascading decref on a chained structure...\n")
    heap2 = GCHeap()
    # Each node's initial refcount of 1, from allocate(), IS the single
    # reference held by its parent's field -- set directly in the
    # constructor, so no extra incref() here (that would double-count
    # the same reference rather than represent a second, independent one).
    tail = heap2.allocate(HeapNode(kind="Leaf"))
    middle = heap2.allocate(HeapNode(kind="Link", next=tail))
    head = heap2.allocate(HeapNode(kind="Link", next=middle))
    check("chain of 3 allocated: live_count == 3", heap2.live_count() == 3, failures)

    # Drop the only EXTERNAL reference to head -- this should cascade-free the whole chain,
    # since middle and tail are only kept alive by the chain itself.
    heap2.decref(head)
    check("dropping the head reference cascades to free the whole chain (live_count == 0)", heap2.live_count() == 0, failures)
    check("tail is no longer alive after the cascade", not heap2.is_alive(tail), failures)

    print("\nReplaying the Part A, Question 2 cyclic-structure case (expected to leak)...\n")
    heap3 = GCHeap()
    n1 = heap3.allocate(HeapNode(kind="Node"))
    n2 = heap3.allocate(HeapNode(kind="Node"))

    # n1.next = n2;
    heap3.incref(n2)
    # n2.prev = n1;
    heap3.incref(n1)

    # n1 = null; n2 = null;  (drop BOTH external variable references)
    heap3.decref(n1)
    heap3.decref(n2)

    check(
        "refcounting ALONE does not collect the cycle -- both nodes remain alive after both variables go out of scope",
        heap3.is_alive(n1) and heap3.is_alive(n2) and heap3.live_count() == 2,
        failures,
    )
    print("  (this is the expected, documented failure of pure reference counting -- not a bug in your GCHeap)")

    print()
    if failures:
        print(f"{len(failures)} check(s) failed. No token issued.")
        return 1

    print("GC_HEAP_VERIFIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
