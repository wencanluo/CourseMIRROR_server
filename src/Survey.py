from OrigReader import prData
import sys
import re
import fio
import NLTKWrapper
import numpy as np
import math
import SennaParser
import json

filters = ["?", "[blank]", 'n/a', 'blank'] #a classifier to predict whether the student has problem
#filters = []
                        
def HasSummary(orig, header, summarykey):
    key = header[0]
    for k, inst in enumerate(orig._data):
        try:
            value = inst[key].lower().strip()
            if value == summarykey.lower():
                if len(inst[header[2]].strip()) > 0:
                    return True
        except Exception:
            return False
    return False

def getWeight(summary):
    summary = summary.strip()
    g = re.search('^\d+\).*\[(\d+)\]$', summary)
    if g != None:
        weight = g.group(1).strip()
        return int(weight)
    
    g = re.search('^.*\[(\d+)\]$', summary)
    if g != None:
        weight = g.group(1).strip()
        return int(weight)
    
    return 0

def NormalizedTASummary(summary):
    summary = summary.strip()
    g = re.search('^\d+\)(.*)\[\d+\]$', summary)
    if g != None:
        summary = g.group(1).strip()
    
    g = re.search('^(.*)\[\d+\]$', summary)
    if g != None:
        summary = g.group(1).strip()
    
    g = re.search('^\d+\)(.*)$', summary)
    if g != None:
        summary = g.group(1).strip()
    
    return summary.strip()

def NormalizeMeadSummary(summary):
    summary = summary.strip()
    g = re.search('^\[\d+\](.*)$', summary)
    if g != None:
        summary = g.group(1).strip()
    
    return summary.strip()

def getTASummary(orig, header, summarykey, type='POI', weight = False):
    '''
    Get TA's summary from the excel
    return a list of sentences
    '''
    if not HasSummary(orig, header, summarykey):
        return []
    
    if type=='POI':
        keyword = header[2]
    elif type=='MP':
        keyword = header[3]
    elif type=='LP':
        keyword = header[4]
    else:
        return []
    
    key = header[0]
    
    weights = []
    summary = []
    for k, inst in enumerate(orig._data):
        value = inst[key].lower().strip()
        if value == summarykey.lower():
            value = inst[keyword].strip()
            summaries = value.split("\n")
            for sum in summaries:
                w = getWeight(sum)
                summary.append(NormalizedTASummary(sum))
                weights.append(w)
    if weight:
        return summary, weights
    return summary

def getTitle(titlefile):
    """
    get the slide titles for one single lecture
    """
    lines = fio.ReadFile(titlefile)
        
    title = []
    
    for i in range(len(lines)):
        if i%3 == 1:
            line = lines[i].strip()
            if len(line) > 0:
                title.append(line)
    
    return title

def getTitles(titledir, sheets=range(0,25)):
    #get title of slides for each lecture, 
    # 0: week 1
    # 1: week 2
    # ...
    # 24: week 25
    titles = []
    for sheet in sheets:
        week = sheet + 1
        
        filename = titledir + str(week) + '.TXT'
        
        lines = fio.ReadFile(filename)
        
        title = []
        
        for i in range(len(lines)):
            if i%3 == 1:
                line = lines[i].strip()
                if len(line) > 0:
                    title.append(line)
        
        titles.append(title)
        
    return titles
    
def WriteTASummary(excelfile, datadir):
    reload(sys)
    sys.setdefaultencoding('utf8')
    
    summarykey = "Top Answers"
    header = ['ID', 'Gender', 'Point of Interest', 'Muddiest Point', 'Learning Point']
    sheets = range(0,12)
    types = ['POI', 'MP', 'LP']
    
    for sheet in sheets:
        week = sheet + 1
        path = datadir + str(week)+ '/'
        fio.NewPath(path)

        orig = prData(excelfile, sheet)
        for type in types:
            summary, weight = getTASummary(orig, header, summarykey, type, weight=True)
    
            #summary = ["ssssss " + str(w) + " " + s for s, w in zip(summary, weight)]
                             
            filename = path + type + '.ref.0'
            print filename
            
            #only save the first 3 points
            fio.SaveList(summary, filename)

def getStudentQuality(orig, header):
    '''
    return a dictionary of the students' summary, with the student id as a key
    The value is a list with each sentence an entry
    '''
    dict = {}
    
    key = "Muddiest Point Coding (0-3; a = \"I understood everything\")"
        
    for k, inst in enumerate(orig._data):
        try:
            value = inst['ID'].lower().strip()
            if value == 'top answers': continue
            
            if len(value) > 0:
                content = inst[key]
                dict[value] = content
            else:
                break
        except Exception:
            return dict
    return dict
           
