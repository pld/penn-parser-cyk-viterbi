from collections import defaultdict
from operator import itemgetter
import util
import math

class Grammar:
	"""Extract Penn Tree Bank style grammar from open file."""

	cfg_l2r = defaultdict(set)
	cfg_r2l = defaultdict(set)
	pcfg = defaultdict(float)
	print_on = 1000
	min_freq = 5
	gt_conf_factor = 1.96

	def __init__(self, f, limit = False, verbose = False, lower = False, numerate = False):
		self.numerate = numerate
		self.lower = lower
		self.verbose = verbose
		self.limit = limit
		self.__extract_cfg(f)
		
	def __extract_cfg(self, f):
		"""For each line in file f extract context free productions"""
		i = 0
		for line in f:
			if self.limit and i >= self.limit:
				break
			i += 1
			if self.verbose and i % self.print_on == 0:
				print "[Grammar] %d lines parsed." % i
			self.__extract_cfg_line(line, self.lower, self.numerate)
		if self.verbose: util.log_g("Computing normalized frequency counts.")
		self.__good_turing_weights()
		if self.verbose: util.log_g("Normalizing PCFG.")
		self.__normalize_pcfg()

	def __extract_cfg_line(self, s, lower, numerate):
		"""Extract productions by counting parentheses"""
		open_p = []
		last_lhs = False
		rhs_list = defaultdict(list)
		for i in range(len(s)):
			if s[i] == '(':
				open_p.append(i)
			elif s[i] == ')':
				start = open_p.pop() + 1
				end = s.find(' ',start)
				lhs = s[start:end]
				# handle case of improper format with space before paren
				if s[i-1] == ' ':
					ch = i-2
				else:
					ch = i-1
				if len(open_p):
					lhs = "%s^%s" % (lhs, s[open_p[-1]+1:s.find(' ',open_p[-1])])
					rhs_list[open_p[-1]].append(lhs)
				if s[ch] != ')':
					rhs = s[end+1:i]
					if lower:
						# make terminals lowercase
						rhs = rhs.lower()
					# tag numerals as all the same
					if numerate and util.is_numeral(rhs):
						# digits can have . and ,
						rhs = util.NUMERAL
					self.__add_production(lhs, rhs)
				else:
					self.__add_production(lhs, rhs_list[start-1])

	def __add_production(self, lhs, rhs):
		if rhs.__class__ == list:
			rhs = tuple(rhs)
		self.cfg_l2r[lhs].add(rhs)
		self.cfg_r2l[rhs].add(lhs)
		# stores frequency of lhs -> rhs
		self.pcfg[lhs, rhs] += 1

	def __good_turing_weights(self):
		"""Frequency weights for Good Turing"""
		n_dict = defaultdict(int)
		r = list(set(self.pcfg.values()))
		r.sort()
		count = len(r)
		rStar, n, Z, log_r, log_Z = [0] * count, [0] * count, [0] * count, [0] * count, [0] * count
		for v in self.pcfg.values():
			n_dict[int(v)] += 1
		for key, value in n_dict.items():
			n[r.index(key)] = value
		bigN = sum([n[i] * r[i] for i in range(count)])
		next_n = self.__row(count, r, 1)
		pZero = 0 if next_n < 0 else n[next_n] / bigN
		for j in range(count):
			i = 0 if j == 0 else r[j - 1]
			k = 2 * r[j] - i if j == count - 1 else r[j + 1]
			Z[j] = 2 * n[j] / (k - i)
			log_r[j] = math.log(r[j])
			log_Z[j] = math.log(Z[j])
		# find best fit
		XYs = Xsquares = 0.0
		meanX = sum(log_r) / count
		meanY = sum(log_Z) / count
		for i in range(count):
			XYs += (log_r[i] - meanX) * (log_Z[i] - meanY)
			Xsquares += (log_r[i] - meanX)**2
		self.slope = XYs / Xsquares
		self.intercept = meanY - self.slope * meanX
		# compute regression
		indiff = False
		for j in range(count):
			y = (r[j] + 1) * (self.__smoothed(r[j] + 1) / self.__smoothed(r[j]))
			if self.__row(count, r, r[j] + 1) < 0:
				indiff = True
			if not indiff:
				next_n = n[self.__row(count, r, r[j] + 1)]
				x = (r[j] + 1) * next_n / n[j]
				if math.fabs(x - y) <= self.gt_conf_factor * math.sqrt((r[j] + 1)**2 * next_n / ((n[j]**2) * (1 + next_n / n[j]))):
					indiff = True
				else:
					rStar[j] = x
			if indiff:
				rStar[j] = y
		bigNprime = sum([n[i] * rStar[i] for i in range(count)])
		self.gt_freq_weights = dict()
		self.gt_freq_weights[0] = pZero
		for i in range(count):
			self.gt_freq_weights[r[i]] = (1 - pZero) * rStar[i] / bigNprime
		
	def __smoothed(self, v):
		return math.exp(self.intercept + self.slope * math.log(v))

	def __row(self, count, r, v):
		i = 0
		while i < count and r[i] < v:
			i += 1
		return i if ((i < count) and r[i] == v) else -1

	def __normalize_pcfg(self):
		"""Normalize the PCFG"""
		unknowns = defaultdict(float)
		norm = defaultdict(float)
		for rhs, lhss in self.cfg_r2l.items():
			# consider only terminals
			if rhs.__class__ == tuple:
				continue
			r2l_rhs = self.cfg_r2l[rhs]
			self.cfg_r2l[util.UNKNOWN] = self.cfg_r2l[util.UNKNOWN].union(r2l_rhs)
			for lhs in lhss:
				self.cfg_l2r[lhs].add(util.UNKNOWN)
				unknowns[lhs, util.UNKNOWN] += 1
		max_unknown_rf = max(unknowns.values())
		for rule in self.pcfg:
			lhs, rhs = rule
			self.pcfg[rule] *= self.gt_freq_weights[int(self.pcfg[rule])]
			norm[lhs] += self.pcfg[rule]
		for rule in unknowns:
			lhs, rhs = rule
			# scale to (0,1] weight by unseen freq
			self.pcfg[rule] = unknowns[rule] * self.gt_freq_weights[0] / max_unknown_rf
			norm[lhs] += self.pcfg[rule]
		for rule in self.pcfg:
			lhs, rhs = rule
			self.pcfg[rule] /= norm[lhs]

	def check_pcfg_sums(self):
		"""Return sum over all righthand sides for all non terminals"""
		probs = defaultdict(int)
		for lhs, rhss in self.cfg_l2r.items():
			for rhs in rhss:
				probs[lhs] += self.pcfg[lhs, rhs]
		return probs.values()

	def ambiguous(self):
		"""Return ambiguous terminals"""
		ambiguous = []
		for key in self.cfg_r2l:
			if key.__class__ == tuple:
				continue
			values = self.cfg_r2l[key]
			if len(values) > 1:
				prob = []
				for v in values:
					prob.append(self.pcfg[v,key])
				ambiguous.append([key, zip(values, prob)])
		return ambiguous
	
	def most_likely_productions(self, lhss):
		"""Return most likely products for given nonterminals"""
		if not lhss.__class__ == list:
			lhss = [lhss]
		ml_productions = []
		for lhs in lhss:
			productions = []
			for rhs in self.cfg_l2r[lhs]:
				productions.append([rhs, self.pcfg[lhs, rhs]])
			if len(productions) > 0:
				productions = sorted(productions, key=itemgetter(1), reverse=True)
				ml_productions.append(productions[0])
		return zip(lhss,ml_productions)

	def __getstate__(self):
		"""For pickle"""
		return [self.cfg_l2r, self.cfg_r2l, self.pcfg]
		
	def __setstate__(self, state):
		"""For pickle"""
		self.cfg_l2r, self.cfg_r2l, self.pcfg = state
