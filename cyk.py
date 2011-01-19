import copy
import util
from collections import defaultdict
import sys

class CYK:
	"""Generate parse forests and parses given a sentence and a grammar."""

	start_symbol = "TOP"
	duplicate_code = "@"
	unary_code = "%%%%%"
	not_in_grammar_error = util.NOT_IN_GRAMMAR_ERROR

	def __init__(self, G, s, verbose = False, lower = False, start_symbol = False, numerate = False):
		self.G = G
		self.sentence = (s.lower() if lower else s).split()
		self.numerate = numerate
		self.sentence_len = len(self.sentence)
		self.verbose = verbose
		if start_symbol:
			self.start_symbol = start_symbol
		self.__create_chart()

	def covering_productions(self):
		"""Return the covering productions for the passed sentence"""
		covering = zip(*zip(*self.covering[0, self.sentence_len, self.start_symbol])[0:2])
		return [rhs[0:1] if rhs[1] == 0 else rhs for rhs in covering]
		
	def covering_productions_str(self):
		"""Return covering productions formatted as a string"""
		return "#".join([" ".join(rhs) for rhs in self.covering_productions()])

	def viterbi_parse(self):
		"""Return Viterbi parse"""
		try:
			return self.__rec_viterbi_parse(self.start_symbol, 0, self.sentence_len)
		except KeyError:
			return self.not_in_grammar_error

	def __rec_viterbi_parse(self, head, begin, end):
		"""Recursively build parse from LHS and RHS"""
		b, c, split = self.viterbi_back[begin, end, head]
		# remove parent annotation
		annot_start = head.find("^")
		if annot_start > 0: head = head[0:head.find("^")]
		if c == 0:
			# unary rule, check for terminal
			lhs = b if split == -1 else self.__rec_viterbi_parse(b, begin, end)
			return "(%s %s)" % (head, lhs)
		else:
			lhs = self.__rec_viterbi_parse(b, begin, split)
			rhs = self.__rec_viterbi_parse(c, split, end)
			if head[-1] == self.duplicate_code:
				# flatten @ suffixed productions XP@
				return "%s %s" % (lhs, rhs)
			else:
				start = head.find(self.unary_code)
				if start > 0:
					# decode unary rule
					return "(%s (%s %s %s))" % (head[0:start], head[start + len(self.unary_code):len(head)], lhs, rhs)
				else:
					return "(%s %s %s)" % (head, lhs, rhs)

	def __create_chart(self):
		"""Build chart using CYK algorithm"""
		# create local vars for memory efficiency
		cfg_r2l = self.G.cfg_r2l
		pcfg = self.G.pcfg
		n = self.sentence_len
		s = self.sentence
		verbose = self.verbose
		start_symbol = self.start_symbol
		unknown = util.UNKNOWN

		chart = defaultdict(set)
		covering = defaultdict(set)
		viterbi_back = dict()
		pi = defaultdict(float)

		# local function for efficiency
		def check_add_prob(prob, a, b, c, begin, end, split):
			# add production to this chart location
			if prob > 0:
				if verbose > 1:
					util.log_p("add C %s => (%s %s) to [%d, %d] split: %d." % (a, b, c, begin, end, split))
				chart[begin, end].add(a)
				# store our covering productions
				if a == start_symbol:
					covering[begin, end, a].add((b, c))
			# if max, break ties by not changing
			if prob > pi[begin, end, a]:
				if verbose > 1:
					util.log_p("add pi %s => (%s %s) to [%d, %d] split: %d." % (a, b, c, begin, end, split))
				pi[begin, end, a] = prob
				viterbi_back[begin, end, a] = [b, c, split]
				return True
			return False

		for i in range(n):
			# replace numerals with code
			if self.numerate and util.is_numeral(s[i]): word = util.NUMERAL
			# replace never seen words with code
			elif len(cfg_r2l[s[i]]) == 0: word = unknown
			else: word = s[i]
			for a in cfg_r2l[word]:
				prob = pcfg[a, word]
				# split as -1 codes a terminal
				check_add_prob(prob, a, s[i], 0, i, i+1, -1)
		for span in range(2, n + 1):
			for begin in range(n + 1 - span):
				end = begin + span
				for split in range(begin + 1, end):
					for b in chart[begin, split]:
						for c in chart[split, end]:
							for a in cfg_r2l[b, c]:
								# prob for all productions A -> B C
								prob = pcfg[a, (b, c)]
								prob = pi[begin, split, b] * pi[split, end, c] * prob
								check_add_prob(prob, a, b, c, begin, end, split)
					# for unary productions TOP -> B
					added = True
					while end == n and added:
						added = False
						nts = copy.copy(chart[begin, end])
						for b in nts:
							a = start_symbol
							prob = pcfg.get((a, (b,)))
							if prob:
								prob = pi[begin, end, b] * prob
								# c as 0, split as 0 codes a unary rule
								added = check_add_prob(prob, a, b, 0, begin, end, 0)
		self.chart = chart
		self.covering = covering
		self.viterbi_back = viterbi_back
		self.pi = pi
