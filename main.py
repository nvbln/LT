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
    print("-a, --atest		Evaluates the program based on the adjusted test questions.")
    print("-w, --wrapper    Does not load NLP.")
    print("-v, --verbose    Verbose mode. Prints debugging messages about it's progress.")

def evaluateQuestion(nlp, line):
    # Input here the process for answering the question
    keywords = s.syntacticAnalysis(nlp, line)

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
        total_lines = sum(1 for row in reader)
        dbfile.seek(0)
        for line in reader:
            # Get the answer
            answer = evaluateQuestion(nlp, line[0]) 
            
            current_correct = total_correct

            if local_verbose:
                print("") # Necessary newline due to line 84.
                print("Given answers vs actual answer:")
			
            if test_choice == 0:
                lineLength = len(line)
            else:
                lineLength = 0
                for x in line:
                     if x != "":
                         lineLength += 1
            
            # If the system and the DB both have a different number of answers,
            # they aren't the same answers. Thus, the answer is incorrect.
            if lineLength - 2 != len(answer):
                total_incorrect += 1
                if local_verbose:
                    print("Different number of answers.")
            # There is more than 1 correct answer
            elif len(answer) > 1:
                correct = True
                # Making 2 lists for both system and correct answers
                systemAnswers = []
                correctAnswers = []
                for i in range(len(answer)):
                    systemAnswers.append(answer[i].lower())
                    correctAnswers.append(line[i + 2].lower().strip())
                # Checking whether the lists are equal
                systemAnswers.sort()
                correctAnswers.sort()
                for i in range(len(answer)):
                    if local_verbose:
                        print(systemAnswers[i] + " vs " + correctAnswers[i])
                    if systemAnswers[i] != correctAnswers[i]:
                        correct = False
                # Adding the correctness to the totals
                if correct:
                    total_correct += 1
                else:
                    total_incorrect += 1
            # This is only 1 correct answer
            elif len(answer) == 1:
                systemAnswer = answer[0].lower()
                correctAnswer = line[2].lower().strip()
                if local_verbose:
                    print(systemAnswer +  " vs " + correctAnswer)
                if systemAnswer == correctAnswer:
                    total_correct += 1
                else:
                    total_incorrect += 1
            # There aren't any correct answers
            elif len(answer) == 0:
                if local_verbose:
                    print("No answer was given.")
                if lineLength == 2:
                    total_correct += 1
                else:
                    total_incorrect += 1
            
            if local_verbose:
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
        nlp = spacy.load('en_core_web_md')

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
