import pandas as pd
import requests as r
import json
import explorer as exp


class Connection():
    def __init__(self, api_name = None):
        if 'eits' not in api_name and api_name != None:
            if api_name in exp.cAPIs.keys():
                curr = exp.cAPIs[api_name]
                self.title = curr['title']
                self.identifier = curr['identifier']
                self.description = curr['description']
                self.cxn = unicode(curr['webService'] + u'?')
                self.__urls__ = {k.strip('c_')[:-4]:v for k,v in curr.iteritems() if k.endswith('Link')}

                if 'variables' in self.__urls__.keys():
                    v = pd.DataFrame()
                    self.variables = v.from_dict(r.get(self.__urls__['variables']).json().values()[0]).T
                if 'geography' in self.__urls__.keys():
                    res = r.get(self.__urls__['geography']).json()
                    self.geographies = {k:pd.DataFrame().from_dict(v) for k,v \
                                                            in res.iteritems()}
                if 'tags' in self.__urls__.keys():
                    self.tags = r.get(self.__urls__['tags']).json().values()[0]

                if 'examples' in self.__urls__.keys():
                    self.example_entries = r.get(self.__urls__['examples']).json()

            elif api_name in exp.tigers:
                e = exp.explain(api_name)
                self.identifier = e.keys()[0]
                self.description = e.values()[0]
                self.title = self.identifier
                self.cxn = exp.tiger_url + '/' + self.identifier + u'MapServer'
                curr = exp._qjson(self.cxn)
                self.geographies = pd.DataFrame(curr['layers'])
                self.variables = pd.DataFrame()
                self.tags = curr['Keywords']
                self.example_entries = None

            else:
                raise ValueError('Pick dataset identifier using the census_pandas.explorer.available() function')



    def __repr__(self):
        return unicode('Connection to ' + self.title + ' (ID: ' + self.identifier + ')')

    def query(self, cols = [], geo_unit = u'us:00', geo_filter = {}, apikey = None, **kwargs):
        self.last_query = self.cxn
        self.last_query += u'get=' + ','.join(col for col in cols)
        
        self.last_query += u'&for=' + geo_unit

        if geo_filter != {}:
            self.last_query += u'&in='
            for key,value in geo_filter.iteritems():
                self.last_query += key + ':' + value + '+'
            self.last_query = self.last_query[:-1]
        
        for key,val in kwargs.iteritems():
            self.last_query += u'&' + key + '=' + val
        
        if apikey is not None:
            self.last_query += u'&key=' + apikey
        res = r.get(self.last_query)
        if res.status_code == 204:
            raise r.HTTPError(str(res.status_code) + ' error: no records matched your query')
        try:
            res = res.json()
            return pd.DataFrame().from_records(res[1:], columns=res[0])
        except ValueError:
            if res.status_code == 400:
                raise r.HTTPError(str(res.status_code) + ' ' + [l for l in res.iter_lines()][0])
            else:
                res.raise_for_status()
