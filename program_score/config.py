class config(object):
    


    def __init__(self):
        '''
        THESE ARE THE CLUSTER WEIGHTINGS FOR THE PROGRAM SCORE [PART OF ATC]      
        '''
        
        weightings = {
                      'Grace':0,
                      'Broadcast':0,
                      'Unsubscribe':0,
                      'MyAviva Engagement':0,
                      'Registrations':0,              
                      'Passive Customer Sales':0,    
                      'Engaged Customer Sales':0,    
                      'Prospect Sales':0
                    }
        
        self.config_dataset = {
            'weightings':weightings
             }