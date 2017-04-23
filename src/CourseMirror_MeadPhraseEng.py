import sys
import re
import fio
import xml.etree.ElementTree as ET

import phraseClusteringKmedoid
import SennaParser
import CourseMirror_Survey
import os,cmd,subprocess

def WriteDocsent(excelfile, folder, sennadatadir, np=None):
    sheets = range(0,maxWeek)
    
    for i, sheet in enumerate(sheets):
        week = i + 1
        
        for type in ['q1', 'q2', 'q3', 'q4']:
            student_summaryList = CourseMirror_Survey.getStudentResponseList(excelfile, course, week, type, withSource=True)
            if len(student_summaryList) == 0: 
                print week, type
                continue
            
            ids = [summary[1] for summary in student_summaryList]
            summaries = [summary[0] for summary in student_summaryList] 
                            
            sennafile = sennadatadir + "senna." + str(week) + "." + type + '.output'
            if not fio.IsExist(sennafile): 
                print sennafile
                continue
            
            sentences = SennaParser.SennaParse(sennafile)
            
            DID = str(week) + '_' + type
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            path = path + type + '/'
            fio.NewPath(path)
            path = path + 'docsent/'
            fio.NewPath(path)
            filename = path + DID + '.docsent'
            
            #create a XML file
            root = ET.Element(tag='DOCSENT', attrib = {'DID':DID, 'LANG':"ENG"})
            root.tail = '\n'
            tree = ET.ElementTree(root)
            
            if np.startswith("candidate"):
                summariesList = summaries
            else:
                summariesList = sentences
            
            sno_id = 1
            for par, s in enumerate(summariesList):
                if np=='syntax':
                    NPs = s.getSyntaxNP()
                    NPs = phraseClusteringKmedoid.MalformedNPFlilter(NPs)
                elif np == 'chunk':
                    NPs = s.getNPrases()
                    NPs = phraseClusteringKmedoid.MalformedNPFlilter(NPs)
                elif np == 'sentence':
                    NPs = s.getSentence()
                else:
                    print "wrong"
                    exit()
                    
                for RSNT, value in enumerate(NPs):
                    node = ET.Element(tag='S', attrib={'PAR':str(par+1), 'RSNT':str(RSNT+1), 'SNO':str(sno_id)})
                    node.text = value
                    node.tail = '\n'
                    root.append(node)
                    sno_id = sno_id + 1
            
            tree.write(filename)
            
def WriteCluster(excelfile, folder, np=None):
    sheets = range(0,maxWeek)
    
    for type in ['q1', 'q2', 'q3', 'q4']:
        for sheet in sheets:
            week = sheet + 1
            student_summaryList = CourseMirror_Survey.getStudentResponseList(excelfile, course, week, type, withSource=True)
            if len(student_summaryList) == 0: continue
            
            path = folder + str(week)+ '/'
            fio.NewPath(path)
            
            path = path + type + '/'
            fio.NewPath(path)
            filename = path + type + '.cluster'
            
            #create a XML file
            root = ET.Element(tag='CLUSTER', attrib = {'LANG':"ENG"})
            root.tail = '\n'
            tree = ET.ElementTree(root)
        
            DID = str(sheet+1) + '_' + type
            
            node = ET.Element(tag='D', attrib={'DID':str(DID)})
            node.tail = '\n'
            root.append(node)
        
            tree.write(filename)
            
def Write2Mead(excelfile, datadir, sennadatadir, np=None):
    #assume one week is a one document
    WriteDocsent(excelfile, datadir, sennadatadir, np)
    WriteCluster(excelfile, datadir)
                
if __name__ == '__main__':
    
    course = 'Engineer'
    maxWeek = 12

    sennadir = "../data/"+course+"/senna/"
    reflections = "../data/CourseMIRROR/reflections.json"
    
    phrasedir = "../data/"+course+"/np/"
    
    #maridir = '../../Maui1.2/data/'
    #maridir_datadir = os.path.join(maridir, course)
    #fio.NewPath(maridir_datadir)
    #CourseMirror_Survey.getStudentResponses4Mari(reflections, course, maxWeek, maridir_datadir)
    #exit(-1)
    
#     for np in ['syntax']:
#         datadir = "../data/"+course+ '/mead/' + "PhraseMead/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#     
#     exit(-1)
#     
#    
#     for np in ['sentence']:
#         datadir = "../data/"+course+ '/mead/' + "OriMead/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#     
#     for np in ['syntax']:
#         datadir = "../data/"+course+ '/mead/' + "Mead/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#     
#     for np in ['syntax']:
#         datadir = "../data/"+course+ '/mead/' + "MeadMMR/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#     
#     for np in ['syntax']:
#         datadir = "../data/"+course+ '/mead/' + "LexRank/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#     
#     for np in ['syntax']:
#         datadir = "../data/"+course+ '/mead/' + "LexRankMMR/"
#         fio.DeleteFolder(datadir)
#         Write2Mead(reflections, datadir, sennadir, np=np)
#      
    #Step5: get PhraseMead output
    #     . get PhraseMead output
    meaddir = '../../mead/bin/'
    cmd = './get_phrasemead_all_eng.sh ' + str(course) + ' ' +  str(maxWeek)
    os.chdir(meaddir)
    retcode = subprocess.call([cmd], shell=True)
    print retcode
    
    print "done"