"""Index generation: Trie, BST and dictionary versions in one file.

Usage:
  python index_generation.py                                         (menus ask for file and method)
  python index_generation.py input.txt output.txt [trie|bst|dict]   (default: trie)
  python index_generation.py generate     create the six large input files in data/
  python index_generation.py benchmark    time all three methods, save results/
  python index_generation.py test         run the test cases
"""
import os
import re
import sys
import random
from time import perf_counter

# ---------------------------------------------------------------- linked-list queue
class LineNode:
    def __init__(self, number):
        self.number = number
        self.next = None


class LineQueue:
    """Queue of line numbers. The tail pointer makes append O(1)."""
    def __init__(self):
        self.head = None
        self.tail = None

    def append(self, number):
        node = LineNode(number)
        if self.head is None:
            self.head = node
        else:
            self.tail.next = node
        self.tail = node

    def numbers(self):
        node = self.head
        while node is not None:
            yield node.number
            node = node.next


# ---------------------------------------------------------------- 1. Trie
class TrieNode:
    def __init__(self):
        self.children = {}      # character -> TrieNode
        self.lines = None       # queue exists only if a complete word ends here


class TrieIndex:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, line):
        node = self.root
        for ch in word:                       # follow / create one node per character
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        if node.lines is None:                # first time this word is seen
            node.lines = LineQueue()
        node.lines.append(line)               # repeated word: just add the line

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node.lines                     # None if only a prefix

    def items(self):
        # Depth-first with a stack. Children are pushed largest first so the
        # smallest comes out first; a word is yielded before its extensions.
        stack = [(self.root, "")]
        while stack:
            node, word = stack.pop()
            if node.lines is not None:
                yield word, node.lines
            for ch in sorted(node.children, reverse=True):
                stack.append((node.children[ch], word + ch))


# ---------------------------------------------------------------- 2. BST
class BSTNode:
    def __init__(self, word):
        self.word = word
        self.lines = LineQueue()
        self.left = None
        self.right = None


class BSTIndex:
    """Ordinary (unbalanced) BST. Loops are used instead of recursion."""
    def __init__(self):
        self.root = None

    def insert(self, word, line):
        if self.root is None:
            self.root = BSTNode(word)
        node = self.root
        while node.word != word:
            if word < node.word:
                if node.left is None:
                    node.left = BSTNode(word)
                node = node.left
            else:
                if node.right is None:
                    node.right = BSTNode(word)
                node = node.right
        node.lines.append(line)

    def search(self, word):
        node = self.root
        while node is not None and node.word != word:
            node = node.left if word < node.word else node.right
        return None if node is None else node.lines

    def items(self):
        # Inorder traversal (left, node, right) using an explicit stack.
        stack = []
        node = self.root
        while node is not None or stack:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.word, node.lines
            node = node.right


# ---------------------------------------------------------------- 3. Dictionary
class DictionaryIndex:
    def __init__(self):
        self.words = {}

    def insert(self, word, line):
        if word not in self.words:
            self.words[word] = LineQueue()
        self.words[word].append(line)

    def search(self, word):
        return self.words.get(word)

    def items(self):
        for word in sorted(self.words):       # sorted() = ASCII order
            yield word, self.words[word]


METHODS = {"trie": TrieIndex, "bst": BSTIndex, "dict": DictionaryIndex}


# ---------------------------------------------------------------- read / write
def build_index(index, input_file):
    """Read line by line (lines numbered from 1) and insert every word."""
    with open(input_file, encoding="ascii") as file:
        for line_number, line in enumerate(file, 1):
            # Separators: whitespace . , : ;   Case and other characters are kept.
            for word in re.split(r"[\s.,:;]+", line):
                if word:
                    index.insert(word, line_number)
    return index


def write_index(index, output_file):
    with open(output_file, "w", encoding="ascii", newline="\n") as file:
        file.write("Word\tLine numbers\n")
        for word, lines in index.items():
            file.write(word + "\t" + ", ".join(str(n) for n in lines.numbers()) + "\n")


# ---------------------------------------------------------------- inputs + benchmark
COUNTS = [1000, 5000, 10000, 50000, 100000, 500000]
TOTAL = 1_000_001


def make_word(number):
    return "word" + str(number).zfill(6)


def generate():
    for count in COUNTS:
        rnd = random.Random(count)
        numbers = list(range(count))          # every distinct word at least once
        numbers += [rnd.randrange(count) for _ in range(TOTAL - count)]
        rnd.shuffle(numbers)                  # random order -> BST is not degenerate
        with open("data/input_%d.txt" % count, "w", encoding="ascii") as file:
            for i in range(0, TOTAL, 50):     # 50 words per line
                file.write(" ".join(make_word(n) for n in numbers[i:i + 50]) + "\n")
        print("input_%d.txt: %d words, %d distinct" % (count, TOTAL, count))


