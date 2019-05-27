# Main program

import sys, spacy
import syntacticAnalysis as s
import wikidataQuery as q

def main(argv):
	print("Loading SpaCy library...")
	# nlp = spacy.load('en')
	print("State a question:")
	for line in sys.stdin:
		line = line.rstrip()
		# Input here the process for answering the question
		s.syntacticAnalysis(nlp, line)
		q.makeQuery()
		print("State a question:")

if __name__ == "__main__":
	main(sys.argv)
