# Functions needed for making queries for WikiData
import requests
import settings
import traceback
import json
import simplejson
import datefinder
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
w_words_dict = {'what':'basic', 'who':'person', 'when':'date', 'where':'place',
                'why':'cause', 'how':'cause', 'which':'basic', 'how many':'count'}

def makeQuery(keywords):
    entity_id = []
    property_ids = []
    filters = []
     
    # Querying for IRIs
    
    # Identify query type
    if "question_word" in keywords:
        query_type = w_words_dict.get(keywords["question_word"][0].lower(), 'yes/no')
        if len(keywords["question_word"]) > 1 and keywords["question_word"][1] == 'many':
            query_type = 'count'
    else:
        query_type = 'yes/no'
    
    # Get list of possible properties
    if "property" in keywords:
        
        # Singularize property, if it's a noun
        blob = TextBlob(keywords["property"][0])
        prop = ' '.join([word.singularize() for word in blob.words])
        
        # Replace property, if it's a defficult one
        prop = property_dict.get(prop, prop)
        if settings.verbose:
            print('property:', prop)
        
        # Try to look for properties
        property_ids = searchEntities(prop, "property")
        
        # If no properties found, it could be occupation of a member in the group
        if not property_ids:
            property_ids = [{'id':str(searchEntity(prop, 'entity')), 'is_entity':True},
                             {'id':'P527'}]
    
    # Get entity IRI
    if "entity" in keywords:        
        entity_id = searchEntity(keywords["entity"][0], "entity")
    
    # Add filters from question
    if "property_attribute" in keywords:
        if keywords["question_id"][0] == 9:
            # Likely a 'yes/no question'
            # ('X is Y of Z', with (Z == property_attribute)? as required answer.)
            addFilter(filters, searchEntity(keywords["property_attribute"][0], "entity"))
            query_type = 'yes/no'
    
    # Add filters from questions
    if "specification" in keywords:       
        if keywords["question_id"][0] == 7:
            # Likely a 'X is Y of Z', with Z as required answer.
            addFilter(filters, searchEntity(keywords["specification"][0], "entity"))
            query_type = 'specified'
    
    qualifiers = []
    if "date_word" in keywords:
        date_word = keywords["date_word"][0]
        if date_word == "between" or date_word == "during":
            date1 = keywords["date1"][0].strftime("%Y-%m-%d")
            date2 = keywords["date2"][0].strftime("%Y-%m-%d")
            qualifiers.append(date1)
            qualifiers.append(date2)
        else:
            if settings.verbose:
                print("Dates have been wrongly analyzed.")

    # Firing the query
    answer = submitTypeQuery(entity_id, property_ids, filters, query_type, qualifiers)

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


def submitTypeQuery(entity_id, property_ids, filters, query_type, qualifiers):
    url = 'https://query.wikidata.org/sparql'
    
    qualifierVariables = ""
    qualifierLines = ""
    if len(qualifiers) != 0:
        qualifierVariables = "?startTime ?endTime"
        qualifierLines = '''
        ?statement pq:P580 ?startTime .
        ?statement pq:P582 ?endTime .
        '''

    # If it's a 'who'-question
    if query_type == 'person':
        # Format the query without adding extra line for standard property
        if not property_ids or not property_ids[0].get('is_entity', False) or not property_ids[0]['id']:
            query = query_dict[query_type][0].format(qualifierVariables, entity_id, '', qualifierLines)
        # If the property is member's occupation, add extra line to account for that
        else:
            extra_line = '?ps_ wdt:P106 wd:{0}.'.format(property_ids[0]['id'])
            query = query_dict[query_type][0].format(qualifierVariables, entity_id, extra_line, qualifierLines)
    else:
        # Otherwise the query formatting is generalized
        query = query_dict[query_type][0].format(qualifierVariables, entity_id, qualifierLines)

    data = []
    # Try to fire a query
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
    
    # Filter data with custom and default filters
    # Variable by which we filter is in query_dict[query_type][1]
    # Values by which we filter are in query_dict[query_type][2] + filters
    processed_data = filterBy(data, query_dict[query_type][1], query_dict[query_type][2] + filters)
    
    # Check what property is found in all filtered properties of the entity
    for prop_id in property_ids:
        for item in processed_data:
            if (chosen_property != None and item['wd']['value'] != chosen_property):
                continue
            if ("http://www.wikidata.org/entity/" + prop_id['id'] == item['wd']['value']):
                if len(qualifiers) != 0:
                    startCheck = False
                    endCheck = False
                    qStartTime = list(datefinder.find_dates(qualifiers[0], index=True))[0][0]
                    qEndTime = list(datefinder.find_dates(qualifiers[0], index=True))[0][0]
                    startTime = list(datefinder.find_dates(item['startTime']['value'], index=True))[0][0].replace(tzinfo=None)
                    endTime = list(datefinder.find_dates(item['endTime']['value'], index=True))[0][0].replace(tzinfo=None)
                    if startTime >= qStartTime:
                        startCheck = True
                    if endTime <= qEndTime:
                        endCheck = True
                    if startCheck or endCheck:
                        answers.append(item['ps_Label']['value'])
                else:
                    answers.append(item['ps_Label']['value'])
                chosen_property = "http://www.wikidata.org/entity/" + prop_id['id']
    
    # Desperate case, when no property was found print out all the filtered values
    if chosen_property == None:
        for item in processed_data:
            if len(qualifiers) != 0:
                startCheck = False
                endCheck = False
                qStartTime = list(datefinder.find_dates(qualifiers[0], index=True))[0][0]
                qEndTime = list(datefinder.find_dates(qualifiers[0], index=True))[0][0]
                startTime = list(datefinder.find_dates(item['startTime']['value'], index=True))[0][0].replace(tzinfo=None)
                endTime = list(datefinder.find_dates(item['endTime']['value'], index=True))[0][0].replace(tzinfo=None)
                if startTime >= qStartTime:
                    startCheck = True
                if endTime <= qEndTime:
                    endCheck = True
                if startCheck or endCheck:
                    answers.append(item['ps_Label']['value'])
            else:
                answers.append(item['ps_Label']['value'])
    
    # Optionally, convert answer to binary
    if query_type == 'yes/no':
        if not answers:
            answers = ['No']
        else:
            answers = ['Yes']
    elif query_type == 'count':
        if not (len(answers) == 1 and answers[0].isdigit()):
            # The property does not give number, we have to count manually
            answers = [str(len(answers))]
            
        
    if settings.verbose:
        print('chosen property:', chosen_property)
    return answers

