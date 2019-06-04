# Main program

import getopt, sys, spacy
import syntacticAnalysis as s
import wikidataQuery as q
import settings
import csv

def printHelp():
    print("Available arguments:")
    print("-h, --help       Prints this list.")
    print("-t, --test       Evaluates the program based on the test questions.")
    print("-w, --wrapper    Does not load NLP.")
    print("-v, --verbose    Verbose mode. Prints debugging messages about it's progress.")

def evaluateQuestion(nlp, line):
    # Input here the process for answering the question
    keywords = s.syntacticAnalysis(nlp, line)

    # Test keywords
    return q.makeQuery(keywords)

def evaluateTestQuestions():
    local_verbose = False
    if settings.verbose:
        print("Loading SpaCy library...")

        # When combining test and verbose, only use verbose locally.
        local_verbose = True
        settings.verbose = False
    nlp = spacy.load('en_core_web_md')

    with open("all_questions_and_answers.tsv") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")

        total_correct = 0
        total_incorrect = 0
        total_lines = sum(1 for row in tsvreader)
        tsvfile.seek(0)
        for line in tsvreader:
            # Get the answer
            answer = evaluateQuestion(nlp, line[0]) 
            
            current_correct = total_correct

            if len(answer) > 1:
                correct = True
                for i in range(len(answer)):
                    if len(line) > i + 2 and answer[i].lower() != line[i + 2].lower():
                        correct = False
                if correct:
                    total_correct += 1
                else:
                    total_incorrect += 1
            elif len(answer) > 0:
                answer = answer[0]
                if answer.lower() == line[2].lower():
                    total_correct += 1
                else:
                    total_incorrect += 1
            else:
                # No answer is available.
                total_incorrect += 1

            if local_verbose:
                print("") # Necessary newline due to line 71.
                if current_correct == total_correct:
                    print("Incorrect: " + line[0])
                else:
                    print("Correct: " + line[0])
            print("\rAnswered correctly: " + str(total_correct) + "/" 
                    + str(total_lines) + ". Answered incorrectly: " 
                    + str(total_incorrect) + "/" + str(total_lines), end="")

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
    # Do some necessary initialisation
    load_nlp = True
    test_questions = False
    settings.init()

    # Check commandline arguments
    full_cmd_arguments = argv
    argument_list = full_cmd_arguments[1:]
    
    # Argument options: help, test
    unix_options = "htwv"
    gnu_options = ["help", "test", "wrapper", "verbose"]

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
            test_questions = True
        elif current_argument in ("-w", "--wrapper"):
            load_nlp = False        
        elif current_argument in ("-v", "--verbose"):
            settings.verbose = True 

    if test_questions:
        evaluateTestQuestions()
        exit()

    if load_nlp:
        if settings.verbose:
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
