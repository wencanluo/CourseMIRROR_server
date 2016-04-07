from datetime import datetime
from pytz import timezone
import CourseMIRROR
from time import gmtime, strftime
import time
import pytz
from tables import *
import os

pacific_zone = timezone('US/Pacific')
eastern_zone = timezone('US/Eastern')

DATE_FORMAT = "%m/%d/%Y"
DATE_FORMAT_AVAILABLE = "%B %m, %Y"
DATE_FORMAT_FILE = "%d-%m-%Y"

if __name__ == '__main__':
    import ConfigParser
    
    config = ConfigParser.RawConfigParser()
    config.read('../config/myconfig.cfg')
    
    course_mirror_server = CourseMIRROR.CourseMIRROR(config.get('Parse', 'PARSE_APP_ID'), 
                                        config.get('Parse', 'PARSE_REST_API_KEY'), 
                                        config.get('Parse', 'PARSE_MASTER_KEY'),
                                        config,
                                        )
    courses = {'CS0445':{3:17,
                         7:17},
               'CS1635':{3:17,
                         7:17},
               'IE256_2016':{3:10,
                        7:10},
                }
    
    while True:
        #get the current time
        ts = time.time()
        utc_now = datetime.utcfromtimestamp(ts)
        t = utc_now.replace(tzinfo=pytz.utc).astimezone(eastern_zone)
        print(t)
        
        weekday = t.isoweekday()
        hour = t.hour
        
        print weekday, hour
        for cid in courses:
            if weekday in courses[cid]:
                if hour >= courses[cid][weekday]:
                    print "time now for %s" %cid
             
                    #get the deadline
                    max_lecture = course_mirror_server.get_max_lecture_num(cid)
                    print(max_lecture)
                    
                    #run the summarization algorithm
                    #whether there is a summary
                    
                    try:
                        query = Summarization.Query.filter(cid=cid, lecture_number=max_lecture)
                        if len(query) == 0:
                            os.system('python CourseMIRROR.py %s'%cid)
                            time.sleep(600)
                        
                    except Exception as e:
                        pass
                    
                    print 'done'
        
        print('it will run in 5mins later')
        time.sleep(600)
            