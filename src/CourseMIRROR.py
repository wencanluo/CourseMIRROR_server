#https://github.com/dgrtwo/ParsePy
from parse_rest.connection import register
from tables import *
import json
import os
import cmd
from cmd import Cmd
import subprocess
import re

from parse_rest.user import User

class CourseMIRROR:
    def __init__(self, app_id, api_key, master_key):
        register(app_id, api_key)
        
        self.demo = User.login("demo", "demo")
    
    def get_data_top(self, table, topK, cid=None, order_by = None):
        data = {'results':[]}

        if cid == None:
            if order_by != None:
                rows = table.Query.all().order_by(order_by)
            else:
                rows = table.Query.all()
        else:
            if order_by != None:
                rows = table.Query.filter(cid=cid).order_by(order_by)
            else:
                rows = table.Query.filter(cid=cid)
        
        assert(topK <= 100)
        page = rows.limit(topK)
    
        dict = {}
        for row in page:
            for key in row.__dict__.keys():
                if key in ['_created_at', '_updated_at']: continue
                dict[key] = row.__dict__[key]
        
        data['results'].append(dict)
               
        return data
    
    def get_data(self, table, cid=None, order_by = None):
        data = {'results':[]}

        if cid == None:
            if order_by != None:
                rows = table.Query.all().order_by(order_by)
            else:
                rows = table.Query.all()
        else:
            if order_by != None:
                rows = table.Query.filter(cid=cid).order_by(order_by)
            else:
                rows = table.Query.filter(cid=cid)
        
        totalN = 0
        N = 100
        page = rows.limit(N)
        while(True):
            for row in page:
                dict = {}
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
    
    def get_max_lecture_num(self, cid):
        reflection = self.get_data_top(Reflection, 1, cid, order_by='-lecture_number')['results']
        
        return reflection[0]['lecture_number']
    
    def run(self, cid):
         max_lecture = self.get_max_lecture_num(cid)
          
#          #get reflections
#          reflections = self.get_reflections(cid)
#          jsonfile = '../data/CourseMIRROR/reflections.json' 
#          with open(jsonfile, 'w') as outfile:
#              json.dump(reflections, outfile, encoding='utf-8', indent=2)
#           
#          #run senna
#          import CourseMirror_Survey
#          os.system('python CourseMirror_Survey.py ' + str(cid) + ' ' +  str(max_lecture))
#   
#          cmd = 'cmd /C "runSennaCourseMirror.bat '+str(cid)+ ' ' + str(max_lecture) + '"'
#          os.system(cmd)
#           
        #     . extract phrases (CourseMirror_phrasebasedShallowSummary.py)
         cmd = 'python CourseMirror_phrasebasedShallowSummary.py ' + str(cid) + ' ' +  str(max_lecture)
         print cmd
         os.system(cmd)
#          
#         #     . get PhraseMead input (CourseMirror_MeadPhrase.py)
#          cmd = 'python CourseMirror_MeadPhrase.py ' + str(cid) + ' ' +  str(max_lecture)
#          print cmd
#          os.system(cmd)
#          #     . get PhraseMead output
#          meaddir = '/cygdrive/e/project/Fall2014/summarization/mead/bin/'
#          cmd = './get_mead_summary_phrase_coursemirror.sh ' + str(cid) + ' ' +  str(max_lecture)
#          os.chdir(meaddir)
#          retcode = subprocess.call([cmd], shell=True)
#          print retcode
        
                
        #     . get LSA results (CourseMirrorphrase2phraseSimilarity.java)
        #os.system('pause')
        
        #     . get ClusterARank (CourseMirror_phraseClusteringbasedShallowSummaryKmedoid-New-Malformed-LexRank.py)
        #os.system("python CourseMirror_phraseClusteringbasedShallowSummaryKmedoid-New-Malformed-LexRank.py")
        
        #     . submit Summary (SummaryUpdate.py)
        
        
        #run mead
        
        #run Similar
        
        #run ClusterA
    
    def test(self):
        #self.get_max_lecture_num('IE256')
        #self.get_data(Reflection, 'NAACL2015')
        pass
    
    def change_demo_user(self):
        current_token = self.demo.token
        
        regex = re.compile("([a-z])(\d+)")
        
        gs = regex.findall(current_token)
        
        new_tokens = []
        if gs:
            for g in gs:
                if g[0] == 'n':
                    id = int(g[1]) + 1
                    new_id = "%04d" % (id,)
                    print "new user token:", new_id
                    new_tokens.append('"' +g[0] + new_id + '"')
                else:
                    new_tokens.append('"' +g[0] + g[1] + '"')
        
        self.demo.token = '['+','.join(new_tokens)+']' 
        self.demo.save()
                
if __name__ == '__main__':
    
    import ConfigParser
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/myconfig.cfg')
    
    cid = config.get('course', 'cid')
    course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY')
                                        )
    
    #course_mirror_server.test()
    
    #course_mirror_server.run(cid)
    course_mirror_server.change_demo_user()
    
    
    