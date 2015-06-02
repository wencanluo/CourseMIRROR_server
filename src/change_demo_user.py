from CourseMIRROR import *
import os
                
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
    while True:
        ch = raw_input("press any key to change the token for the current demo user")
        
        try:
            course_mirror_server.change_demo_user()
        except Exception as e:
            print e
    
    