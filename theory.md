# PA 9: The Garbage Collector — Part A

**CS 379: Programming Languages, Fall 2026**
**Angel Lopez**

## 1. Refcount Trace

| Statement | D1 | D2 |
|---|---|---|
| `let a = Dog();` | 1 | — |
| `let b = a;` | 2 | — |
| `let c = Dog();` | 2 | 1 |
| `b = c;` | 1 | 2 |
| `a = null;` | **0** | 2 |

D1 hits 0 on `a = null;` since that was its last reference. The heap frees D1 right then and decrefs anything it was holding, which is nothing for a plain Dog.

## 2. The Cycle That Won't Die

| Statement | N1 | N2 |
|---|---|---|
| `let n1 = Node();` | 1 | — |
| `let n2 = Node();` | 1 | 1 |
| `n1.next = n2;` | 1 | 2 |
| `n2.prev = n1;` | 2 | 2 |
| `n1 = null;` | 1 | 2 |
| `n2 = null;` | 1 | 1 |

After both nulls, each node is stuck at 1 because the other node's field still points to it. A node only drops its fields when it gets freed, so N1 waits on N2 and N2 waits on N1, and neither ever hits 0.

Nothing in the program can reach them anymore, but refcounting only counts references and doesn't check if they're reachable.

## 3. Refcounting vs. Mark-and-Sweep

**Where immediacy matters:**

```
func writeLog(msg) {
    let f = FileHandle("log.txt");
    f.write(msg);
}

for (i = 0; i < 1000; i = i + 1) { writeLog("tick"); }
```

Refcounting frees each `FileHandle` as soon as `writeLog` returns, so the file closes right away. With mark-and-sweep, a bunch of files could stay open until the collector runs.

**Where it leaks:**

```
// long-running REPL session
loop {
    let a = Node();
    let b = Node();
    a.next = b;
    b.prev = a;
}
```

Every loop leaves a 2-node cycle stuck at 1, same as Question 2. Over a long session `live_count()` keeps going up, while mark-and-sweep would see they're unreachable and free them.

## Note on the implementation

My `GCHeap` is just refcounting with no hidden cycle cleanup. The cycle test is supposed to end with `live_count() == 2` to show the leak.