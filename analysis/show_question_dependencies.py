import spacy
import sys

nlp = spacy.load('en_core_web_md')

for line in sys.stdin:
    line = line.rstrip()
    
    question = nlp(line)
    dependencies = []
    for word in question:
        dependencies.append(word.dep_)
    print(dependencies)
