import sys
import re
import fio
import json
import NLTKWrapper

filters = ["?", "[blank]", 'n/a', 'blank',] #'none', "no", "nothing"

import datetime

RatingKey = {"slightly": 1, 
"somewhat": 2,
"moderately": 3, 
"mostly":4,
"completely":5
}

RateSplitTag = "||Rating: "

stopwordfilename = "../data/smart_common_words.txt"
stopwords = [line.lower().strip() for line in fio.ReadFile(stopwordfilename)]
punctuations = ['.', '?', '-', ',', '[', ']', '-', ';', '\'', '"', '+', '&', '!', '/', '>', '<', ')', '(', '#', '=']

stopwords = stopwords + punctuations

def getRatingkey(rate):
    key = rate.strip().lower()
    if key in RatingKey:
        return RatingKey[key]
    return -1

def NormalizeResponse(response):
    k = response.find(RateSplitTag)
    if k == -1:
        return response
    return response[:k]
            
def getStudentResponse(excelfile, cid, lecture_number, type):
    '''
    return a dictionary of the students' summary, with the student id as a key
    The value is a list with each sentence an entry
    '''
    f = open(excelfile)
    reflections = json.load(f)['results']
    f.close()
    
    tokenIndex = 'user'
    couseIndex = 'cid'
    lectureIndex = 'lecture_number'
    
    summaries = {}
    
    key = type
        
    for k, inst in enumerate(reflections):
        try:
            token = inst[tokenIndex].lower().strip()
            courseNow = inst[couseIndex].strip()
            lecture = inst[lectureIndex]
            
            if courseNow != cid: continue
            if lecture_number != lecture: continue
            
            if len(token) > 0:
                content = inst[key].strip()
                if content.lower() in filters: continue
                if len(content) > 0:   
                    content = NormalizeResponse(content)                 
                    summary = NLTKWrapper.splitSentence(content)
                    
                    summary = [s.strip() for s in summary]
                    
                    if token in summaries:
                        summaries[token] += summary
                    else:
                        summaries[token] = summary
            else:
                break
        except Exception as e:
            print e
            return summaries
    return summaries

def getStudentResponseList(excelfile, cid, lecture, type, withSource=False):
    student_summaries = getStudentResponse(excelfile, cid, lecture, type)
    student_summaryList = []
    
    for id, summaryList in student_summaries.items():
        for s in summaryList:
            student_summaryList.append((s,id))
            
    if withSource:
        return student_summaryList
    else:
        return [summary[0] for summary in student_summaryList]
    
def getStudentResponses4Senna(excelfile, datadir):
    sheets = range(1, maxWeek+1)
    
    for sheet in sheets:
        week = sheet

        for type in ['q1', 'q2', 'q3', 'q4']:
            student_summaryList = getStudentResponseList(excelfile, cid, week, type)
            if len(student_summaryList) == 0: continue
            
            filename = datadir + "senna." + str(week) + "." + type + ".input"
            
            fio.SaveList(student_summaryList, filename)
       
if __name__ == '__main__':
    cid = sys.argv[1]
    maxWeek = int(sys.argv[2])
    
    excelfile = "../data/CourseMirror/reflections.json"
    sennadir = "../data/"+cid+"/senna/"
    fio.NewPath(sennadir)
    getStudentResponses4Senna(excelfile, sennadir)
    