# Functions needed for syntactic analysis
import settings
import datefinder
from nltk.corpus import wordnet as wn
 
# Static variables for the convertPOS-function
WN_NOUN = 'n'
WN_VERB = 'v'
WN_ADJECTIVE = 'a'
WN_ADJECTIVE_SATELLITE = 's'
WN_ADVERB = 'r'

w_words_list = {'What', 'Who', 'When', 'Where', 'Why', 'How', 'Which', 'How many'}

def syntacticAnalysis(nlp, line, with_names):
    line = line.strip()
    if line[-1] != "?":
        line += "?"
    question = nlp(line)

    keywords = {}

    names = []

    # Check if the sentence contains a date (and remove it).
    # TODO: Clean up code.
    # TODO: Check if the date is not between puncts. This likely means that
    # we are dealing with names.
    # TODO: The datefinder tries to fill in the gaps by itself.
    # I.e. for '1999' it will return '1999-06-08' (which is today 20 years ago).
    # There is the strict option. So we should exploit that and report whether
    # the datefinder filled in gaps. Then we can ignore everything that is
    # the same date/time as at the moment of the extraction.
    prep_pos = sentenceContains(question, "prep", 0)
    if prep_pos != -1:
        # Get the latest prep.
        latest_prep_pos = prep_pos
        current_prep_pos = sentenceContains(question, "prep", latest_prep_pos + 1)
        while (current_prep_pos != -1):
           latest_prep_pos = current_prep_pos 
           current_prep_pos = sentenceContains(question, "prep", latest_prep_pos + 1)

        if question[latest_prep_pos].text == "between":
            # There should be two dates.
            cc_pos = sentenceContains(question, "cc", latest_prep_pos)
            date1 = getPhraseUntil(question, latest_prep_pos + 1, cc_pos)
            date2 = getPhraseUntil(question, cc_pos + 1, 99999)

            # See if datefinder can exfiltrate them.
            if (len(list(datefinder.find_dates(date1))) == 1
                    and len(list(datefinder.find_dates(date2))) == 1):
                # Dates successfully extracted. Add them to the keywords.
                addToDict(keywords, "date_word", "between")

                date1_match = list(datefinder.find_dates(date1, index=True))
                date1_match = date1_match[0]
                date2_match = list(datefinder.find_dates(date2, index=True))
                date2_match = date2_match[0]
                
                addToDict(keywords, "date1", date1_match[0])
                addToDict(keywords, "date2", date2_match[0])

                date1_source = date1[date1_match[1][0]:date1_match[1][1]]
                date2_source = date2[date2_match[1][0]:date2_match[1][1]]
                
                addToDict(keywords, "date1_source", date1_source)
                addToDict(keywords, "date2_source", date2_source)

                if len(list(datefinder.find_dates(date1, strict=True))) == 1:
                    addToDict(keywords,"date1_strict", True)
                else:
                    addToDict(keywords,"date1_strict", False)

                if len(list(datefinder.find_dates(date2, strict=True))) == 1:
                    addToDict(keywords,"date2_strict", True)
                else:
                    addToDict(keywords,"date2_strict", False)

                # Remove phrase from the question.
                # Also remove the space
                new_line = line[:question[latest_prep_pos].idx - 1]
                new_line += "?"
                question = nlp(new_line)

        else:
            date = getPhraseUntil(question, latest_prep_pos + 1, 99999)
            if len(list(datefinder.find_dates(date))) == 1:
                # A date has been found.
                addToDict(keywords,"date_word", question[latest_prep_pos].text)

                date_match = list(datefinder.find_dates(date, index=True))
                date_match = date_match[0]

                addToDict(keywords,"date1", date_match[0])

                date_source = date[date_match[1][0]:date_match[1][1]]
                addToDict(keywords,"date1_source", date_source)
                
                if len(list(datefinder.find_dates(date, strict=True))) == 1:
                    addToDict(keywords,"date1_strict", True)
                else:
                    addToDict(keywords,"date1_strict", False)

                # Remove phrase from the question.
                # Also remove the space
                new_line = line[:question[latest_prep_pos].idx - 1] 
                new_line += "?"
                question = nlp(new_line)

    if settings.verbose:
        print("Question after date removal:")
        print(question)
    
    # Retrieve the names from the question.
    if with_names:
        new_line = line
        for word in question:
            # It's the start of a new name.
            if word.ent_iob_ == "B":
                names.append(word.text)
            # It's the continuation of a name.
            elif word.ent_iob_ == "I" and word.text != "'s":
                names[-1] += " " + word.text
                new_line = new_line.replace(" " + word.text, word.text, 1)
        question = nlp(new_line)

        if settings.verbose:
            print("Question after name replacement:")
            print(question)
    
    # Probably a misidentification of spacy
    for word in question:
        if word.dep_ == "npadvmod":
            word.dep_ = "nsubj"

    # Check for all syntactic dependencies
    advmod_pos = sentenceContains(question, "advmod", 0)
    auxpass_pos = sentenceContains(question, "auxpass", 0)
    aux_pos = sentenceContains(question, "aux", 0)
    attr_pos = sentenceContains(question, "attr", 0)
    case_pos = sentenceContains(question, "case", 0)
    det_pos = sentenceContains(question, "det", 0)
    dobj_pos = sentenceContains(question, "dobj", 0)
    nsubj_pos = sentenceContains(question, "nsubj", 0)
    pcomp_pos = sentenceContains(question, "pcomp", 0)
    pobj_pos = sentenceContains(question, "pobj", 0)
    poss_pos = sentenceContains(question, "poss", 0)
    prep_pos = sentenceContains(question, "prep", 0)
    root_pos = sentenceContains(question, "ROOT", 0)

    # In the past tense nsubjpass is used instead of nsubj.
    if nsubj_pos == -1:
        nsubj_pos = sentenceContains(question, "nsubjpass", 0)

    # If no aux has been found, try the passive aux.
    if aux_pos == -1:
        aux_pos = auxpass_pos

    ## Get the question types based on the syntactic dependencies found.
    # Check if the sentence contains advmod, nsubj, and root.
    # Check if the order of dependencies is correct.
    if aux_pos != 0 and ((advmod_pos == 0 and nsubj_pos > advmod_pos)
            or (pobj_pos == 0 and nsubj_pos > pobj_pos)) and root_pos > nsubj_pos:
        # Likely a When/what/who is/was/are/did X [verb] question.
        addToDict(keywords,"question_id",1)

        if settings.verbose:
            print("When/what/who is/are/did X [verb] question.")
        if advmod_pos == 0:
            addToDict(keywords, "question_word", getPhrase(question, advmod_pos, names))
        else: 
            addToDict(keywords, "question_word", getPhrase(question, pobj_pos, names))
        addToDict(keywords, "entity", getPhrase(question, nsubj_pos, names))
        addToDict(keywords, "property", getPhrase(question, root_pos, names))

        # Add further specification if available.
        # TODO: See if this is possible for other questions as well.
        if prep_pos > nsubj_pos and pobj_pos > prep_pos:
            addToDict(keywords, "specification", getPhrase(question, pobj_pos, names))
    elif (root_pos > 0 and aux_pos != 0
            and (nsubj_pos > root_pos or sentenceContains(question, "attr", root_pos) > root_pos)
            and pobj_pos > root_pos) and not (poss_pos != -1 and case_pos != -1):
        # Likely an X of Y question.
        addToDict(keywords, "question_id", 2)
        if settings.verbose:
            print("X of Y question.")
        addToDict(keywords, "entity", getPhrase(question, pobj_pos, names))

        secondAttribute = sentenceContains(question, "attr", root_pos)
        if nsubj_pos != -1:
            addToDict(keywords, "property", getPhrase(question, nsubj_pos, names))
        elif secondAttribute != -1:
            addToDict(keywords, "property", getPhrase(question, secondAttribute, names))

        if advmod_pos != -1:
            addToDict(keywords,"question_word", getPhrase(question, advmod_pos, names))
        elif attr_pos != -1:
            addToDict(keywords, "question_word", getPhrase(question, attr_pos, names))
    elif (((dobj_pos != -1 and aux_pos > dobj_pos) 
            or (pcomp_pos != -1 and aux_pos > pcomp_pos)) and nsubj_pos > aux_pos 
            and root_pos > nsubj_pos):
        # Likely a What X did Y [verb] question.
        addToDict(keywords, "question_id", 3)
        if settings.verbose:
            print("What X did Y [verb] question.")
        
        addToDict(keywords, "question_word", "What")
        if dobj_pos != -1:
            addToDict(keywords,"property", getPhrase(question, dobj_pos, names))
        else:
            addToDict(keywords, "property", getPhrase(question, pcomp_pos, names))
        addToDict(keywords,"property", getPhrase(question, root_pos, names))
        addToDict(keywords,"entity", getPhrase(question, nsubj_pos, names))

        if attr_pos != -1:
            addToDict(keywords, "question_word", getPhrase(question, attr_pos, names))
    elif (aux_pos != 0 and root_pos != -1 and poss_pos > root_pos
            and case_pos > poss_pos):
        # Likely an X's Y question.
        addToDict(keywords,"question_id", 4)
        if settings.verbose:
            print("X's Y question.")
        addToDict(keywords,"entity", getPhrase(question, poss_pos, names))

        if attr_pos == 0:
            addToDict(keywords, "question_word", getPhrase(question, attr_pos, names))
            secondAttribute = sentenceContains(question, "attr", case_pos)
            if secondAttribute != -1:
                addToDict(keywords, "property", getPhrase(question, secondAttribute, names))
            else:
                # A second attribute could not be found.
                # Likely a construction like 'X of Y' is present.
                # 9999 means to go on until a punctuation is encountered.
                # This should probably be changed once we implement checking for dates
                # and such which are often at the end of a sentence.
                addToDict(keywords, "property", getPhraseUntil(question, case_pos + 1, 9999))

        elif attr_pos > case_pos:
            addToDict(keywords, "property", getPhrase(question, attr_pos, names))
    elif aux_pos != 0 and nsubj_pos != -1 and root_pos > nsubj_pos and dobj_pos > root_pos:
        # Likely a What X [verb] Y question.
        addToDict(keywords,"question_id",5)
        if settings.verbose:
            print("What X [verb] Y question.")

        addToDict(keywords, "property", getPhrase(question, nsubj_pos, names))
        addToDict(keywords, "entity", getPhrase(question, dobj_pos, names))
        addToDict(keywords, "root", getPhrase(question, root_pos, names))

        if attr_pos == 0:
            addToDict(keywords,"question_word", getPhrase(question, attr_pos, names))
    elif (det_pos != -1 and nsubj_pos > det_pos and root_pos > nsubj_pos 
            and attr_pos > root_pos):
        # Likely a [Det] X is Y question.
        addToDict(keywords, "question_id", 6)
        if settings.verbose:
            print("[Det] X is Y question.")
        
        addToDict(keywords, "question_word", "What")
        addToDict(keywords, "property", getPhrase(question, nsubj_pos, names))
        addToDict(keywords, "entity", getPhrase(question, attr_pos, names))

        # TODO: Put this tag up for discussion.
        # Back-up property:
        addToDict(keywords, "property_backup", "part of")
    elif aux_pos != 0 and nsubj_pos != -1 and root_pos > nsubj_pos and attr_pos > root_pos:
        # Likely a '(remind me,) X was Y of what again?' question type.
        # TODO: Take into account that is can also likely be a yes/no
        # question. E.g. X was the Y of Z (right?)
        addToDict(keywords, "question_id", 7)
        if settings.verbose:
            print("(remind me,) X was Y of what again? question.")

        addToDict(keywords, "entity", getPhrase(question, nsubj_pos, names))
        addToDict(keywords,  "property", getPhrase(question, attr_pos, names))

        if question[prep_pos + 1].text.lower() in [x.lower() for x in w_words_list]:
            # 9999 means to go on until a punctuation is encountered.
            # This should probably be changed once we implement checking for dates
            # and such which are often at the end of a sentence.
            addToDict(keywords, "specification", getPhraseUntil(question, prep_pos + 2, 9999))
    elif (aux_pos != 0 and nsubj_pos != -1 and aux_pos != 0 
            and root_pos > nsubj_pos and prep_pos > root_pos
            and pobj_pos > prep_pos):
            # Likely a Who/What is/are [prep] X question.
            addToDict(keywords, "question_id", 8)
            if settings.verbose:
                print("Who/What is/are [prep] X question.")

            addToDict(keywords, "entity", getPhrase(question, pobj_pos, names))
            # Prep won't be a phrase anyway, so better to do it like this.
            addToDict(keywords, "property", question[prep_pos].text)
            # These kind of questions are very likely 'part of' questions.
            addToDict(keywords, "property_backup", "part of")

            if question[0].dep_ == "det" or question[0].dep_ == "nsubj":
                addToDict(keywords, "question_word", question[0].text)
    # Try to pick up some leftover questions
    elif (aux_pos != 0 and dobj_pos != -1 and (nsubj_pos != -1 or pobj_pos != -1)):
        addToDict(keywords, "question_word", "What")
        if nsubj_pos != -1:
            addToDict(keywords, "entity", getPhrase(question, nsubj_pos, names))
        else:
            addToDict(keywords, "entity", getPhrase(question, pobj_pos, names))
        addToDict(keywords, "property", getPhrase(question, dobj_pos, names))
    elif root_pos == 0 or aux_pos == 0:
        # Likely a yes/no question
        addToDict(keywords, "question_id", 9)
        if settings.verbose:
            print("Yes/no question")

        if aux_pos == 0:
            addToDict(keywords, "question_word", getPhrase(question, aux_pos, names))
            addToDict(keywords,  "property", getPhrase(question, root_pos, names))
            addToDict(keywords, "property_attribute", getPhrase(question, pobj_pos, names))
        elif root_pos == 0:
            addToDict(keywords,"question_word", getPhrase(question, root_pos, names))
            
        addToDict(keywords, "entity", getPhrase(question, nsubj_pos, names))

    if (aux_pos != 0 and advmod_pos == 0 and question[0].text.lower() == "how"
        and question[1].text.lower() == "many"):
        # Likely a how many question.
        if settings.verbose:
            print("How many question.")

        nsubj2_pos = sentenceContains(question, "nsubj", nsubj_pos + 1)

        if dobj_pos != -1:
            # Do not use getPhrase in this case
            # because it will also include 'many'.
            addToDict(keywords, "property", question[dobj_pos].text)
        elif nsubj_pos != -1 and nsubj2_pos != -1:
            addToDict(keywords, "property", question[nsubj_pos].text)

            # First reset the dictionary for the entity keyword.
            keywords["entity"] = []
            addToDict(keywords, "entity", getPhrase(question, nsubj2_pos, names))
        elif pobj_pos != -1:
            # First reset the dictionary for the property keyword.
            keywords["property"] = []
            addToDict(keywords, "property", question[nsubj_pos].text)
            
            # First reset the dictionary for the entity keyword.
            keywords["entity"] = []
            addToDict(keywords, "entity", getPhrase(question, pobj_pos, names))
        addToDict(keywords, "question_word", "many")
        
    if settings.verbose:
        print("Keywords:")
        print(keywords)

    if ((len(keywords) == 0 or (len(keywords) < 2 and "question_word" in keywords))
            and with_names):
        # It did not fit any categories, try again without names.
        keywords = syntacticAnalysis(nlp, line, False)

    return keywords

