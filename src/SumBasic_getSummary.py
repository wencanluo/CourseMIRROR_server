import sys
import re
import fio
from collections import defaultdict
#from Survey import *
import random
import NLTKWrapper
import os
import SumBasic_sentence as SumBasic
            
def getShallowSummary(phrasedir, datadir, cid, sheets, types, K):
    #K is the number of words per summary
    for sheet in sheets:
        
        for type in types:
            responses_filename = os.path.join(phrasedir, str(sheet), '%s.syntax.key'%(type))
            
            student_summaryList = fio.LoadList(responses_filename)
            
            path = os.path.join(datadir, str(sheet))
            fio.NewPath(path)
            filename = os.path.join(path, type + '.txt')
            
            fio.SaveList(student_summaryList, filename)
            
            #run the SumBasic
            distribution, clean_sentences, processed_sentences = SumBasic.get_sentences(filename)
            summary = SumBasic.summarize(distribution, clean_sentences, processed_sentences, K)
            
            filename = os.path.join(path, type + '.summary')
            fio.SaveList(summary, filename)
        
if __name__ == '__main__':
    for cid in [
                'Engineer',
                'IE256',
                'IE256_2016',
                'CS0445', 
                ]:
        
        import global_params
        from config import ConfigFile
        
        config = ConfigFile(config_file_name='config_%s.txt'%cid)
        sheets = global_params.lectures[cid]
        types=config.get_types()
        L = global_params.getLLP(cid)[0]
        
        phrasedir = "../data/"+cid+"/np/"
        datadir = "../data/"+cid+"/mead/SumBasic/"
        fio.DeleteFolder(datadir)
        
        getShallowSummary(phrasedir, datadir, cid, sheets, types, K=L)

    print 'done'
    