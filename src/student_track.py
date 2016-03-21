from CourseMirror_Survey import *
from collections import defaultdict
import fio
import codecs

def RankStudents(excelfile, cid, output):
    f = open(excelfile)
    reflections = json.load(f)['results']
    f.close()
    
    tokenIndex = 'user'
    couseIndex = 'cid'
    
    total_count = 0
    
    dict = defaultdict(int)
    for k, inst in enumerate(reflections):
        try:
            token = inst[tokenIndex].lower().strip()
            courseNow = inst[couseIndex].strip()
            
            if courseNow != cid: continue
            
            dict[token] += 1
            total_count += 1
            
        except Exception as e:
            print e
    
    fio.SaveDict2Json(dict, output+'.rank')
    
    keys = sorted(dict, key=dict.get, reverse = True)
    
    named = {}
    for i, key in enumerate(keys):
        named[key] = i+1
    
    fio.SaveDict2Json(named, output)
    
    print total_count

def find_name(token, users):
    for user in users:
        if user['token'] == token:
            return user['name']
    
    return 'None'
    
def RankStudentbyName(excelfile, nameids, cid, output):
    f = open(excelfile)
    reflections = json.load(f)['results']
    f.close()
    
    tokenIndex = 'user'
    couseIndex = 'cid'
    
    total_count = 0
    
    dict = defaultdict(int)
    for k, inst in enumerate(reflections):
        try:
            token = inst[tokenIndex].lower().strip()
            courseNow = inst[couseIndex].strip()
            
            if courseNow != cid: continue
            
            dict[token] += 1
            total_count += 1
            
        except Exception as e:
            print e
    
    name_dict = {}
    
    name_ids = fio.LoadDictJson(nameids)['results']

    sys.stdout = codecs.open(output, 'w', 'utf-8')
    for token, count in dict.items():
        #find the name
        name = find_name(token, name_ids)
        name_dict[name] = count
        print name, '\t', count  
    
    
def getStudentResponses4Summary(excelfile, ranked, cid, maxWeek, datadir):
    rank = fio.LoadDictJson(ranked)
    
    sheets = range(1, maxWeek+1)
    
    for i, sheet in enumerate(sheets):
        lecture = sheet
        
        for type in ['q1', 'q2']:
            head = ['student_id', 'responses']
            body = []
        
            student_summaries = getStudentResponse(excelfile, cid, lecture, type)
            student_summaryList = []
            
            for id, summaryList in student_summaries.items():
                summary = ' '.join(summaryList)
                if len(summary) == 0: continue
                student_summaryList.append((id, summary))
            
            filename = datadir + "response." + str(lecture) + "." + type + ".txt"
            print filename
            
            for id,summary in student_summaryList:
                row = []
                summary = summary.replace('"', '\'')
                if len(summary.strip()) == 0: continue
                
                if id in rank:
                    ranked_id = rank[id]
                else:
                    #produce a new id for the student
                    sorted_ids = sorted(rank.values())
                    ranked_id = sorted_ids[-1] + 1
                    rank[id] = ranked_id
                    print ranked_id
                    
                row.append(ranked_id)
                
                row.append(summary)
                body.append(row)
            
            #rank body
            
            body = sorted(body, key=lambda x : x[0])
            fio.WriteMatrix(filename, body, head)
    
    fio.SaveDict2Json(rank, ranked)
    
if __name__ == '__main__':
    excelfile = "../data/CourseMirror/reflections.json"
    
    ranked = "../data/CourseMirror/rank2.json"
    nameids = "../data/CourseMirror/IE312TokenName.json"
    RankStudentbyName(excelfile, nameids, 'IE312', ranked)
    
    cid = sys.argv[1]
    maxWeek = int(sys.argv[2])
     
#     cid = "IE312"
#     maxWeek = 26
#     
    datadir = "../data/IE312/response/"
    fio.NewPath(datadir)
    getStudentResponses4Summary(excelfile, ranked, cid, maxWeek, datadir)