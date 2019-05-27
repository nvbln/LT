import spacy

def getKey(item):
    return item[0]

nlp = spacy.load('en')

try:
    # Retrieve questions from file, remove student number and put them
    # in a new array without duplicates.
    file = open("questions")
    questions = file.read()
    questions = questions.split("\n")
    del questions[-1]
    non_dup_questions = []
    for question in questions:
        question = question.split("\t")
        if (len(question) == 1):
            question = question[0]
        else:
            question = question[1]

        if question not in non_dup_questions:
            non_dup_questions.append(question)

    questions = non_dup_questions

    # Get sentence word dependencies. Put unique "sentences" in a list.
    # Also keep track of the number of occurrences of such a sentence.
    structures = []
    structures_count = []
    total = len(questions)
    for question in questions:
        question = nlp(question)
        non_compound_question = []
        for word in question:
            if (word.dep_ != "compound" and word.dep_ != "punct"):
                non_compound_question.append(word.dep_)

        if non_compound_question not in structures:
            structures.append(non_compound_question)
            structures_count.append(1)
        else:
            index = structures.index(non_compound_question)
            structures_count[index] += 1

    # Merge the arrays
    merged_structures = []
    for i in range(len(structures)):
        new_structure = (structures_count[i], structures[i])
        merged_structures.append(new_structure)

    merged_structures.sort(key=getKey)

    # Print results.
    for structure in merged_structures:
        print('[%s]' % ', '.join(map(str, structure[1])), end='')
        print(" count: " + str(structure[0]) + " percentage: "
                + "{0:.2f}".format(structure[0]/total))

    total = len(merged_structures)
    print("Total number of unique structures: " + str(total))

finally:
    file.close()