def getStudentResponse(orig, header, summarykey=None, type='POI'):
    '''
    return a dictionary of the students' summary, with the student id as a key
    The value is a list with each sentence an entry
    '''
    summaries = {}
    
    if type=='POI':
        key = header[2]
    elif type=='MP':
        key = header[3]
    elif type=='LP':
        key = header[4]
    else:
        return None
        
    for k, inst in enumerate(orig._data):
        try:
            value = inst['ID'].lower().strip()
            if value == 'top answers': continue
            
            if len(value) > 0:
                content = inst[key].strip()
                if content.lower() in filters: continue
                #if len(content) > 0:
                
                #if content.lower() in filters: 
                #    content = ""
                
                if True:
                    summary = NLTKWrapper.splitSentence(content)
                    summaries[value] = summary
            else:
                break
        except Exception:
            return summaries
    return summaries

def NormalizationMP(content):
    empty_response = ["?", "[blank]", 'n/a', 'blank', '_', '__', '___', '_____', 'na']
    
    if content.lower() in empty_response:
        content = ""
        print "@",
    
    return content
    
def getMPQualityPoint(orig, filters=None):
    '''
    return a list of the students' muddiest point with scores
    '''
    summaries = []
    
    key = "Muddiest Point"
    pointkey = "Muddiest Point Coding (0-3; a = \"I understood everything\")"
    
    for k, inst in enumerate(orig._data):
        
        if pointkey not in inst:
            continue
            
        try:
            value = inst['ID'].lower().strip()
            if value == 'top answers': continue
            
            if filters != None:
                if value not in filters: continue
                
            if len(value) > 0:
                content = inst[key].strip()
                score = inst[pointkey]
                
                if score == 'a': score = 0.0
                
                content = NormalizationMP(content)
                
                summaries.append((content, score))
            else:
                break
        except Exception:
            return summaries
    
    return summaries

def getStudentResponseList(orig, header, summarykey, type='POI', withSource=False):
    student_summaries = getStudentResponse(orig, header, summarykey, type)
    student_summaryList = []
    
    for id, summaryList in student_summaries.items():
        for s in summaryList:
            student_summaryList.append((s,id))
            
    if withSource:
        return student_summaryList
    else:
        return [summary[0] for summary in student_summaryList]
                    
def getStudentSummaryNum(orig, header, summarykey, type='POI'):
    if type=='POI':
        key = header[2]
    elif type=='MP':
        key = header[3]
    elif type=='LP':
        key = header[4]
    else:
        return 0
    
    count = 0
    for k, inst in enumerate(orig._data):
        try:
            value = inst['ID'].lower().strip()
            if len(value) > 0:
                if len(inst[key].lower().strip()) > 0:
                    count = count + 1
            else:
                break
        except Exception:
            return 0
    return count-1

def getMaleNum(orig, header, summarykey):
    key = header[1]
    count = 0
    for k, inst in enumerate(orig._data):
        try:
            value = inst[key].lower().strip()
            if value == 'm':
                count = count + 1
        except Exception:
            return 0
    return count

def getStudentNum(orig, header, summarykey):
    key = header[0]
    count = 0
    for k, inst in enumerate(orig._data):
        try:
            value = inst[key].lower().strip()
            if len(value) > 0:
                count = count + 1
            else:
                break
        except Exception:
            return 0
    return count-1

def getValidStudentNum(student_summaryList):
    ids = []
    for _, id in student_summaryList:
        ids.append(id)
    return len(set(ids))

def getMeadSummary(datadir, type):
    #return a list of summaries, week by week. The summary for each week is also a list
    sheets = range(0,12)
    
    summaries = []
    
    for sheet in sheets:
        row = []
        week = sheet + 1
        row.append(week)
                    
        path = datadir + str(week)+ '/'
        filename = path + type + '.summary'
        
        if not fio.IsExist(filename): continue
        
        lines = fio.ReadFile(filename)
        summary = []
        for line in lines:
            summary.append(NormalizeMeadSummary(line))
        
        summaries.append(summary)
    
    return summaries
        
def getMeadSummaryList(datadir, type):
    #return a list of summaries, week by week. The summary for each week is also a list
    sheets = range(0,12)
    
    summaries = []
    for sheet in sheets:
        row = []
        week = sheet + 1
        row.append(week)
                    
        path = datadir + str(week)+ '/'
        filename = path + type + '.summary'
        
        lines = fio.ReadFile(filename)
        summary = []
        for line in lines:
            summary.append(NormalizeMeadSummary(line))
        
        summaries.append(summary)
    
    summaryList = []
    for summaries in summaries:
        for summary in summaries:
            summaryList.append(summary)
        
    return summaryList

