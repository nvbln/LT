# Functions needed for making queries for WikiData
import requests
import settings

# A pre-defined dictionary for difficult terms
property_dict = {'band members': 'has part', 'members': 'has part',
                  'member': 'has part', 'band member': 'has part',
                  'founding year': 'inception', 'bandmember': 'has part',
                  'bandmembers': 'has part', 'founding': 'inception',
                  'play': 'instrument', 'join': 'has part'}

# List of w-words, feel free to add any words I forgot
w_words_dict = {'What':'basic', 'Who':'basic', 'When':'date', 'Where':'place',
                'Why':'cause', 'How':'cause', 'Which':'basic', 'How many':'count'}

qualifier_dict = {'join': 'start time', 'start': 'start time', 'leave': 'end    time', 'quit': 'end time', 'stop': 'end time'}


def makeQuery(keywords):
    property_id = None
    entity_id = None
    prop_attribute_id = None
    properties_id = None
    specification_id = None
    
    query_type = None

    for keyword in keywords:
        if keyword[1] == "question_word":
            query_type = w_words_dict.get(keyword[0], 'yes/no')
                
        elif keyword[1] == "property":
            prop = property_dict.get(keyword[0], keyword[0])
            qual = qualifier_dict.get(keyword[0], keyword[0])
            properties_id = searchEntities(prop, "property")
            if len(properties_id) > 0:
                property_id = properties_id[0]['id']
            else:
                property_id = []
            
        elif keyword[1] == "entity":
            entWord = keyword[0]
            entity_id = searchEntity(keyword[0], "entity")
            
        elif keyword[1] == "property_attribute":
            # TODO attribute is not always entity, right? needs to be fixed
            prop_attribute_id = searchEntity(keyword[0], "entity")

        elif keyword[1] == "specification":
            # TODO attribute is not always entity, right? needs to be fixed
            specification_id = searchEntity(keyword[0], "entity")
            
    answer = []
    
    if query_type == 'basic':
        answer = submitQuery(entity_id, property_id)
    elif query_type == 'yes/no':
        answer = submitCheckQuery(entity_id, property_id, prop_attribute_id)
    # TODO make query for each type
    elif query_type == 'date' and specification_id == None:
        answer = submitTypeQuery(entity_id, properties_id, 'date')
    
    elif specification_id is not None:
        answer = submitQualifiedDate(entWord, properties_id, specification_id, qual)
        
    elif query_type == 'place':
        answer = submitTypeQuery(entity_id, properties_id, 'place')

        
    elif query_type == 'person':
        answer = submitTypeQuery(entity_id, properties_id, 'person')
    elif query_type == 'cause':
        answer = submitTypeQuery(entity_id, properties_id, 'cause')
    # TODO extract how many questions properly
    #elif query_type == 'count':
    print(query_type)
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

def submitTypeQuery(entity_id, properties_id, query_type):
    url = 'https://query.wikidata.org/sparql'
    query = query_dict[query_type].format(entity_id)
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    
    answers = []
    chosen_property = None
    for prop_id in properties_id:
        for item in data['results']['bindings']:
            if (chosen_property != None and item['wd']['value'] != chosen_property):
                continue
            if ("http://www.wikidata.org/entity/" + prop_id['id'] == item['wd']['value']):
                answers.append(item['ps_Label']['value'])
                chosen_property = "http://www.wikidata.org/entity/" + prop_id['id']
    return answers

def submitQualifiedDate(entWord, properties_id, specification_id, qual):
    url = 'https://query.wikidata.org/sparql'
    query = '''
        SELECT ?wd ?ps_Label ?pq_Label ?wdpqLabel{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          
          ?wd wikibase:statementProperty ?ps.
          
          OPTIONAL {{
          ?statement ?pq ?pq_ .
          ?wdpq wikibase:qualifier ?pq
          }}
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}
    '''.format(specification_id)
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()
    
    answers = []
    chosen_property = None
    for prop_id in properties_id:
        for item in data['results']['bindings']:
            if(item['ps_Label']['value'] == entWord):
                # if(qual == item['wdpqLabel']['value'])
                if (chosen_property != None and item['wd']['value'] != chosen_property):
                    continue
                if ("http://www.wikidata.org/entity/" + prop_id['id'] == item['wd']['value']):
                    chosen_property = prop_id['id']
                    #print(qual, item['wdpqLabel']['value'])
                    answers.append(item['pq_Label']['value'])
    return answers

query_dict = {
    'date':'''
        SELECT ?wd ?ps_Label{{
        VALUES (?entity) {{(wd:{0})}}
        
        ?entity ?p ?statement .
        ?statement ?ps ?ps_ .
        
        ?wd wikibase:statementProperty ?ps.
        FILTER(DATATYPE(?ps_) = xsd:dateTime).
        
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}''',
    'place': '''
        SELECT ?wd ?ps_Label{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
          
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P31 wd:Q18635217.
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''', 
    'person':'''
        SELECT ?wd ?ps_Label{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
        
          ?wd wikibase:statementProperty ?ps.
          ?ps_ wdt:P31 wd:Q5.
        
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}''',
    'cause':'''
        SELECT ?wd ?ps_Label{{
          VALUES (?entity) {{(wd:{0})}}
        
          ?entity ?p ?statement .
          ?statement ?ps ?ps_ .
        
          ?wd wikibase:statementProperty ?ps.
          ?wd wdt:P1629 ?cause_type.
          ?cause_type wdt:P279 wd:Q179289.
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}'''
    }
