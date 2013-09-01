## Treebank Parser, CYK, and Viterbi

Code written to run under Python 2.7 with the `argparse` module.

> The below assumes you have the Penn WSJ Treebank corpus in the folder
> `data`

Quick start to parse and run CYK interactive:

```bash
$ python run.py -t data/wsj.02-21.training -cyk
```

Quick start to parse and run Viterbi on a file of sentences:

```bash
$ python run.py -t data/wsj.02-21.training -cyk data/test.sentence.23 -test
```

### Executable: `run.py`

`run.py` refers to the modules `grammar.py` and `cyk.py`.  All options can be controlled through
passed arguments as detailed in the help.  To print the run $ python run.py --help.

A grammar can be built with the command:

```bash
$ python run.py -t data/wsj.02-21.training -s
```

Then with the generated grammar a set of covering productions can be generated with the command:

```bash
$ python run.py -p grammar.pkl -cyk data/test.sentence.23
```

These covering productions will be ourput to the file `covering_productions.txt` where each line is of the form:

> XP1 YP1#XP2 YP2

where _XPi_ _YPi_ are the left hand sides of the covering productions and _#_ indicate the
start of a new covering produciton.

Or, a grammar can be built and a set of covering productions can be generated with the singe command:

```bash
$ python run.py -t data/wsj.02-21.training -cyk data/test.sentence.23
```

To run the parser on a sentence file given a pickle grammar:

```bash
$ python run.py -p grammar.pkl -cyk data/test.sentence.23 -test
```

By default the covering productions are output to covering_productions.txt, formatted as:

* each line corresponds to a line in the input test file
* each line is an array of arrays where the first member is _A_, the second _B_ and the third _C_ for the rule _A -> BC_

For reference the help output (`$ python run.py -h`) is displayed below:

```
usage: run.py [-h] [-t TREEBANK] [-p PICKLE] [-gl GRAMMAR_LIMIT] [-s [SAVE]]
              [-c] [-v] [-vv] [-m [MOST_LIKELY_PRODUCTIONS]] [-cyk [CYK]]
              [-pl PARSER_TEST_LIMIT] [-a [AMBIGUOUS]] [-l] [-test]

optional arguments:
  -h, --help            show this help message and exit
  -t TREEBANK, --treebank TREEBANK
                        Generate a grammar from the passed treebank file.
  -p PICKLE, --pickle PICKLE
                        Load a grammar from the passed Python Pickle file.
  -gl GRAMMAR_LIMIT, --grammar-limit GRAMMAR_LIMIT
                        Limit the grammar to including the passed number of
                        sentences.
  -s [SAVE], --save [SAVE]
                        Save the generated grammar to the passed file.
  -c, --check           Check for consistency and print 4 syntactically
                        ambiguous terminals.
  -v, --verbose         Print verbose output.
  -vv, --very-verbose   Print very verbose output.
  -m [MOST_LIKELY_PRODUCTIONS], --most-likely-productions [MOST_LIKELY_PRODUCTIONS]
                        Print the most likely productions for the passed non-
                        terminals.
  -cyk [CYK], --cyk [CYK]
                        Run the CYK parser on given test corpus or from std
                        input.
  -pl PARSER_TEST_LIMIT, --parser-test-limit PARSER_TEST_LIMIT
                        Limit the parsed test sentences to including the
                        passed number of sentences.
  -a [AMBIGUOUS], --ambiguous [AMBIGUOUS]
                        Display ambiguous words.
  -l, --lower-case      Lower case words in building grammar and parsing
                        sentences.
  -test, --test         Build output test sentences. If passed we don't build
                        covering.
```


### Class: `grammar.py`

Extracts a Penn Tree Bank style grammar from a passed open file.

Constructor takes an open file handle, an optional boolean limit of the number of lines to read
(default no limit), and an optional boolean of whether to print verbose output or not (default False).

Public variables:

* `cfg_l2r`, dictionary of sets which maps nonterminals to terminals and nonterminals
* `cfg_r2l`, dictionary of sets which maps terminals and nonterminals to nonterminals
* `pcfg`, dictionary of floats which maps tuples nonterminals, terminals and nonterminals to (0,1]

Public functions:

* `check_pcfg_sums`, no arguments, return the sum of the probablities of all productions for each nonterminal
* `ambiguous`, no arguments, return the set of syntactically ambiuous terminals
* `most_likely_productions`, nonterminal or array of nonterminals, return the most likely productions for nonterminals


### Class: `cyk.py`
Generate parse forests given a sentence and a grammar.

Constructor takes a grammar of type grammar, a sentence of type string, and an optional boolean
vervose indicating whether to print verbose output or not (default False).

Public variables:
* `chart`, the created chart parse

Public functions:
* `covering_productions`, return the set of productions _TOP => XP_ and _TOP => XP YP_ that cover the sentence
* `covering_productions_str`, return the set of covering production formatted as a string
* `viterbi_parse`, return the parse generated by Viterbi probabilities

Written for Elements of Language Processing and Learning 2010, University of Amsterdam.
Peter Lubell-Doughtie, Davide Modolo.

Copyright (c) 2010 Peter Lubell-Doughtie.  All rights reserved.  Licensed under the BSD license.

