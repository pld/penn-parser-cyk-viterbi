import re

NOT_IN_GRAMMAR_ERROR = "ERROR sentence not in the grammar"
UNKNOWN = "%%UNKNOWN%%"
NUMERAL = "%%NUMBER%%"

def is_numeral(n):
	"numerals can have internal '.' or ','"
	def repl(m):
		return m.group(1) + '0' + m.group(3)
	return re.sub('(\w+)(\.|,)(\w+)', repl, n).isdigit()

def ordered_set(alist):
	"""Creates an ordered set from a list of tuples or other hashable items"""
	mmap = {} # implements hashed lookup
	oset = [] # storage for set

	for item in alist:
		#Save unique items in input order
		if item not in mmap:
			mmap[item] = 1
			oset.append(item)
	return oset

def log_g(s): __log("Grammar", s)

def log_p(s): __log("Parser", s)

def __log(pre, s): print "[%s] %s" % (pre, s)
