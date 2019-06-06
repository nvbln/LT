# Functions needed for syntactic analysis
import settings

# A pre-defined dictionary for difficult terms
key_words_dict = {'band members': 'has part', 'members': 'has part',
                  'member': 'has part', 'band member': 'has part',
                  'founding year': 'inception', 'bandmember': 'has part',
                  'bandmembers': 'has part', 'founding': 'inception'}

def syntacticAnalysis(nlp, line):
    question = nlp(line)

    keywords = []

    # Check for all syntactic dependencies
    # Skip the first word as it is likely a question word.
    advmod_pos = sentenceContains(question, "advmod", 0)
    auxpass_pos = sentenceContains(question, "auxpass", 0)
    aux_pos = sentenceContains(question, "aux", 0)
    attr_pos = sentenceContains(question, "attr", 0)
    case_pos = sentenceContains(question, "case", 0)
    dobj_pos = sentenceContains(question, "dobj", 0)
    nsubj_pos = sentenceContains(question, "nsubj", 0)
    pobj_pos = sentenceContains(question, "pobj", 0)
    poss_pos = sentenceContains(question, "poss", 0)
    prep_pos = sentenceContains(question, "prep", 0)
    root_pos = sentenceContains(question, "ROOT", 0)

    ## Get the question types based on the syntactic dependencies found.
    # Check if the sentence contains advmod, nsubj, and root.
    # Check if the order of dependencies is correct.
    if advmod_pos == 0 and nsubj_pos > advmod_pos and root_pos > nsubj_pos:
        # Likely a When/what/who is/are/did X [verb] question.
        if settings.verbose:
            print("When/what/who is/are/did X [verb] question.")
        keywords.append((getPhrase(question, advmod_pos), "question_word"))
        keywords.append((getPhrase(question, nsubj_pos), "entity"))
        keywords.append((getPhrase(question, root_pos), "property"))
    elif (root_pos > 0
            and (nsubj_pos > root_pos or sentenceContains(question, "attr", root_pos) > root_pos)
            and pobj_pos > root_pos):
        # Likely an X of Y question.
        if settings.verbose:
            print("X of Y question.")
        keywords.append((getPhrase(question, pobj_pos), "entity"))

        secondAttribute = sentenceContains(question, "attr", root_pos)
        if nsubj_pos != -1:
            keywords.append((getPhrase(question, nsubj_pos), "property"))
        elif secondAttribute != -1:
            keywords.append((getPhrase(question, secondAttribute), "property"))

        if advmod_pos != -1:
            keywords.append((getPhrase(question, advmod_pos), "question_word"))
        elif attr_pos != -1:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
    elif (dobj_pos != -1 and aux_pos > dobj_pos and nsubj_pos > aux_pos 
            and root_pos > nsubj_pos):
        # Likely a What X did Y [verb] question.
        if settings.verbose:
            print("What did Y [verb] question.")
        keywords.append((getPhrase(question, dobj_pos), "property"))
        keywords.append((getPhrase(question, nsubj_pos), "entity"))

        if attr_pos != -1:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
    elif (root_pos != -1 and poss_pos > root_pos
            and case_pos > poss_pos 
            and sentenceContains(question, "attr", case_pos) > case_pos):
        # Likely an X's Y question.
        if settings.verbose:
            print("X's Y question.")
        keywords.append((getPhrase(question, poss_pos), "entity"))

        if attr_pos == 0:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
            secondAttribute = sentenceContains(question, "attr", case_pos)
            if secondAttribute != -1:
                keywords.append((getPhrase(question, secondAttribute), "property"))

        elif attr_pos > case_pos:
            keywords.append((getPhrase(question, attr_pos), "property"))
    elif nsubj_pos != -1 and root_pos > nsubj_pos and dobj_pos > root_pos:
        # Likely a What X [verb] Y question.
        if settings.verbose:
            print("What X [verb] Y question.")
        # TODO: Discuss whether we should also append the verb.

        keywords.append((getPhrase(question, nsubj_pos), "property"))
        keywords.append((getPhrase(question, dobj_pos), "entity"))

        if attr_pos == 0:
            keywords.append((getPhrase(question, attr_pos), "question_word"))

    if settings.verbose:
        print(keywords)

    return keywords

# Gets the syntactic dependency on the given position
# and all the compounds in front of it.
def getPhrase(sentence, position):
    # TODO: Make effective use of the 'prep' dependency.
    # For example: "United States of America" is one phrase,
    # but it will not be seen as such unless using this dependency.

    word = sentence[position]
    phrase = ""
    position -= 1
    while (position >= 0 and (sentence[position].dep_ == "compound"
            or sentence[position].dep_ == "amod")):
        phrase += sentence[position].text + " "
        position -= 1

    return phrase + word.text

def sentenceContains(sentence, keyword, start_position):
    # Return the position of the first encounter
    # with the requested keyword from the start_position.
    for i in range(len(sentence)):
        if (i >= start_position):
            word = sentence[i]
            if (word.dep_ == keyword):
                return i

    # The keyword could not be found.
    return -1
