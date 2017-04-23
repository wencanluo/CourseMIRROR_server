#https://github.com/dgrtwo/ParsePy
import os
os.environ["PARSE_API_ROOT"] = "https://coursemirror.azurewebsites.net/parse"

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

import gmail
import CourseMirror_Survey
TypeMap = {"q1":'q1_summaries', "q2":'q2_summaries', "q3":'q3_summaries', "q4":'q4_summaries'}
NameMap = {"q1":'Point of Interest', "q2":'Muddiest Point', "q3":'Learning Point'}
TypeMapReverse = {"q1_summaries":'Point of Interest', "q2_summaries":'Muddiest Point', "q3_summaries":'Learning Point'}

from parse_rest.user import User

class CourseMIRROR:
    def __init__(self, app_id, api_key, master_key, config=None):
        
        register(app_id, api_key)
        
        self.old_N = 0
        self.config = config
        self.email_from = 'wencanluo.cn@gmail.com'
    
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
    
    def get_max_lecture_num_from_relection(self, cid, reflections):
        max_lec = None
        couseIndex = 'cid'
        lectureIndex = 'lecture_number'
        for k, inst in enumerate(reflections['results']):
            try:
                courseNow = inst[couseIndex].strip()
                lecture = inst[lectureIndex]
                
                if courseNow != cid: continue
                
                max_lec = lecture if max_lec == None else max(max_lec, lecture)
                
            except Exception as e:
                print e
        
        return max_lec
    
    def remove_sumamry(self, cid):
        max_lecture = self.get_max_lecture_num(cid)
        
        try:
            summary_Object = Summarization.Query.get(cid=cid, lecture_number = max_lecture, method='ClusterARank')
            summary_Object.delete()
        except parse_rest.query.QueryResourceDoesNotExist:
            pass
    
    def getDate(self, lectures, cid, lecture):
        for dict in lectures['results']:
            if dict['cid'] != cid: continue
            if dict['number'] == lecture:
                return dict['date']
        
        return ""
    
    def upload_summary(self, cid, lectures=None):
        #only sumbit the last summary
        lectures_json = fio.LoadDictJson('../data/CourseMIRROR/lectures.json')
        response_json = fio.LoadDictJson('../data/CourseMIRROR/reflections.json')
        questions = ['q1', 'q2']
        
        max_lecture = self.get_max_lecture_num_from_relection(cid, response_json)
        
        if max_lecture == None: return
        
        if lectures:
            sheets = lectures
            
        for i in sheets:
            print sheets
            
            lecture = i + 1
            
            try:
                email_to = config.get('email', 'to')
                
                email_tos = [email_address.strip() for email_address in email_to.split(',')]
                
                lecture_date = self.getDate(lectures_json, cid, lecture)
                
                content = []
                subject = 'Responses for Lecture %s in %s'%(lecture_date, cid)
                
                #get responses
                for q in questions:
                    if q not in NameMap: continue
                    
                    stu_responses = CourseMirror_Survey.getStudentResponseFromJson(response_json, cid, lecture, q)
                    
                    responses = []
                    
                    if len(stu_responses) > 0:
                        responses.append('Responses for %s:'%NameMap[q])
                        rid = 1
                        for response in stu_responses.values():
                            responses.append('%d\t%s'%(rid, ' '.join(response)))
                            rid += 1
#                             for ss in response:
#                                 responses.append('%d\t%s'%(rid, ss))
#                                 rid += 1
                        responses.append('')
                        content += responses
                
                content = '\n'.join(content)
                
                gmail.send_email(subject, self.email_from, email_tos, content)
                
                print subject, self.email_from, email_tos, content
                
            except Exception as e:
                print e
                continue
            
    def run(self, cid, summarylastlecture=False):
        
        jsonfile = '../data/CourseMIRROR/reflections.json'
        
        #get reflections
        reflections = self.get_reflections(cid=None)
        with open(jsonfile, 'w') as outfile:
            json.dump(reflections, outfile, encoding='utf-8', indent=2)
         
        reflections = fio.LoadDictJson(jsonfile)
        
        max_lecture = self.get_max_lecture_num_from_relection(cid, reflections)
        if max_lecture == None: return
        print "max_lecture", max_lecture
        
        #get lectures
        lectures = self.get_lectures(cid=None)
        jsonfile = '../data/CourseMIRROR/lectures.json' 
        with open(jsonfile, 'w') as outfile:
            json.dump(lectures, outfile, encoding='utf-8', indent=2)
        
        self.N = len(reflections['results'])
        print "total number of reflections:", self.N
         
        if self.N == self.old_N: #no need to summary
            return
         
        self.old_N = self.N
        
        lectures=range(max_lecture-1, max_lecture)
        
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
    
    course = 'Programmieren 1_2'
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/config_'+course+'.cfg')
    
    cid = config.get('course', 'cid')
    course_mirror_server = CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY'),
                                        config
                                        )
    
    #course_mirror_server.upload_summary(cid, lectures=[1])
    
    course_mirror_server.run(cid, summarylastlecture=config.getint('course', 'summarylastlecture'))
    
   
    
    