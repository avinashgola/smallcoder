# Attribution — QuixBugs

The fixtures and task specs under `evals/quixbugs/` are **derived works**. The
buggy programs, their reference fixes and their test data all come from
QuixBugs:

- **Upstream:** https://github.com/jkoppel/QuixBugs
- **Paper:** Derrick Lin, James Koppel, Angela Chen, Armando Solar-Lezama,
  *QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the
  Quixey Challenge* (SPLASH Companion 2017)
- **Licence:** MIT — full text below, as required.

## What this repository changed

`evals/import_quixbugs.py` performs the conversion and is the reproducible
record of it. Nothing was hand-edited. Per program it:

1. keeps the buggy source verbatim, including its docstring;
2. extracts the reference fix as a single anchored replacement, ignoring the
   docstring deletion, comment tidying and whitespace changes that upstream's
   "correct" versions also carry;
3. replaces the upstream test harness (which routes through a
   `pytest.use_correct` switch and a loader outside the program directory)
   with a standalone pytest file that inlines the same JSON test data;
4. generates the issue text by *running* the buggy program and recording what
   it actually does.

Programs are **excluded** when they have no JSON test data, when the fix is not
a single anchorable replacement, or when the buggy version never terminates —
the last because such a task would exhaust the agent's command timeout on every
test run. 24 of 50 programs survive all three filters.

## QuixBugs licence

```
Copyright 2017-2019 James Koppel

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
