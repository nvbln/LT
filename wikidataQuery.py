# Functions needed for making queries for WikiData
import requests
import settings

# A pre-defined dictionary for difficult terms
property_dict = {'band members': 'has part', 'members': 'has part',
                  'member': 'has part', 'band member': 'has part',
                  'founding year': 'inception', 'bandmember': 'has part',
                  'bandmembers': 'has part', 'founding': 'inception',
                  'play': 'instrument'}

# List of w-words, feel free to add any words I forgot
w_words_list = ['What', 'Who', 'When', 'Where', 'Why', 'How', 'Which']

def makeQuery(keywords):
    property_id = None
    entity_id = None
    prop_attribute_id = None
    
    query_type = None

    for keyword in keywords:
        if keyword[1] == "question_word":
            if keyword[0] in w_words_list:
                #TODO update property & possibly query based on that
                query_type = 'basic'
            else:
                query_type = 'yes/no' 
                
        elif keyword[1] == "property":
            prop = property_dict.get(keyword[0], keyword[0])
            property_id = searchEntity(prop, "property")
            
        elif keyword[1] == "entity":
            entity_id = searchEntity(keyword[0], "entity")
            
        elif keyword[1] == "property_attribute":
            # TODO attribute is not always entity, right? needs to be fixed
            prop_attribute_id = searchEntity(keyword[0], "entity")
            
    answer = None
    
    if query_type == 'basic':
        answer = submitQuery(entity_id, property_id)
    elif query_type == 'yes/no':
        answer = submitCheckQuery(entity_id, property_id, prop_attribute_id)

    return answer

def searchEntity(entity, string_type):
    url = 'https://www.wikidata.org/w/api.php'
    if string_type != 'entity':
        url = url + '?type=' + string_type
    params = {'action':'wbsearchentities',
              'language':'en',
              'format':'json'}

    params['search'] = entity.rstrip()
    json = requests.get(url,params).json()
    
    print(entity, '->', json['search'][0]['label'])
    
    # Return the most likely entity
    if len(json['search']) > 0:
        if settings.verbose:
            print(json['search'][0]['id'])
        return json['search'][0]['id']

# Creates a query and returns the answer(s) on that query.
def submitQuery(entity_id, property_id):
    url = 'https://query.wikidata.org/sparql'
    query = '''
        SELECT ?itemLabel
        WHERE
        {{
            wd:{0} wdt:{1} ?item.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".}}
        }}
        '''.format(entity_id, property_id)

    data = requests.get(url, params={'query': query, 'format': 'json'}).json()

    answers = []
    for item in data['results']['bindings']:
        for var in item :
            answers.append(item[var]['value'])
    return answers
    
# Creates a query that checks whether the given property
# has appropriate attribute and returns the yes/no answer on that query.
def submitCheckQuery(entity_id, property_id, attribute_id):
    url = 'https://query.wikidata.org/sparql'
    query = '''
        ASK {{
            wd:{0} wdt:{1} ?attribute .
            FILTER(?attribute = wd:{2})
        }}
        '''.format(entity_id, property_id, attribute_id)

    data = requests.get(url, params={'query': query, 'format': 'json'}).json()

    answer = []
    if data['boolean'] == True:
        answer = ['Yes']
    else:
        answer = ['No']
    
return answer
