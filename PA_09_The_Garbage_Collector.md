# PA 9: The Garbage Collector
## CS 379: Programming Languages (Fall 2026)

### 🔧 Pipeline Context
This is the **memory-management stage** of the USILang pipeline. It consumes the object/dispatch model from PA 8 — every `USIObject` and AST node your interpreter allocates is now something that can be referenced from multiple places (variables, closures' captured environments, other objects' fields) — and adds a **reference-counting heap** underneath it, so objects are freed automatically the instant they become unreachable. The memory-safe runtime you build here is what PA 10's channel buffer must safely hand objects between threads through next week.

---

### Part A: The Specification (50 Points)
**Instructions:** Answer the following in a separate document (PDF or Markdown). Use the requested traces and brief, focused explanations; no essay is required.

1. **Refcount Trace:**
   Trace the reference count of each object created by the following USILang sequence, showing a table with one row per statement and one column per live object:
   ```
   let a = Dog();      // object D1
   let b = a;          // alias
   let c = Dog();      // object D2
   b = c;              // b now points at D2
   a = null;            // D1 loses its last reference
   ```
   At which exact line does D1's refcount hit zero, and what must your `GCHeap` do at that moment?

2. **The Cycle That Won't Die:**
   Consider a USILang doubly-linked structure:
   ```
   let n1 = Node();
   let n2 = Node();
   n1.next = n2;
   n2.prev = n1;
   n1 = null;
   n2 = null;
   ```
   Trace the refcount of both `Node` objects **before and after** the two `null` assignments. Prove, using your trace, that neither object's refcount ever reaches zero even though nothing in the program can reach either one anymore. This is the precise, mechanical reason reference counting alone cannot reclaim cycles — write the explanation in terms of the counts, not just "cycles are bad."

3. **Refcounting vs. Mark-and-Sweep:**
   Reference counting reclaims memory the instant the last reference disappears, with no world-stopping pause; mark-and-sweep requires a full traversal but correctly reclaims cycles. Give one realistic USILang program where refcounting's immediacy matters (e.g., a resource-like object that must be freed promptly), and one where its cycle-blindness would leak memory over a long-running program (e.g., a REPL session building linked structures repeatedly).

---

### Part B: The Implementation (50 Points)
**Instructions:** Implement a reference-counting heap in `gc_heap.py` and hook it into the interpreter so that every `USIObject` and AST/environment node allocated through PA 6–PA 8's machinery is tracked.

**Requirements:**
1. Implement `GCHeap`:
   ```python
   class GCHeap:
       def allocate(self, obj) -> int:
           ...  # stores obj, returns a handle; initial refcount is 1 (the creating reference)
       def incref(self, handle: int) -> None:
           ...
       def decref(self, handle: int) -> None:
           ...  # when count hits 0: free the object AND cascade-decref any handles it holds
       def is_alive(self, handle: int) -> bool:
           ...
       def live_count(self) -> int:
           ...
   ```
2. Every variable assignment, parameter binding (reuse PA 7's `bind_parameters`), and object field write that stores a handle must call `incref` on the new value's handle and `decref` on whatever handle it overwrote (if any).
3. Every activation record popped off the `CallStack` (PA 6) must `decref` every handle held in its locals before it is discarded — going out of scope is a real dereference event, not a no-op.
4. `decref` must **cascade**: freeing a `USIObject` whose fields hold other handles must decref those handles too, recursively, so a chain of objects with refcount 1 all the way down is fully reclaimed in one top-level `decref` call.
5. **Cycle Acknowledgment Required:** your test harness must include the cyclic-structure case from Part A, Question 2, and your submitted code must **not** silently "fix" it with an undocumented workaround (e.g., quietly running a mark-and-sweep pass). The point of this PA is to observe and document the failure, not paper over it.

**Verification:** Run `python test_gc.py`. The harness runs the alias/reassignment sequence from Part A Question 1 and asserts `live_count()` drops at the correct line, runs a chained-object teardown to confirm cascading `decref`, and runs the cyclic-structure case to confirm (and report) that refcounting alone leaves the cycle's `live_count` non-zero after both variables go out of scope — this last assertion is expected to demonstrate the failure, not silently pass. If all checks match expected behavior, the script prints:
```
GC_HEAP_VERIFIED
```

---

### 🚀 Submission
1. `PA9_Theory.pdf` (or `.md`) — Part A answers, including the written cycle-failure explanation.
2. Put your completed `gc_heap.py` and required prior-stage work in a repository under your own GitHub account. Submit that repository's URL and full commit SHA in Blackboard Ultra; do not upload separate code files.
3. Submit terminal output/screenshot showing the **`GC_HEAP_VERIFIED`** Success Token from `python test_gc.py` in Blackboard Ultra.

The instructor starter is the public template at `https://github.com/cwillpinto/cs379-pa09-garbage-collector`. It is an upstream source. Do not push student work to the instructor repository. See `README.md` for the template and safe direct-clone workflows. The due date is October 26, 2026; use the Blackboard assignment for the verified deadline time.
