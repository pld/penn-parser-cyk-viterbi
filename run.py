#!/usr/bin/python

import pickle
import argparse
import gc
import pprint
import pickle
import grammar
import cyk
import util

if __name__ == '__main__':
	help = {
		't':	'Generate a grammar from the passed treebank file.',
		'p':	'Load a grammar from the passed Python Pickle file.',
		'gl':	'Limit the grammar to including the passed number of sentences.',
		's':	'Save the generated grammar to the passed file.',
		'c':	'Check for consistency and print 4 syntactically ambiguous terminals.',
		'v':	'Print verbose output.',
		'vv':	'Print very verbose output.',
		'm':	'Print the most likely productions for the passed non-terminals.',
		'cyk':	'Run the CYK parser on given test corpus or from std input.',
		'ps':	'Limit the parsed test sentences to starting at passed line number.',
		'pl':	'Limit the parsed test sentences to including the passed number of sentences.',
		'a':	'Display ambiguous words.',
		'l':	'Lower case words in building grammar and parsing sentences.',
		'test':	'Build output test sentences.  If passed we don\'t build covering.'
	}
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--treebank', help=help['t'])
	parser.add_argument('-p', '--pickle', help=help['p'])
	parser.add_argument('-gl', '--grammar-limit', type=int, help=help['gl'])
	parser.add_argument('-s', '--save', nargs='?', const='grammar', help=help['s'])
	parser.add_argument('-c', '--check',  action='store_true', help=help['c'])
	parser.add_argument('-v', '--verbose',  action='store_const', default=0, const=1, help=help['v'])
	parser.add_argument('-vv', '--very-verbose', action='store_const', default=0, const=2, help=help['vv'])
	parser.add_argument('-m', '--most-likely-productions', nargs='?', const=True, help=help['m'])
	parser.add_argument('-cyk', '--cyk', nargs='?', const=True, help=help['cyk'])
	parser.add_argument('-ps', '--parser-test-start', type=int, help=help['ps'])
	parser.add_argument('-pl', '--parser-test-limit', type=int, help=help['pl'])
	parser.add_argument('-a', '--ambiguous', nargs='?', const=True, help=help['a'])
	parser.add_argument('-l', '--lower-case', action='store_true', help=help['l'])
	parser.add_argument('-test', '--test', action='store_true', help=help['test'])
	args = parser.parse_args()
	
def main():
	# extract args
	p = args.pickle
	verbose = args.very_verbose or args.verbose
	check = args.check
	ambiguous = args.ambiguous
	mlps = args.most_likely_productions
	lower_case = args.lower_case
	test = args.test
	non_terms_for_ml = mlps.split() if mlps and mlps.__class__ != bool else ['VP', 'S', 'NP', 'SBAR', 'PP']
	max_word_length = 15

	# loading grammar
	if p:
		if verbose:
			util.log_g("Loading grammar from pickle file %s" % (p))
		pkl_file = open(p, 'rb')
		G = pickle.load(pkl_file)
		pkl_file.close()
	else:
		if verbose:
			util.log_g("Loading grammar from treebank %s" % (args.treebank))
		f = open(args.treebank, 'r')
		G = grammar.Grammar(f, args.grammar_limit, verbose, lower_case)
		f.close()
		if args.save:
			output = open(args.save + '.pkl', 'wb')
			pickle.dump(G, output)
			output.close()
	if verbose: util.log_g("Grammar loaded.")
		
	# running checks and statistics
	if check:
		util.log_g("Testing probability consistencies.")
		util.log_g("Greatest divergence from unity: %0.20f." % max([abs(1 - i) for i in G.check_pcfg_sums()]))
	if check or ambiguous:
		util.log_g("Ambiguous word tests.")
		ambig = G.ambiguous()
		ambig_words = zip(*ambig)[0] if ambig else []
		if ambiguous and not ambiguous.__class__ == bool:
			for word in ambiguous.split():
				if word in ambig_words:
					util.log_g("'%s' is ambiguous." % (word))
					pprint.pprint(ambig[ambig_words.index(word)])
				else:
					util.log_g("'%s' is not ambiguous." % (word))
		else:
			util.log_g("4 randomly chosen syntactically ambiguous terminals:")
			pprint.pprint(ambig[0:4])
	if check or mlps:
		util.log_g("Most likely production for non-terminals %s:" % non_terms_for_ml)
		mlps = G.most_likely_productions(non_terms_for_ml)
		pprint.pprint(mlps)
		
	# running CYK
	if args.cyk:
		if args.cyk.__class__ == bool:
			util.log_p("Enter new line to exit.")
			while True:
				s = raw_input('Enter a sentence to parse: ')
				if len(s):
					if verbose:
						util.log_p("Start CYK")
					parse = cyk.CYK(G, s, verbose, lower_case)
					if verbose > 1:
						util.log_p("Covering productions:")
						pprint.pprint(parse.covering_productions())
						util.log_p("Covering productions string: %s" % parse.covering_productions_str())
					util.log_p("Viterbi Parse: %s" % parse.viterbi_parse())
				else:
					break
		else:
			f = open(args.cyk)
			limit = args.parser_test_limit
			start = args.parser_test_start
			i = 0
			if test:
				f_vit = open('viterbi_sentences.txt', 'w')
			else:
				f_cov = open('covering_productions.txt', 'w')
			for line in f:
				if limit and i >= limit:
					break
				i += 1
				if start and i < start:
					continue
				if max_word_length and len(line.split()) > max_word_length:
					out = "\n"
					if test:
						f_vit.write(out)
					else:
						f_cov.write(out)
				else:
					util.log_p("Sentence %d, parsing sentence: << %s >>" % (i, line.strip()))
					parse = cyk.CYK(G, line, verbose)
					# write parse results to output file
					if test:
						out = parse.viterbi_parse()
						if out == util.NOT_IN_GRAMMAR_ERROR:
							out = "\n"
						else:
							out += "\n"
						f_vit.write(out)
					else:
						out = parse.covering_productions_str()
						f_cov.write(out + "\n")
					if verbose:
						util.log_p("Wrote line: %s" % out)
					gc.collect() # collect cyk object
			f.close()
			if test:
				f_vit.close()
			else:
				f_cov.close()
main()
