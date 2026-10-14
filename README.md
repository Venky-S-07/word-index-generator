# Index Generation (Lab Examination 2)

Reads a text file and writes a table of every word in ASCII order with the line
numbers where it occurs. Three versions are in one file, `index_generation.py`:
Trie, BST and Python dictionary.

## Run

Simplest: `python index_generation.py` - it shows numbered menus to pick the input
file (sample or one of the six large files, or your own path) and the method
(1 Trie, 2 BST, 3 dictionary), then asks for the output name (Enter = default in `results/`).

Or give the arguments directly:

```
python index_generation.py input.txt output.txt          # Trie (default)
python index_generation.py input.txt output.txt bst      # BST
python index_generation.py input.txt output.txt dict     # dictionary
python index_generation.py test                          # test cases
python index_generation.py generate                      # rebuild data/input_*.txt
python index_generation.py benchmark                     # needs: pip install matplotlib
```

Try it: `python index_generation.py data/sample.txt out.txt`

## Folder

- `index_generation.py` - all code, comments, tests, input generator, benchmark
- `data/` - `sample.txt` and six inputs (1,000,001 words each; 1000, 5000, 10000, 50000, 100000, 500000 distinct words)
- `results/` - sample outputs of all three methods, `timings.csv`, `performance.png`

## Design

1. **Line queue**: a linked list with head and tail pointers. Each node holds one
   line number, so adding an occurrence is O(1). A repeated word adds a node to its
   existing queue, so `cat` twice on line 1 gives `1, 1`.
2. **Reading**: lines are numbered from 1 (blank lines count). Each line is split at
   blanks/whitespace, `.` `,` `:` `;`. Empty pieces are ignored. Case, digits and all
   other printable ASCII characters stay part of the word, so `Cat` and `cat` differ
   and `cat!` is its own word.
3. **Trie**: one node per character; only the node where a complete word ends holds a
   queue (so the prefix `app` is not a word just because `apple` exists). Output uses a
   stack, visiting children in sorted order and a word before its longer extensions.
4. **BST**: each node holds a word and its queue. Smaller goes left, larger right,
   equal appends a line number. Inorder traversal gives sorted output. Loops and an
   explicit stack are used, so there is no recursion limit. It is not self-balancing,
   so sorted input would make it slow; the generated inputs are shuffled.
5. **Dictionary**: word -> queue. Keys are sorted before writing.
6. **Output**: first line `Word<TAB>Line numbers`, then one tab-separated row per word.
   Input must be ASCII, otherwise a clear error is shown.

## Example

Input:
```
cat, dog cat.
Cat: car; dog
apple cat! 123 a-b
```
Output:
```
Word	Line numbers
123	3
Cat	2
a-b	3
apple	3
car	2
cat	1, 1
cat!	3
dog	1, 2
```

## Test cases (`python index_generation.py test`)

Checked for all three methods, which must also give byte-identical files: repeated
words, case, separators, all printable ASCII characters, empty file, only separators,
blank lines, prefixes, a 2000-character word, missing-word search, and a tall BST.

## Performance (seconds, one run, Python on Linux)

| Distinct | Trie build | BST build | Dict build | Trie search | BST search | Dict search | Trie print | BST print | Dict print |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 1.863 | 2.337 | 1.478 | 0.052 | 0.073 | 0.008 | 0.627 | 0.598 | 0.546 |
| 5000 | 2.506 | 3.062 | 2.006 | 0.056 | 0.159 | 0.011 | 0.711 | 0.629 | 0.647 |
| 10000 | 2.650 | 3.060 | 2.186 | 0.069 | 0.138 | 0.014 | 0.608 | 0.574 | 0.705 |
| 50000 | 3.538 | 4.769 | 3.099 | 0.141 | 0.254 | 0.043 | 0.784 | 0.733 | 0.702 |
| 100000 | 4.548 | 6.520 | 3.099 | 0.160 | 0.413 | 0.062 | 0.914 | 0.976 | 0.785 |
| 500000 | 5.445 | 8.820 | 3.319 | 0.213 | 0.683 | 0.071 | 1.493 | 1.502 | 1.932 |

Search uses the same 100,000 random existing words for every method. Construction
includes reading, splitting, insertion and queue building; printing includes sorted
traversal and writing the file. See `results/performance.png` for the plots.

The dictionary is fastest to build and search; Trie is second; the BST is slowest and
grows with tree height. Printing is similar for all three because every occurrence must
be written. The words are synthetic with a shared prefix, and each time is from a
single run, so treat this as a simple comparison, not a rigorous benchmark.
