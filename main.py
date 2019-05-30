# Main program

import getopt, sys, spacy
import syntacticAnalysis as s
import wikidataQuery as q
import csv

def printHelp():
    print("Available arguments:")
    print("-h, --help       Prints this list.")
    print("-t, --test       Evaluates the program based on the test questions.")

def evaluateTestQuestions():
    with open("all_questions_and_answers.tsv") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")

        total_correct = 0
        total_lines = sum(1 for row in tsvreader)
        tsvfile.seek(0)
        for line in tsvreader:
            # Get the answer
            #answer = evaluateQuestion() 
            answer = line[2:] # These lines should be commented when
            if len(answer) == 1: # we get an output from evaluateQueston()
                answer = answer[0] # and we want to test the program.

            if isinstance(answer, list):
                correct = True
                for i in range(len(answer)):
                    if answer[i] != line[i + 2]:
                        correct = False
                if correct:
                    total_correct += 1
            else:
                if answer == line[2]:
                    total_correct += 1

        print("Percentage of correct answers: " 
              + "{0:.2f}".format((total_correct/total_lines) * 100) + "%")

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
    # Check commandline arguments
    full_cmd_arguments = argv
    argument_list = full_cmd_arguments[1:]
    
    # Argument options: help, test
    unix_options = "ht"
    gnu_options = ["help", "test"]

    try:
        arguments, values = getopt.getopt(argument_list, unix_options, gnu_options)
    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))
        sys.exit(2)

    # Evaluate given options
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--help"):
            printHelp()
            exit()
        elif current_argument in ("-t", "--test"):
            evaluateTestQuestions()
            exit()

    print("Loading SpaCy library...")
    # nlp = spacy.load('en')
    # testQuestions()
    print("State a question:")
    for line in sys.stdin:
        line = line.rstrip()
        # Input here the process for answering the question
        s.syntacticAnalysis(nlp, line)
        q.makeQuery()
        print("State a question:")

if __name__ == "__main__":
    main(sys.argv)
    
