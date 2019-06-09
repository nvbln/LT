# Functions needed for making queries for WikiData
import requests
import settings
import traceback
import json
import simplejson
# Installable with 'pip install textblob'
from textblob import TextBlob

# A pre-defined dictionary for difficult terms
property_dict = {'band members': 'has part', 'members': 'has part',
                  'member': 'has part', 'band member': 'has part',
                  'founding year': 'inception', 'bandmember': 'has part',
                  'bandmembers': 'has part', 'founding': 'inception',
                  'play': 'instrument', 'real name':'birth name',
                  'album':'part of'}

# List of w-words, feel free to add any words I forgot
w_words_dict = {'What':'basic', 'Who':'person', 'When':'date', 'Where':'place',
                'Why':'cause', 'How':'cause', 'Which':'basic', 'How many':'count'}

def makeQuery(keywords):
    property_id = []
    entity_id = []
    prop_attribute_id = []
    properties_id = []
    
    # Querying for IRIs
    if "question_word" in keywords:
        query_type = w_words_dict.get(keywords["question_word"][0], 'yes/no')
    else:
        query_type = 'yes/no'
    
    if "property" in keywords:
        blob = TextBlob(keywords["property"][0])
        prop = ' '.join([word.singularize() for word in blob.words])
        prop = property_dict.get(prop, prop)
        if settings.verbose:
            print('property:', prop)
        properties_id = searchEntities(prop, "property")
        if len(properties_id) > 0:
            property_id = properties_id[0]['id']
    
    if "entity" in keywords:        
        entity_id = searchEntity(keywords["entity"][0], "entity")
    
    # TODO attribute is not always entity, right? needs to be fixed
    if "property_attribute" in keywords:
        prop_attribute_id = searchEntity(keywords["property_attribute"][0], "entity")
    
    # Firing the query
    answer = []
    if query_type == 'basic':
        answer = submitTypeQuery(entity_id, properties_id, 'basic')
        
    elif query_type == 'yes/no':
        answer = submitCheckQuery(entity_id, property_id, prop_attribute_id)
        
    # TODO make query for each type
    elif query_type == 'date':
        answer = submitTypeQuery(entity_id, properties_id, 'date')
        
    elif query_type == 'place':
        answer = submitTypeQuery(entity_id, properties_id, 'place')
        
    elif query_type == 'person':
        answer = submitTypeQuery(entity_id, properties_id, 'person')
        
    elif query_type == 'cause':
        answer = submitTypeQuery(entity_id, properties_id, 'cause')
    # TODO extract how many questions properly
    #elif query_type == 'count':

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
    
    # Return the most likely entity
    if len(json['search']) > 0:
         if settings.verbose:
             print(entity + '->' + json['search'][0]['label'])
         if settings.verbose:
             print(json['search'][0]['id'])
         return json['search'][0]['id']

def searchEntities(entity, string_type):
    url = 'https://www.wikidata.org/w/api.php'
    if string_type != 'entity':
        url = url + '?type=' + string_type
    params = {'action':'wbsearchentities',
              'language':'en',
              'format':'json'}

    params['search'] = entity.rstrip()
    json = requests.get(url,params).json()
    
    # Return all the entities
    return json['search']

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

    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    except json.decoder.JSONDecodeError:
        if settings.verbose:
            print("Problem with the following query:")
            print(query)
            print(traceback.format_exc())
        return []
    
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

    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    except (json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError):
        if settings.verbose:
            print("Problem with the following query:")
            print(query)
            print(traceback.format_exc())
        return []
    
    answer = []
    if data['boolean'] == True:
        answer = ['Yes']
    else:
        answer = ['No']
    return answer

def submitTypeQuery(entity_id, properties_id, query_type):
    url = 'https://query.wikidata.org/sparql'
    query = query_dict[query_type][0].format(entity_id)
    data = []
    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    except json.decoder.JSONDecodeError:
        if settings.verbose:
            print("Problem with the following query:")
            print(query)
            print(traceback.format_exc())
        return []        
    
    
    answers = []
    chosen_property = None
    
    processed_data = filterBy(data, query_dict[query_type][1], query_dict[query_type][2])

    for prop_id in properties_id:
        for item in processed_data:
            if (chosen_property != None and item['wd']['value'] != chosen_property):
                continue
            if ("http://www.wikidata.org/entity/" + prop_id['id'] == item['wd']['value']):
                answers.append(item['ps_Label']['value'])
                chosen_property = "http://www.wikidata.org/entity/" + prop_id['id']
    if settings.verbose:
        print('chosen property:', chosen_property)
    return answers

query_dict = {
    'basic':['''
        SELECT ?wd ?ps_Label {{
            VALUES (?entity) {{(wd:{0})}}
            
            ?entity ?p ?statement .
            ?statement ?ps ?ps_ .
            
            ?wd wikibase:statementProperty ?ps.
            
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 'wd', []],
    'date':['''
        SELECT ?wd ?ps_Label{{
        VALUES (?entity) {{(wd:{0})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        
        ?wd wikibase:statementProperty ?ps.
        FILTER(DATATYPE(?ps_) = xsd:dateTime).
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''','is_date', []],
    'place': ['''
        SELECT ?wd ?ps_Label ?is_place{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P31 ?is_place.
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 'is_place', ['http://www.wikidata.org/entity/Q18635217']],
    'person':['''
        SELECT ?wd ?ps_Label ?is_human {{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
        
          ?wd wikibase:statementProperty ?ps.
          ?ps_ wdt:P31 ?is_human.
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''','is_human', ['http://www.wikidata.org/entity/Q5']],
    'cause':['''
        SELECT ?wd ?ps_Label ?is_cause{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
        
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P1629 ?cause_type.
          ?cause_type wdt:P279 ?is_cause.
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''','is_cause', ['http://www.wikidata.org/entity/Q179289']]
    }
        
def filterBy(data, var_id, entities_id):
    new_data = []
    for item in data['results']['bindings']:
        if (not entities_id or item[var_id]['value'] in entities_id):
            new_data.append(item)
    return new_data