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

def syntacticAnalysis(nlp, line):
    question = nlp(line)

    keywords = []

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
            print(date1)
            date2 = getPhraseUntil(question, cc_pos + 1, 99999)
            print(date2)

            # See if datefinder can exfiltrate them.
            if (len(list(datefinder.find_dates(date1))) == 1
                    and len(list(datefinder.find_dates(date2))) == 1):
                # Dates successfully extracted. Add them to the keywords.
                keywords.append(("date_word", "between"))

                date1_match = list(datefinder.find_dates(date1, index=True))
                date1_match = date1_match[0]
                date2_match = list(datefinder.find_dates(date2, index=True))
                date2_match = date2_match[0]

                keywords.append(("date1", date1_match[0]))
                keywords.append(("date2", date2_match[0]))

                date1_source = date1[date1_match[1][0]:date1_match[1][1]]
                date2_source = date2[date2_match[1][0]:date2_match[1][1]]

                keywords.append(("date1_source", date1_source))
                keywords.append(("date2_source", date2_source))

                if len(list(datefinder.find_dates(date1, strict=True))) == 1:
                    keywords.append(("date1_strict", True))
                else:
                    keywords.append(("date1_strict", False))

                if len(list(datefinder.find_dates(date2, strict=True))) == 1:
                    keywords.append(("date2_strict", True))
                else:
                    keywords.append(("date2_strict", False))

                # Remove phrase from the question.
                # Also remove the space
                new_line = line[:question[latest_prep_pos].idx - 1]
                new_line += "?"
                question = nlp(new_line)

        else:
            date = getPhraseUntil(question, latest_prep_pos + 1, 99999)
            if len(list(datefinder.find_dates(date))) == 1:
                # A date has been found.
                keywords.append(("date_word", question[latest_prep_pos].text))

                date_match = list(datefinder.find_dates(date, index=True))
                date_match = date_match[0]

                keywords.append(("date1", date_match[0]))

                date_source = date[date_match[1][0]:date_match[1][1]]
                keywords.append(("date1_source", date_source))
                
                if len(list(datefinder.find_dates(date, strict=True))) == 1:
                    keywords.append(("date1_strict", True))
                else:
                    keywords.append(("date1_strict", False))

                # Remove phrase from the question.
                # Also remove the space
                new_line = line[:question[latest_prep_pos].idx - 1] 
                new_line += "?"
                question = nlp(new_line)

    if settings.verbose:
        print("Question after date removal:")
        print(question)

    # Check for all syntactic dependencies
    advmod_pos = sentenceContains(question, "advmod", 0)
    auxpass_pos = sentenceContains(question, "auxpass", 0)
    aux_pos = sentenceContains(question, "aux", 0)
    attr_pos = sentenceContains(question, "attr", 0)
    case_pos = sentenceContains(question, "case", 0)
    det_pos = sentenceContains(question, "det", 0)
    dobj_pos = sentenceContains(question, "dobj", 0)
    nsubj_pos = sentenceContains(question, "nsubj", 0)
    pobj_pos = sentenceContains(question, "pobj", 0)
    poss_pos = sentenceContains(question, "poss", 0)
    prep_pos = sentenceContains(question, "prep", 0)
    root_pos = sentenceContains(question, "ROOT", 0)

    # In the past tense nsubjpass is used instead of nsubj.
    if nsubj_pos == -1:
        nsubj_pos = sentenceContains(question, "nsubjpass", 0)

    ## Get the question types based on the syntactic dependencies found.
    # Check if the sentence contains advmod, nsubj, and root.
    # Check if the order of dependencies is correct.
    if advmod_pos == 0 and nsubj_pos > advmod_pos and root_pos > nsubj_pos:
        # Likely a When/what/who is/was/are/did X [verb] question.
        keywords.append((1, "question_id"))
        if settings.verbose:
            print("When/what/who is/are/did X [verb] question.")
        keywords.append((getPhrase(question, advmod_pos), "question_word"))
        keywords.append((getPhrase(question, nsubj_pos), "entity"))
        keywords.append((getPhrase(question, root_pos), "property"))

        # Add further specification if available.
        # TODO: See if this is possible for other questions as well.
        if prep_pos > nsubj_pos and pobj_pos > prep_pos:
            keywords.append((getPhrase(question, pobj_pos), "specification"))
    elif (root_pos > 0
            and (nsubj_pos > root_pos or sentenceContains(question, "attr", root_pos) > root_pos)
            and pobj_pos > root_pos) and not (poss_pos != -1 and case_pos != -1):
        # Likely an X of Y question.
        keywords.append((2, "question_id"))
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
        keywords.append((3, "question_id"))
        if settings.verbose:
            print("What X did Y [verb] question.")
        keywords.append((getPhrase(question, dobj_pos), "property"))
        keywords.append((getPhrase(question, nsubj_pos), "entity"))

        if attr_pos != -1:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
    elif (root_pos != -1 and poss_pos > root_pos
            and case_pos > poss_pos):
        # Likely an X's Y question.
        keywords.append((4, "question_id"))
        if settings.verbose:
            print("X's Y question.")
        keywords.append((getPhrase(question, poss_pos), "entity"))

        if attr_pos == 0:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
            secondAttribute = sentenceContains(question, "attr", case_pos)
            if secondAttribute != -1:
                keywords.append((getPhrase(question, secondAttribute), "property"))
            else:
                # A second attribute could not be found.
                # Likely a construction like 'X of Y' is present.
                # 9999 means to go on until a punctuation is encountered.
                # This should probably be changed once we implement checking for dates
                # and such which are often at the end of a sentence.
                keywords.append((getPhraseUntil(question, prep_pos + 1, 9999), "specification"))

        elif attr_pos > case_pos:
            keywords.append((getPhrase(question, attr_pos), "property"))
    elif nsubj_pos != -1 and root_pos > nsubj_pos and dobj_pos > root_pos:
        # Likely a What X [verb] Y question.
        keywords.append((5, "question_id"))
        if settings.verbose:
            print("What X [verb] Y question.")

        keywords.append((getPhrase(question, nsubj_pos), "property"))
        keywords.append((getPhrase(question, dobj_pos), "entity"))
        keywords.append((getPhrase(question, root_pos), "root"))

        if attr_pos == 0:
            keywords.append((getPhrase(question, attr_pos), "question_word"))
    elif (det_pos != -1 and nsubj_pos > det_pos and root_pos > nsubj_pos 
            and attr_pos > root_pos):
        # Likely a [Det] X is Y question.
        keywords.append((6, "question_id"))
        if settings.verbose:
            print("[Det] X is Y question.")

        keywords.append((getPhrase(question, nsubj_pos), "property"))
        keywords.append((getPhrase(question, attr_pos), "entity"))

        # TODO: Put this tag up for discussion.
        # Back-up property:
        keywords.append(("part of", "property_backup"))
    elif nsubj_pos != -1 and root_pos > nsubj_pos and attr_pos > root_pos:
        # Likely a '(remind me,) X was Y of what again?' question type.
        # TODO: Take into account that is can also likely be a yes/no
        # question. E.g. X was the Y of Z (right?)
        keywords.append((7, "question_id"))

        keywords.append((getPhrase(question, nsubj_pos), "entity"))
        keywords.append((getPhrase(question, attr_pos), "property"))

        # TODO: Change 'which' to question word.
        if question[prep_pos + 1].text == 'which':
            # 9999 means to go on until a punctuation is encountered.
            # This should probably be changed once we implement checking for dates
            # and such which are often at the end of a sentence.
            keywords.append((getPhraseUntil(question, prep_pos + 2, 9999), "specification"))
    elif root_pos == 0 or aux_pos == 0:
        # Likely a yes/no question
        keywords.append((7, "question_id"))

        if aux_pos == 0:
            keywords.append((getPhrase(question, aux_pos), "question_word"))
            keywords.append((getPhrase(question, root_pos), "property"))
            keywords.append((getPhrase(question, pobj_pos), "property_attribute"))
        elif root_pos == 0:
            keywords.append((getPhrase(question, root_pos), "question_word"))
            
        keywords.append((getPhrase(question, nsubj_pos), "entity"))
        
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
