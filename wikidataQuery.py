# Functions needed for making queries for WikiData
import requests

def makeQuery(keywords):
    property_id = None
    entity_id = None
    for keyword in keywords:
        if keyword[1] == "property":
            property_id = searchEntity(keyword[0], "property")
        elif keyword[1] == "entity":
            entity_id = searchEntity(keyword[0], "entity")

    return submitQuery(entity_id, property_id)

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
