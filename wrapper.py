import sys
from importlib import reload
import main
import syntacticAnalysis
import wikidataQuery
import spacy

nlp = None

if __name__ == "__main__":
    # Run repetitively until the user quits.
    while True:
        # Load nlp if not yet done so (so only at the start).
        if not nlp:
            nlp = spacy.load('en')
        # Run main.py as if it is called normally (but with the wrapper parameter).
        main.main(['main.py', '--wrapper'], nlp)
        print("Press enter to re-run the script, CTRL-C to exit")
        sys.stdin.readline()

        # Reload all the files.
        # Important: if any files are added to the program, they must be added
        # in imports above and here.
        reload(main)
        reload(syntacticAnalysis)
        reload(wikidataQuery)
