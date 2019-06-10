# Functions needed for making queries for WikiData
import requests
import settings
import traceback
import json
import simplejson
from textblob import TextBlob

# TODO account for band member occupation properties
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
    property_ids = []
    filters = []
    
    # Querying for IRIs
    if "question_word" in keywords:
        query_type = w_words_dict.get(keywords["question_word"][0], 'yes/no')
    else:
        query_type = 'yes/no'
    
    if "property" in keywords:
        blob = TextBlob(' '.join(keywords["property"]))
        if 'influence' in blob:
            temp = ' '.join(keywords["entity"])
            keywords["entity"] = keywords["property_attribute"]
            keywords["property_attribute"] = [temp]
            
        prop = ' '.join([word.singularize() for word in blob.words])
        prop = property_dict.get(prop, prop)
        if settings.verbose:
            print('property:', prop)
        property_ids = searchEntities(prop, "property")
        
        if not property_ids:
            property_ids = [{'id':searchEntity(prop, 'entity'), 'is_entity':True},
                             {'id':'P527'}]
        if len(property_ids) > 0:
            property_id = property_ids[0]['id']
    
    if "entity" in keywords:        
        entity_id = searchEntity(keywords["entity"][0], "entity")
    
    # TODO attribute is not always entity, right? needs to be fixed
    if "property_attribute" in keywords:
        addFilter(filters, searchEntity(keywords["property_attribute"][0], "entity"))
        if keywords["question_id"][0] == 7:
            # Likely a 'yes/no question'
            query_type = 'yes/no'
    
    if "specification" in keywords:       
        addFilter(filters, searchEntity(keywords["specification"][0], "entity"))
        if keywords["question_id"][0] == 9:
            # Likely a 'X is Y of Z', with Z as required answer.
            query_type = 'specified'
    
    
    
    # Firing the query
    answer = []
    if query_type == 'basic':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'basic')
        
    elif query_type == 'yes/no':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'yes/no')
        
    # TODO make query for each type
    elif query_type == 'date':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'date')
        
    elif query_type == 'place':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'place')
        
    elif query_type == 'person':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'person')
        
    elif query_type == 'cause':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'cause')
    
    elif query_type == 'specified':
        answer = submitTypeQuery(entity_id, property_ids, filters, 'specified')
        
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

def submitTypeQuery(entity_id, property_ids, filters, query_type):
    url = 'https://query.wikidata.org/sparql'
    if query_type == 'person':
        print(property_ids)
        if not property_ids or not property_ids[0].get('is_entity', False):
            query = query_dict[query_type][0].format(entity_id, '')
        else:
            extra_line = '?ps_ wdt:P106 wd:{0}.'.format(property_ids[0]['id'])
            query = query_dict[query_type][0].format(entity_id, extra_line)
    else:
        query = query_dict[query_type][0].format(entity_id)
    data = []
    
    try:
        data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    except (json.decoder.JSONDecodeError, simplejson.errors.JSONDecodeError):
        if settings.verbose:
            print("Problem with the following query:")
            print(query)
            print(traceback.format_exc())
        return []
    
    answers = []
    chosen_property = None
    processed_data = filterBy(data, query_dict[query_type][1], query_dict[query_type][2] + filters)

    for prop_id in property_ids:
        for item in processed_data:
            if (chosen_property != None and item['wd']['value'] != chosen_property):
                continue
            if ("http://www.wikidata.org/entity/" + prop_id['id'] == item['wd']['value']):
                answers.append(item['ps_Label']['value'])
                chosen_property = "http://www.wikidata.org/entity/" + prop_id['id']
    
    # Desperate case, when no property was found
    if chosen_property == None:
        for item in processed_data:
            answers.append(item['ps_Label']['value'])
    
    if query_type == 'yes/no':
        if not answers:
            answers = ['No']
        else:
            answers = ['Yes']
        
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
    'specified':['''
        SELECT ?wd ?ps_Label ?spec {{
        VALUES (?entity) {{(wd:{0})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        
        ?wd wikibase:statementProperty ?ps.
        ?ps_ wdt:P31/wdt:P279 ?spec.
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''', 'spec', []],
    'date':['''
        SELECT ?wd ?ps_Label{{
        VALUES (?entity) {{(wd:{0})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        
        ?wd wikibase:statementProperty ?ps.
        FILTER(DATATYPE(?ps_) = xsd:dateTime).
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''','wd', []],
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
          
          {1}
        
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
        }}''','is_cause', ['http://www.wikidata.org/entity/Q179289']],
    'yes/no':['''
        SELECT ?wd ?ps_Label ?ps_ {{
        VALUES (?entity) {{(wd:{0})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        
        ?wd wikibase:statementProperty ?ps.
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''', 'ps_', []]
    }
        
def filterBy(data, var_id, entities_id):
    new_data = []
    for item in data['results']['bindings']:
        if (not entities_id or item[var_id]['value'] in entities_id):
            new_data.append(item)
    return new_data

def addFilter(filters, f):
    if f != None:
        filters.append('http://www.wikidata.org/entity/' + f)