# Main program

import sys, spacy
import syntacticAnalysis as s
import wikidataQuery as q
import csv

def testQuestions():
	with open("all_questions_and_answers.tsv") as tsvfile:
		tsvreader = csv.reader(tsvfile, delimiter="\t")
		for line in tsvreader:
			for x in line:
				if x == line[0]:
					print(x)
				if x != line[0] and x != line[1]:
					print(" - " + x)

def main(argv):
	print("Loading SpaCy library...")
	# nlp = spacy.load('en')
	testQuestions()
	print("State a question:")
	for line in sys.stdin:
		line = line.rstrip()
		# Input here the process for answering the question
		s.syntacticAnalysis(nlp, line)
		q.makeQuery()
		print("State a question:")

if __name__ == "__main__":
	main(sys.argv)
	
