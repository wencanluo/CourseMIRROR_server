#https://github.com/dgrtwo/ParsePy
from parse_rest.connection import register
import parse_rest

from tables import *
import json
import os
import cmd
from cmd import Cmd
import subprocess
import re
import fio

TypeMap = {"q1":'q1_summaries', "q2":'q2_summaries', "q3":'q3_summaries', "q4":'q4_summaries'}

from parse_rest.user import User

class CourseMIRROR:
    def __init__(self, app_id, api_key, master_key):
        register(app_id, api_key)

        self.old_N = 0
    
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
    
    def get_data(self, table, cid=None, order_by = None, withtime=False):
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
                    if not withtime:
                        if key in ['_created_at', '_updated_at']: continue
                    dict[key] = row.__dict__[key]
            
                data['results'].append(dict)
            
            totalN += N
            page = rows.skip(totalN).limit(N)
            
            if len(page) == 0:
                break
            
        return data
    
    def print_data(self, table, cid=None):
        data = self.get_data(table, cid, withtime=True)
        
        for dict in data['results']:
            for key in dict.keys():
                print dict[key], '\t',
            print
    
    def get_lectures(self, cid=None):
        return self.get_data(Lecture, cid)
    
    def get_reflections(self, cid):
        return self.get_data(Reflection, cid)
    
    def get_questions(self, cid):
        courses = self.get_data(Course, cid)
        
        for course in courses['results']:
            return json.loads(course['questions'])
        
        return None
    
    def get_max_lecture_num(self, cid):
        reflection = self.get_data_top(Reflection, 1, cid, order_by='-lecture_number')['results']
        
        return reflection[0]['lecture_number']
    
    def remove_sumamry(self, cid):
        max_lecture = self.get_max_lecture_num(cid)
        
        try:
            summary_Object = Summarization.Query.get(cid=cid, lecture_number = max_lecture, method='ClusterARank')
            summary_Object.delete()
        except parse_rest.query.QueryResourceDoesNotExist:
            pass
    
    def upload_summary(self, cid, lectures=None):
        #only sumbit the last summary
        max_lecture = self.get_max_lecture_num(cid)
        
        if lectures:
            sheets = lectures
            
        if lectures==None:
            sheets = range(0, max_lecture)
            
        for i in sheets:
            lecture = i + 1
            
            path = "../data/" + str(cid) + '/mead/ClusterARank/' + str(lecture)+ '/'
            if not fio.IsExistPath(path): continue
            
            dict = {}
            for q in self.get_questions(cid):
                filename = path + q + '.summary'
                if not fio.IsExist(filename): continue
                
                lines = fio.ReadFile(filename)
                if len(lines) == 0: continue
                
                summary = []
                weight = []
                
                for line in lines:
                    summary.append(line.decode('latin-1').strip())
                    
                summarydict = {}
                summarydict['summaryText'] = summary
                
                sourcefile = path + q + '.summary.source'
                if not fio.IsExist(sourcefile):
                    for s in summary:
                        weight.append(1.0)
                else:
                    sources = [line.strip().split(",") for line in fio.ReadFile(sourcefile)]
                    
                    assert(len(sources) == len(summary))
                    summarydict['Sources'] = sources
                    
                    for source in sources:
                        weight.append(len(source))
                    
                summarydict['weight'] = weight
                
                dict[TypeMap[q]] = summarydict
            
            #get the object
            try:
                summary_Object = Summarization.Query.get(cid=cid, lecture_number = lecture, method='ClusterARank')
            except parse_rest.query.QueryResourceDoesNotExist:
                summary_Object = Summarization(cid=cid, lecture_number = lecture, method='ClusterARank')
            
            for key in dict:
                print key
                summary_Object.__dict__[key] = json.dumps(dict[key])
            
            #update the object
            summary_Object.save()
        
    def run(self, cid, summarylastlecture=False):
        max_lecture = self.get_max_lecture_num(cid)
        print "max_lecture", max_lecture
        
        #get reflections
        reflections = self.get_reflections(cid)
        jsonfile = '../data/CourseMIRROR/reflections.json' 
        with open(jsonfile, 'w') as outfile:
            json.dump(reflections, outfile, encoding='utf-8', indent=2)
        
        #get lectures
        lectures = self.get_lectures(cid)
        jsonfile = '../data/CourseMIRROR/lectures.json' 
        with open(jsonfile, 'w') as outfile:
            json.dump(lectures, outfile, encoding='utf-8', indent=2)
        
        self.N = len(reflections['results'])
        print "total number of reflections:", self.N
         
        if self.N == self.old_N: #no need to summary
            return
         
        self.old_N = self.N
        
        #run senna
        os.system('python CourseMirror_Survey.py ' + str(cid) + ' ' +  str(max_lecture))
        
        os.system('python student_track.py ' + str(cid) + ' ' +  str(max_lecture))
          
        cmd = 'cmd /C "runSennaCourseMirror.bat '+str(cid)+ ' ' + str(max_lecture) + '"'
        os.system(cmd)
             
        #     . extract phrases (CourseMirror_phrasebasedShallowSummary.py)
        cmd = 'python CourseMirror_phrasebasedShallowSummary.py ' + str(cid) + ' ' +  str(max_lecture)
        print cmd
        os.system(cmd)
            
        #     . get PhraseMead input (CourseMirror_MeadPhrase.py)
        cmd = 'python CourseMirror_MeadPhrase.py ' + str(cid) + ' ' +  str(max_lecture)
        print cmd
        os.system(cmd)
        
        olddir = os.path.dirname(os.path.realpath(__file__))
        
        #     . get PhraseMead output
        meaddir = '/cygdrive/e/project/Fall2014/summarization/mead/bin/'
        cmd = './get_mead_summary_phrase_coursemirror.sh ' + str(cid) + ' ' +  str(max_lecture)
        os.chdir(meaddir)
        retcode = subprocess.call([cmd], shell=True)
        print retcode
        #subprocess.call("exit 1", shell=True)
        
        os.chdir(olddir)
        #     . get LSA results (CourseMirrorphrase2phraseSimilarity.java)
        cmd = 'cmd /C "runLSA.bat '+str(cid)+ ' ' + str(max_lecture) + '"'
        os.system(cmd)
         
        #     . get ClusterARank (CourseMirror_phraseClusteringbasedShallowSummaryKmedoid-New-Malformed-LexRank.py)
        cmd = "python CourseMirror_ClusterARank.py " + str(cid) + ' ' +  str(max_lecture)
        print cmd
        os.system(cmd)
        
        #     . submit Summary (SummaryUpdate.py)
        
        if summarylastlecture == 1:
            lectures=range(max_lecture-2, max_lecture)
        else:
            lectures=range(max_lecture-2, max_lecture-1)
        
        self.upload_summary(cid, lectures=lectures)
        
    def test(self):
        #self.get_max_lecture_num('IE256')
        #self.get_data(Reflection, 'NAACL2015')
        print self.get_questions('NAACL2015')
#         try:
#             summary = Summarization.Query.get(cid='PHYSs0175', lecture_number= 41, method='ClusterARank')
#         except parse_rest.query.QueryResourceDoesNotExist:
#             pass
        #print summary.cid, summary.q1_summaries
        
    def change_demo_user(self, cid='NAACL2015'):
        demo_user = User.login("demo", "demo")
        
        regex = re.compile("([a-z])(\d+)")
        
        gs = regex.findall(demo_user.token)
        
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
        
        demo_user.token = '['+','.join(new_tokens)+']' 
        demo_user.save()
        
        self.remove_sumamry(cid)
                
if __name__ == '__main__':
    
    import ConfigParser
    import sys
    
    course = sys.argv[1]
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/config_'+course+'.cfg')
    
    cid = config.get('course', 'cid')
    course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY')
                                        )
    
    #course_mirror_server.test()
    
    #course_mirror_server.upload_summary('CS1635', [1])
    course_mirror_server.run(cid, summarylastlecture=config.getint('course', 'summarylastlecture'))
    
    #course_mirror_server.print_data(IE312TokenName, cid=None)
    
    #course_mirror_server.change_demo_user()
    
    
    