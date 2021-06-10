import requests
import json


api_key='*'
headers = {'Authorization': 'Bearer %s' % api_key}

url='https://api.yelp.com/v3/businesses/search'
cuisines = ['Mexican','Chinese','Italian','Thai','Japanese','Mediterranean']

out={}
params = {'term':'Mexican','location':'Manhattan','limit':50,'offset':0}
uniqueid = set()
for c in cuisines:
    print(c)
    params['term']=c

    for i in range(21):
        params['offset']=50*i
        req=requests.get(url, params=params, headers=headers)
        print('The status code is {}'.format(req.status_code))
        if req.status_code==200:
            response=json.loads(req.text)
            uniquerest = []
            for r in response['businesses']:
                if r['id'] not in uniqueid:
                    uniqueid.add(r['id'])
                    uniquerest.append(r)

            if c in out:
                out[c].extend(uniquerest)
            else:
                out[c]=uniquerest
            #print(len(out['businesses']))
with open('restaurants1.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=4)
