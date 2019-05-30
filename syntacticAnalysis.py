# Functions needed for syntactic analysis

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
    attr_pos = sentenceContains(question, "attr", 0)
    case_pos = sentenceContains(question, "case", 0)
    dobj_pos = sentenceContains(question, "dobj", 0)
    nsubj_pos = sentenceContains(question, "nsubj", 0)
    pobj_pos = sentenceContains(question, "pobj", 0)
    poss_pos = sentenceContains(question, "poss", 0)
    prep_pos = sentenceContains(questioin, "prep", 0)
    root_pos = sentenceContains(question, "ROOT", 0)

    ## Get the question types based on the syntactic dependencies found.

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