# Gets the syntactic dependency on the given position
# and all the compounds in front of it.
def getPhrase(sentence, position, names):
    # TODO: Make effective use of the 'prep' dependency.
    # For example: "United States of America" is one phrase,
    # but it will not be seen as such unless using this dependency.

    word = sentence[position]

    # If word is a name, get it from names.
    name = compareNames(word, names)
    if name != -1:
        return name

    phrase = ""
    position -= 1
    while (position >= 0 and (sentence[position].dep_ == "compound"
            or sentence[position].dep_ == "amod")):
        phrase += sentence[position].text + " "
        position -= 1

    return phrase + word.text

def compareNames(word, names):
    for name in names:
        spaceless_name = name.replace(" ", "")
        if word.text == spaceless_name:
            return name
    return -1

def getPhraseUntil(sentence, start_position, end_position):
    phrase = ""
    position = start_position
    while (position < end_position and position < len(sentence) 
            and sentence[position].dep_ != "punct"):
        phrase += sentence[position].text + " "
        position += 1
    return phrase.strip()

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

# Converts a word string from POS to another POS, using WordNet
# WN_NOUN: noun
# WN_VERB: verb
# WN_ADJECTIVE: adjective
# WN_ADJECTIVE_SATELLITE: ?
# WN_ADVERB: adverb
def convertPOS(word, from_pos, to_pos):
    synsets = wn.synsets(word, pos=from_pos)
 
    # Word not found
    if not synsets:
        return []
 
    # Get all lemmas of the word (consider 'a'and 's' equivalent)
    lemmas = [l for s in synsets
                for l in s.lemmas() 
                if s.name().split('.')[1] == from_pos
                    or from_pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE)
                        and s.name().split('.')[1] in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE)]
 
    # Get related forms
    derivationally_related_forms = [(l, l.derivationally_related_forms()) for l in lemmas]
 
    # filter only the desired pos (consider 'a' and 's' equivalent)
    related_noun_lemmas = [l for drf in derivationally_related_forms
                             for l in drf[1] 
                             if l.synset().name().split('.')[1] == to_pos
                                or to_pos in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE)
                                    and l.synset().name().split('.')[1] in (WN_ADJECTIVE, WN_ADJECTIVE_SATELLITE)]
 
    # Extract the words from the lemmas
    words = [l.name() for l in related_noun_lemmas]
    len_words = len(words)
 
    # Build the result in the form of a list containing tuples (word, probability)
    result = [(w, float(words.count(w))/len_words) for w in set(words)]
    result.sort(key=lambda w: -w[1])
 
    # return all the possibilities sorted by probability
    # for each element e in result, e[0] gives the name and e[1] gives the probability
    return result

def addToDict(dictionary, item, value):
    dictionary[item] = dictionary.get(item, []) + [value]
    
    