query_dict = {
    'basic':['''
        SELECT ?wd ?ps_Label {0} {{
            VALUES (?entity) {{(wd:{1})}}
            
            ?entity ?p ?statement .
            ?statement ?ps ?ps_ .
            {2}
                        
            ?wd wikibase:statementProperty ?ps.
            
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 'wd', []],
    'count':['''
        SELECT ?wd ?ps_Label {{
            VALUES (?entity) {{(wd:{0})}}
            
            ?entity ?p ?statement .
            ?statement ?ps ?ps_ .
            
            ?wd wikibase:statementProperty ?ps.
            
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 'wd', []],
    'specified':['''
        SELECT ?wd ?ps_Label ?spec {0} {{
        VALUES (?entity) {{(wd:{1})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        {2}
        
        ?wd wikibase:statementProperty ?ps.
        ?ps_ wdt:P31/wdt:P279 ?spec.
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''', 'spec', []],
    'date':['''
        SELECT ?wd ?ps_Label {0} {{
        VALUES (?entity) {{(wd:{1})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        {2}
        
        ?wd wikibase:statementProperty ?ps.
        FILTER(DATATYPE(?ps_) = xsd:dateTime).
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''','wd', []],
    'place': ['''
        SELECT ?wd ?ps_Label ?is_place {0} {{
          VALUES (?entity) {{(wd:{1})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          {2}
          
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P31 ?is_place.
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 'is_place', ['http://www.wikidata.org/entity/Q18635217']],
    'person':['''
        SELECT ?wd ?ps_Label ?is_human {0} {{
          VALUES (?entity) {{(wd:{1})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          
          ?wd wikibase:statementProperty ?ps.
          ?ps_ wdt:P31 ?is_human.
          
          {2}
          
          {3}
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''','is_human', ['http://www.wikidata.org/entity/Q5']],
    'cause':['''
        SELECT ?wd ?ps_Label ?is_cause {0} {{
          VALUES (?entity) {{(wd:{1})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          {2}
        
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P1629 ?cause_type.
          ?cause_type wdt:P279 ?is_cause.
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''','is_cause', ['http://www.wikidata.org/entity/Q179289']],
    'yes/no':['''
        SELECT ?wd ?ps_Label ?ps_ {0} {{
        VALUES (?entity) {{(wd:{1})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        {2}
        
        ?wd wikibase:statementProperty ?ps.
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''', 'ps_', []]
    }
        
def filterBy(data, var_id, entities_id):
    new_data = []
    
    # Look through all values of var_id, return only
    # item with values available in entities_id
    for item in data['results']['bindings']:
        if (not entities_id or item[var_id]['value'] in entities_id):
            new_data.append(item)
    return new_data

def addFilter(filters, f):
    
    # If there is a filter to append, append it
    if f != None:
        filters.append('http://www.wikidata.org/entity/' + f)