def benchmark():
    import csv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = []
    for count in COUNTS:
        path = "data/input_%d.txt" % count
        rnd = random.Random(count + 7)
        queries = [make_word(rnd.randrange(count)) for _ in range(100000)]  # same for all
        for name, cls in METHODS.items():
            start = perf_counter()
            index = build_index(cls(), path)
            build = perf_counter() - start
            start = perf_counter()
            for word in queries:
                index.search(word)
            search = perf_counter() - start
            start = perf_counter()
            write_index(index, "results/temp_index.txt")
            printing = perf_counter() - start
            rows.append([count, name, build, search, printing])
            print(count, name, round(build, 3), round(search, 3), round(printing, 3), flush=True)
    with open("results/timings.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["distinct_words", "method", "construction_s", "search_s", "printing_s"])
        writer.writerows(rows)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    titles = ["Construction", "100,000 searches", "Print sorted index"]
    for col, axis in enumerate(axes, start=2):
        for name in METHODS:
            chosen = [r for r in rows if r[1] == name]
            axis.plot([r[0] for r in chosen], [r[col] for r in chosen], marker="o", label=name)
        axis.set_xscale("log")
        axis.set_xlabel("Distinct words (log scale)")
        axis.set_ylabel("Seconds")
        axis.set_title(titles[col - 2])
        axis.legend()
        axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig("results/performance.png", dpi=150)
    print("Saved results/timings.csv and results/performance.png")


# ---------------------------------------------------------------- tests
def run_tests():
    import os
    import tempfile
    cases = [
        ("cat, dog cat.\nCat: car; dog\napple cat! 123 a-b\n",
         {"cat": [1, 1], "dog": [1, 2], "Cat": [2], "car": [2],
          "apple": [3], "cat!": [3], "123": [3], "a-b": [3]}),
        ("", {}),                                              # empty file
        (" ,.:;\n\t\n", {}),                                   # only separators
        ("a ab abc\n\na a\n", {"a": [1, 3, 3], "ab": [1], "abc": [1]}),  # blank line, prefixes
        ("x" * 2000, {"x" * 2000: [1]}),                       # very long word
        (" ".join(chr(c) for c in range(33, 127) if chr(c) not in ".,:;"),
         {chr(c): [1] for c in range(33, 127) if chr(c) not in ".,:;"}),  # all printable ASCII
    ]
    folder = tempfile.mkdtemp()
    for number, (text, expected) in enumerate(cases, 1):
        path = os.path.join(folder, "in.txt")
        with open(path, "w", encoding="ascii") as file:
            file.write(text)
        outputs = []
        for name, cls in METHODS.items():
            index = build_index(cls(), path)
            actual = {w: list(q.numbers()) for w, q in index.items()}
            assert actual == expected, (number, name)
            assert list(actual) == sorted(expected), (number, name, "order")
            assert index.search("missing_word") is None
            for word, nums in expected.items():
                assert list(index.search(word).numbers()) == nums
            out = os.path.join(folder, name + ".txt")
            write_index(index, out)
            with open(out, "rb") as file:
                outputs.append(file.read())
        assert outputs[0] == outputs[1] == outputs[2], number
        print("test", number, "passed")
    trie = TrieIndex()
    trie.insert("apple", 1)
    assert trie.search("app") is None                          # prefix is not a word
    bst = BSTIndex()                                           # sorted input -> tall tree
    for n in range(1500):
        bst.insert(str(n).zfill(4), n + 1)
    assert [w for w, q in bst.items()] == [str(n).zfill(4) for n in range(1500)]
    print("All tests passed")


# ---------------------------------------------------------------- main
def choose(title, options):
    """Show a numbered menu and return the chosen option (asks until valid)."""
    print(title)
    for number, option in enumerate(options, 1):
        print(" ", number, ".", option)
    while True:
        answer = input("Enter number: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print("Please enter a number from 1 to", len(options))


def interactive():
    files = ["data/sample.txt"] + ["data/input_%d.txt" % c for c in COUNTS]
    files.append("Other file (type the path)")
    input_file = choose("Choose the input file:", files)
    if input_file.startswith("Other"):
        input_file = input("Input file path: ").strip().strip('"')
    method = choose("Choose the method:", ["trie", "bst", "dict"])
    name = os.path.splitext(os.path.basename(input_file))[0]
    default = "results/index_%s_%s.txt" % (method, name)
    output_file = input("Output file name [%s]: " % default).strip().strip('"') or default
    return input_file, output_file, method


def main():
    args = sys.argv[1:]
    if len(args) == 1 and args[0] in ("generate", "benchmark", "test"):
        {"generate": generate, "benchmark": benchmark, "test": run_tests}[args[0]]()
        return
    if not args:                               # no arguments: ask with menus
        input_file, output_file, method = interactive()
    elif len(args) in (2, 3) and (len(args) == 2 or args[2] in METHODS):
        input_file, output_file = args[0], args[1]
        method = args[2] if len(args) == 3 else "trie"
    else:
        sys.exit(__doc__)
    if os.path.abspath(input_file) == os.path.abspath(output_file):
        sys.exit("Error: output file must differ from input file")
    try:
        folder = os.path.dirname(output_file)
        if folder:
            os.makedirs(folder, exist_ok=True)
        start = perf_counter()
        index = build_index(METHODS[method](), input_file)
        write_index(index, output_file)
        print("Index saved to", output_file, "using", method,
              "(%.2f seconds)" % (perf_counter() - start))
    except (OSError, UnicodeError) as error:
        sys.exit("Error: " + str(error))


if __name__ == "__main__":
    main()
