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
    print("-a, --atest		  Evaluates the program based on the adjusted test questions.")
    print("-w, --wrapper    Does not load NLP.")
    print("-v, --verbose    Verbose mode. Prints debugging messages about it's progress.")

def evaluateQuestion(nlp, line):
    # Input here the process for answering the question
    keywords = s.syntacticAnalysis(nlp, line, True)

    # Test keywords
    return q.makeQuery(keywords)

def evaluateTestQuestions(test_choice):
    local_verbose = False
    if settings.verbose:
        print("Loading SpaCy library...")

        # When combining test and verbose, only use verbose locally.
        local_verbose = True
        settings.verbose = False

    nlp = spacy.load('en_core_web_md')
    
    if test_choice == 0:
        file = "all_questions_and_answers.tsv"
    else:
        file = "qa_v2.csv"
    with open(file) as dbfile:
        if test_choice == 0:
            delim = "\t"
        else:
            delim = ";"
        reader = csv.reader(dbfile, delimiter=delim)

        total_correct = 0
        total_incorrect = 0
        total_lines = sum(1 for row in reader if row[0] != "")
        dbfile.seek(0)
        for line in reader:
            # Getting the question
            question = line[0].strip()
            if question != "":
                if local_verbose:
                    print(question)
                
                # Getting the system answers
                systemAnswers = evaluateQuestion(nlp, question)
                for i in range(len(systemAnswers)):
                    systemAnswers[i] = systemAnswers[i].lower().strip()
                systemAnswers.sort()
                
                # Getting the number of system answers
                numberOfSystemAnswers = len(systemAnswers)
                
                # Getting the number of correct answers
                numberOfCorrectAnswers = 0
                if test_choice == 0:
                    numberOfCorrectAnswers = len(line) - 2
                elif test_choice == 1:
                    for i in range(len(line)):
                        if i >= 2 and line[i] != "":
                            numberOfCorrectAnswers += 1
                
                # Getting the correct answers
                correctAnswers = []
                for i in range(numberOfCorrectAnswers):
                    answer = line[2 + i].lower().strip()
                    correctAnswers.append(answer)
                correctAnswers.sort()
                
                # Comparing the system and correct answers
                correct = True
                if numberOfSystemAnswers != numberOfCorrectAnswers:
                    correct = False
                    if local_verbose:
                        if numberOfSystemAnswers == 0:
                            print("No answer could be given by the system.")
                        else:
                            print("The given answer(s) was not expected.")
                elif numberOfSystemAnswers > 0:
                    if local_verbose:
                        print("Given answers vs correct answers:")
                    for i in range(numberOfSystemAnswers):
                        if local_verbose:
                            print(systemAnswers[i] + " vs " + correctAnswers[i])
                        if systemAnswers[i] != correctAnswers[i]:
                            correct = False
                elif numberOfSystemAnswers == 0 and local_verbose:
                     print("There is no correct answer.")

                # Adding the result to the totals
                if correct:
                    if local_verbose:
                        print("Correct")
                    total_correct += 1
                else:
                    if local_verbose:
                        print("Incorrect")
                    total_incorrect += 1
                
                # Printing the current results 
                print("\rCorrect answers: " + str(total_correct) + "/" + str(total_lines) + 
                      ", Wrong answers: " + str(total_incorrect) + "/" + str(total_lines), end="")
                if local_verbose:
                    print("")
        
        # Printing the total results
        print("\nPercentage of correct answers: " + "{0:.2f}".format((total_correct/total_lines) * 100) + "%")  

def testQuestions():
    with open("qa_v2.csv") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter=";")
        for line in tsvreader:
            for x in line:
                if x == line[0] and x != "":
                    print(x)
                if x != line[0] and x != line[1] and x != "":
                    print(" - " + x)

def main(argv, nlp):
    # Do some necessary initialisation
    load_nlp = True
    test_questions = False
    test_choice = -1
    settings.init()

    # Check commandline arguments
    full_cmd_arguments = argv
    argument_list = full_cmd_arguments[1:]
    
    # Argument options: help, test
    unix_options = "htawv"
    gnu_options = ["help", "test", "atest", "wrapper", "verbose"]

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
            test_choice = 0
        elif current_argument in ("-a", "--atest"):
            test_questions = True
            test_choice = 1
        elif current_argument in ("-w", "--wrapper"):
            load_nlp = False        
        elif current_argument in ("-v", "--verbose"):
            settings.verbose = True 

    if test_questions:
        evaluateTestQuestions(test_choice)
        exit()

    if load_nlp:
        if settings.verbose:
            print("Loading SpaCy library...")
        nlp = spacy.load('en')

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