def getStudentResponses4Senna(excelfile, datadir):
    header = ['ID', 'Gender', 'Point of Interest', 'Muddiest Point', 'Learning Point']
    summarykey = "Top Answers"
    
    #sheets = range(0,25)
    sheets = range(0,12)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        orig = prData(excelfile, sheet)
        
        for type in ['POI', 'MP', 'LP']:
            student_summaryList = getStudentResponseList(orig, header, summarykey, type)
            filename = datadir + "senna." + str(week) + "." + type + ".input"
            
            fio.SaveList(student_summaryList, filename)
            #student_summaryList = [summary[0] for summary in student_summaryList]
            #fio.SaveList(student_summaryList, filename)

def getStudentResponses4Maui(excelfile, datadir):
    header = ['ID', 'Gender', 'Point of Interest', 'Muddiest Point', 'Learning Point']
    summarykey = "Top Answers"
    
    #sheets = range(0,25)
    sheets = range(0,12)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        orig = prData(excelfile, sheet)
        
        for type in ['POI', 'MP', 'LP']:
            student_summaryList = getStudentResponseList(orig, header, summarykey, type)
            filename = datadir + "" + str(week) + "." + type + ".txt"
            fio.SaveList(student_summaryList, filename, ".\n")

def getCandidatePhrases(dir):
    sheets = range(0,12)
    
    numbers = []
    
    length = []
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        filename = dir + str(week) + ".txt"
        
        phrases = fio.ReadFile(filename)
        #print len(phrases)
        numbers.append(len(phrases))
        for phrase in phrases:
            n = len(phrase.split())
            if n>10:
                print phrase
            length.append(len(phrase.split()))
    
    #fio.PrintList(numbers, "\n")
    fio.PrintList(length, ",")

def getLength(NPs):
    N = 0.0
    for NP in NPs:
        N = N + len(NP.split())
    return N / len(NPs)
    
def Excel2Json(excelfile, jsonfile):
    header = ['ID', 'Gender', 'Point of Interest', 'Muddiest Point', 'Learning Point']
    summarykey = "Top Answers"
    
    #sheets = range(0,25)
    sheets = range(0,12)
    
    data = {}
    data['Questions'] = {'POI':'Describe what you found most interesting in today\'s class.',
                         'MP':'Describe what was confusing or needed more detail.',
                         'LP':'Describe what you learned about how you learn.',
                         }
    data['Lectures'] = []
    
    index = 1
    IDIndex = {}
        
    for i, sheet in enumerate(sheets):
        dict = {}
        
        week = i + 1
        orig = prData(excelfile, sheet)
        
        dict['lecture_number'] = week
            
        summarydict = {}
        responsedict = {}
        
        for type in ['POI', 'MP', 'LP']:
            #student_summaryList = getStudentResponseList(orig, header, summarykey, type)
            responses = getStudentResponse(orig, header, summarykey, type)
            for id, response in responses.items():
                if id not in IDIndex:
                    sid = 'S' + str(index)
                    IDIndex[id] = sid
                    index = index + 1
                else:
                    sid = IDIndex[id]
                    
                if sid not in responsedict:
                    responsedict[sid] = {}
                assert(type not in responsedict[sid])
                responsedict[sid][type] = response
            
            if HasSummary(orig, header, summarykey):
                ta_summaries, weight = getTASummary(orig, header, summarykey, type, weight=True)
                
                summary = []
                for w, s in zip(weight, ta_summaries):
                    if w==0:
                        summary.append(s)
                    else:
                        summary.append(s + ' [' + str(w) + ']')
                summarydict[type] = summary
        
        dict['Student_Responses'] = responsedict
        
        dict['TA_summary'] = summarydict
        
        data['Lectures'].append(dict)
    
    with open(jsonfile, 'w') as outfile:
        json.dump(data, outfile, indent=2)
    
    fio.SaveDict(IDIndex, "../data/students.txt")
                                         
if __name__ == '__main__':
    
    excelfile = "../data/2011Spring.xls"
    #datadir = "../../Maui1.2/data/2011Spring/"
    sennadir = "../data/senna/"
    fio.NewPath(sennadir)
    
    #Excel2Json("../data/anotated_corpus_phrase_summarization.xls", "../data/data.json")
    #fio.newPath(datadir)
    #getStudentResponses4Maui(excelfile, datadir)
    
    getStudentResponses4Senna(excelfile, sennadir)
    
    #getCandidatePhrases("../data/phrases/")
    
    #getNumberofCandiatePhrase(excelfile, "../data/phrases/")