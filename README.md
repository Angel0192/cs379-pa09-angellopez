# CS379 PA 9: The Garbage Collector

Read `PA_09_The_Garbage_Collector.md` for the 100-point assignment and its October 26, 2026 due date. Check Blackboard Ultra for the exact deadline time.

## Files and prerequisite work

Use Python 3.11 or newer; no third-party packages are required. `gc_heap.py` is the intentionally incomplete `GCHeap` starter. `test_gc.py` is the supplied harness. `lexer.py`, `parser.py`, `symtable.py`, `frames.py`, `parameters.py`, and `dispatcher.py` are prior-stage placeholders: bring your **own verified PA 3–PA 8 work** into your student-owned repository. They are not completed dependencies.

## Local check

From the repository root, run `python test_gc.py`. A completed implementation matching the supplied harness prints `GC_HEAP_VERIFIED`. An incomplete starter is expected to stop at a `NotImplementedError`. The harness checks alias/reassignment lifetime, a three-node cascade, and the known two-node cycle leak. It does not verify all prior-stage integration requirements.

## Work in your own GitHub repository

If the instructor starter is a template, select **Use this template** on GitHub, create a repository under your own account, and clone it locally. For a direct clone, create an empty repository under your account first:

```sh
git clone https://github.com/cwillpinto/cs379-pa09-garbage-collector.git
cd cs379-pa09-garbage-collector
git remote rename origin upstream
git remote add origin <your-repository-url>
git remote -v
git push -u origin <your-branch>
```

Check that `origin` points to your repository before pushing. Do not push to the instructor repository. Commit your code and copy its full SHA with `git rev-parse HEAD`.

## Submit in Blackboard Ultra

Submit your student-owned repository URL and full commit SHA, `PA9_Theory.pdf` or `.md` with the required traces and concise explanations, and terminal output or a screenshot showing `GC_HEAP_VERIFIED`. Your `gc_heap.py` and prior-stage code live in your repository; separate code-file uploads are not required.
