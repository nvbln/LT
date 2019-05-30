# Main program

import getopt, sys, spacy
import syntacticAnalysis as s
import wikidataQuery as q
import csv

def printHelp():
    print("Available arguments:")
    print("-h, --help       Prints this list.")
    print("-t, --test       Evaluates the program based on the test questions.")
    print("-w, --wrapper    Does not load NLP.")

def evaluateQuestion(nlp, line):
    # Input here the process for answering the question
    keywords = s.syntacticAnalysis(nlp, line)

    # Test keywords
    return q.makeQuery(keywords)

def evaluateTestQuestions():
    print("Loading SpaCy library...")
    nlp = spacy.load('en_core_web_md')

    with open("all_questions_and_answers.tsv") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")

        total_correct = 0
        total_lines = sum(1 for row in tsvreader)
        tsvfile.seek(0)
        for line in tsvreader:
            # Get the answer
            answer = evaluateQuestion(nlp, line[0]) 

            if isinstance(answer, list):
                correct = True
                for i in range(len(answer)):
                    if answer[i].lower() != line[i + 2].lower():
                        correct = False
                if correct:
                    total_correct += 1
            else:
                if answer.lower() == line[2].lower():
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

def main(argv, nlp):
    load_nlp = True

    # Check commandline arguments
    full_cmd_arguments = argv
    argument_list = full_cmd_arguments[1:]
    
    # Argument options: help, test
    unix_options = "htw"
    gnu_options = ["help", "test", "wrapper"]

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
        elif current_argument in ("-w", "--wrapper"):
            load_nlp = False        

    if load_nlp:
        print("Loading SpaCy library...")
        nlp = spacy.load('en_core_web_md')

    # testQuestions()
    print("State a question:")
    for line in sys.stdin:
        line = line.rstrip()

        # Finish the program when typing exit.
        if line == "exit":
            break

        # Evaluate the question and get the answer.
        answers = evaluateQuestion(nlp, line)

        for answer in answers:
            print(answer)
        print("State a question:")

if __name__ == "__main__":
    nlp = None
    main(sys.argv, nlp)
