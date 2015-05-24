#https://github.com/dgrtwo/ParsePy
from parse_rest.connection import register
from tables import *

class CourseMIRROR:
    def __init__(self, app_id, api_key, master_key):
        register(app_id, api_key)
    
    def get_data(self, table, cid=None):
        data = {'results':[]}

        if cid == None:
            rows = table.Query.all()
        else:
            rows = table.Query.filter(cid=cid)
        
        totalN = 0
        N = 100
        page = rows.limit(N)
        while(True):
            dict = {}
            for row in page:
                for key in row.__dict__.keys():
                    if key in ['_created_at', '_updated_at']: continue
                    dict[key] = row.__dict__[key]
            
            data['results'].append(dict)
            
            totalN += N
            page = rows.skip(totalN).limit(N)
            
            if len(page) == 0:
                break
            
        return data

    def get_lectures(self, cid=None):
        return self.get_data(Lecture, cid)
    
    def get_reflections(self, cid):
        return self.get_data(Reflection, cid)
    
    def get_questions(self, cid):
        courses = self.get_data(Course, cid)
        
        for course in courses:
            return course.questions 
        
        return None
    
    def run(self, cid):
        #get reflections
        reflections = self.get_reflections(cid)
        
        #run senna
        
        #run mead
        
        #run Similar
        
        #run ClusterA
        
    
if __name__ == '__main__':
    
    import ConfigParser
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/myconfig.cfg')
    
    cid = config.get('course', 'cid')
    course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY')
                                        )
    
    #course_mirror_server.run(cid)
    
    print course_mirror_server.get_data(Reflection, cid)
    