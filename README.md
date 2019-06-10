# QA-system for music-related questions
Hi! This system has been developed as a project for the RUG course Language Technology (2019).
The following people have been part of this development:
- Nathan van Beelen (s3392961)
- Kevin Kelly (s...)
- Galina Lesnic (s3367398)
- Tom Veldhuis (s3451771)
## Requirements for running this system:
- Python3 (and pip3)
- SpaCy and its library for English, can be installed through a Linux terminal as follows:
  ```
  pip3 install --user spacy
  pip3 install --user https://github.com/explosion/spacy-models/releases/download/en_core_web_md-2.1.0/en_core_web_md-2.1.0.tar.gz
  python3 -m spacy link en_core_web_md en
  ```
- NLTK for Python3, can be installed through a Linux terminal as follows:
  ```
  sudo apt install python3-nltk
  ```
- WordNet add-on for NLTK, can be installed as follows:
  - Run the commands `import nltk` and `nltk.download()` in a Python3 terminal
  - In the window that appears, make sure that the add-on with the identifier `wordnet` in the `Corpora` list is installed
- Datefinder (can be installed by running `pip3 install datefinder`)
- Textblob (can be installed by running `pip3 install text blob` and then `python3 -m textblob.download_corpora`)
- Simplejson (can be installed by running `pip3 install simplejson`)