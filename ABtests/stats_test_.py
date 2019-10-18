import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import scipy.stats as scipy
import numpy as np
#import pymc3 as pm
from scipy.stats import beta




class stats_tests(object):
    """
    This class contains a number of objects for conduction statistical tests
    
    For each test, you will need to enter a pandas dataframe into the object, as specified by df. 

    
    """

    def __init__(self, config):
        """
        Class initiation.
        
        Pull key variables from the config file [config.py]
        """

        # Location-specific attributes:
        self.component_A = config.config_dataset['A']
        self.component_B = config.config_dataset['B']        
        self.metric_headers = config.config_dataset['metric_headers']
        self.vol_header = config.config_dataset['vol_header']
        self.suffixes = config.config_dataset['suffixes']
        self.prior_sales_rates = config.config_dataset['prior_sales_rates']
        self.component_header = config.config_dataset['component_header']
        
    def summate(self,df,component):
        """
        This function sums response across all products to return a holisitic vue of the campaing performance.
        The resulting dataframe is then appended to the existing data set
        """

        df_sum = {}

        summation = df.sum()
        headers = list(df.columns)

        summation[0] = 'ALL {}'.format(component)
        summation[8] = '{}'.format(component)
        summation[9] = 'All products'

        for i in range(len(headers)):
            df_sum[headers[i]] = summation[i]

        return df_sum    
    
    def stats_calc(self,df,suffix,response_metric,volume):
        '''
        This function quickly calcualtes a engagement response rate and its error

        INPUT:
        df - dataframe, new columns will be appended here
        suffix - A strong value denoting the metric suffix
        response_metric - column headers of the response to analysed
        volume - volume header

        OUTPUT:
        df - the dataframe with appended columns
        '''

        df['{}RR'.format(suffix)] = df[response_metric]/df[volume]
        df['err{}RR'.format(suffix)] = np.sqrt((df['{}RR'.format(suffix)]*((1-df['{}RR'.format(suffix)])/df[volume])))

        return df
    
    def posterior_calc(slef,S_0,N_0,S_i,N_i):
        '''
        This fucntion calculates the posterior probability of S_i sales from N_i trials, 
        given a prior probability of S_0 sales from N_0 trials

        Inputs
        ======
        S_0 - prior sales
        N_0 - prior volume
        N_i - test volume for a given interval
        S_i - test sales for a given interval

        Outputs
        =======
        posterior pdf
        '''
        # Calculate a (success) and b (failures)
        a_0 = S_0
        b_0 = N_0-S_0
        a_i = S_i
        b_i = N_i-S_i 

        #print("a_0 = {} b_0 = {}".format(a_0,b_0))
        #print("a_i = {} b_i = {}".format(a_i,b_i))    
        #Calculate and return the posterior (prior + present dat) pdf
        return beta(a_0 + a_i,b_0 + b_i)        
        
                
    def prep_data(self, df,test_component):
        """
        Prepares the data for and runs a stats for a test
        
        input:
        
        df = data frame [EXTERNAL INPUT]
        test_component = string [FROM CONFIG]
        
        Output:
        df_test = prepared dataset for a given test with key stats as additional columns
        
        """
        
        #CLEANING AND RESPONSE RATE CALCULATIONS
        df.fillna(0,inplace=True)

        #Split segment strings
        df['test_component'], df['product'] = df['segment'].str.split(' ', 1).str
        #SPLIT DATAFRAME INTO TEST GROUPS
        df_test = df.loc[(df['test_component']==test_component)]
        #Summate all sales per batch        
        summed_vals = self.summate(df_test,test_component)
        df_test = df_test.append(summed_vals, ignore_index=True)
        #Loop across metrics and complete calculations where possible
        for i in range(len(self.metric_headers)):  
            try: 
                df_test = self.stats_calc(df_test,self.suffixes[i],self.metric_headers[i],self.vol_header)
            except:
                print('WARNING | {} missing'.format(self.suffixes[i]))
                pass
        
        return df_test
     

    def run_uplift_calculator(self,df):
        """
           
        """
        #Caculate key stats
        df_A = self.prep_data(df,self.component_A)
        df_B = self.prep_data(df,self.component_B)    
        #Join datasets together
        df_AB = df_B.merge(df_A,how='inner',left_on=['product'],right_on=['product'],suffixes=('_B','_A'))
        #Calculate Z_test stats
        for i in range(len(self.suffixes)):      
            try: 
                df_AB = self.z_test_calculator(df_AB,'{}_B'.format(self.vol_header),
                                                '{}RR_B'.format(self.suffixes[i]),
                                                '{}RR_A'.format(self.suffixes[i]),
                                                'err{}RR_B'.format(self.suffixes[i]),
                                                'err{}RR_A'.format(self.suffixes[i]),
                                                 self.suffixes[i])                                                            
                df_AB.replace(np.inf,0,inplace=True)    
                df_AB['combined volume'] = df_AB['{}_A'.format(self.vol_header)]+df_AB['{}_B'.format(self.vol_header)]                          
                df_AB['{}_A scaled'.format(self.suffixes[i])] = df_AB['{}RR_A'.format(self.suffixes[i])]*df_AB['combined volume']
                df_AB['{}_B scaled'.format(self.suffixes[i])] = df_AB['{}RR_B'.format(self.suffixes[i])]*df_AB['combined volume']
                df_AB['{}_B_v_uplift'.format(self.suffixes[i])] = df_AB['{}_B scaled'.format(self.suffixes[i])]-df_AB['{}_A scaled'.format(self.suffixes[i])]
                df_AB['{}_B_uplift'.format(self.suffixes[i])] = df_AB['{}_B_v_uplift'.format(self.suffixes[i])]/df_AB['{}_A scaled'.format(self.suffixes[i])]                                          
                                          
            except:
                print('ERROR | no scores calculated for {}'.format(self.metric_headers[i]))                       
            pass
        df_AB.replace(np.inf,'NAN',inplace=True)
        return df_AB
   
    def z_test_calculator(self,df,volume_B,B,A,errB,errA,suffix):
        '''
        This is a function for a significane calculator for an AB test.
        This will take a response metric for and A and B sample and tell you if there is a significant

        INPUTS:

        df - data frame containing the A,B metrics, the A,B errors and A volume
        volume_A - a column header for the volume of the A sample
        A - a column header for the A response metric
        B - a column header for the B response metric
        errA - a column header for the A error response metric
        errB - a column header for the A error response metric
        suffix - a suitable string to describe what response metric you are analysing

        OUTPUTS:

        df['{}_uplift'] - uplift as a number of percentage points
        df['{}_r_uplift'] - uplift as a relative fraction of the control (B)
        df['{}_v_uplift'] - absolute volume of uplift
        df['{}_z-score'] - z-score
        df['{}_p-score'] - p-score as a percentage. Anything above 95 is considered significant result (2sigma). Anything above 68 could be indicative (1 sigma). We are not doing astrophysics here lol!
        '''

        df['{}_uplift'.format(suffix)] = df[B]-df[A]
        df['{}_r_uplift'.format(suffix)] = ((df[B]-df[A])/df[A])
        df['{}_v_uplift'.format(suffix)] = df['{}_uplift'.format(suffix)]*df[volume_B].round(0)
        df['{}_z-score'.format(suffix)] = (df[B]-df[A])/np.sqrt(np.power(df[errB],2)+np.power(df[errA],2))
        df['{}_p-score'.format(suffix)] = ((1.-scipy.norm.sf(abs(df['{}_z-score'.format(suffix)])))*100.).round(0)

        return df

    def bayesian_test(self,df,product):
        '''
        This is an object for calculating the bayesian probability that B will beat A in an A/B test.
        
        Call this object if you are trying to calculate the Bayesian proba for a single product/use case.
        
        pre-requisites:
        component_header - a header stored in the config file
        component_A - a string label from the component_header feature for test case A
        component_B - a string label from the component_header feature for test case B
        
        Input:
        df_TS - IMPORTANT this is a time series dataframe. It is NOT the same structure that is used for the frquentist method. 
                A typical schema should look like this...
                Index([u'email_date', u'segment_cut', u'vol_all', u'vol_live', u'vol_cntrl', u'vol_motor', u'vol_home', u'vol_life', 
                u'vol_pmi', u'vol_cic', u'vol_travel', u's_motor', u's_home', u's_life', u's_pmi', u's_cic', u's_travel', u's_all', 
                u'cntrl_s_motor', u'cntrl_s_home', u'cntrl_s_life', u'cntrl_s_pmi', u'cntrl_s_cic', u'cntrl_s_travel'], dtype='object')
        product - strong value. Must be consistent with the schema above. 
        
        output:
        proba - float value for probability that B will beat A
        '''
        df_A = df.loc[df[self.component_header]==self.component_A]
        df_B = df.loc[df[self.component_header]==self.component_B]
        
        samples = 20000
        prior_sale_factor = 2.  
        
        #changed prior_)sales to prior_vol check if needed
        prior_vol = round(prior_sale_factor*(1/self.prior_sales_rates[product]),0)

        S_A_0,S_B_0 = prior_sale_factor,prior_sale_factor
        N_A_0,N_B_0 = prior_vol,prior_vol

        N_A,N_B,S_A,S_B = 0,0,0,0
        
        i = 0
        
        for i in range(len(df_A)):
            df_A_i = df_A.iloc[i]
            df_B_i = df_B.iloc[i]
           
            #Compute for A
            S_A_i = df_A_i['s_{}'.format(product)]
            N_A_i = df_A_i['vol_{}'.format(product)]   
            post_A = self.posterior_calc(S_A_0,N_A_0,S_A_i,N_A_i)
            #Compute for B
            S_B_i = df_B_i['s_{}'.format(product)]
            N_B_i = df_B_i['vol_{}'.format(product)]   
            post_B = self.posterior_calc(S_B_0,N_B_0,S_B_i,N_B_i)    

            #Scale priors      
            N_A_0 = N_A_0+N_A_i
            N_B_0 = N_B_0+N_B_i
            S_A_0 = S_A_0+S_A_i
            S_B_0 = S_B_0+S_B_i   
            N_A = N_A+N_A_i
            S_A = S_A+S_A_i
            N_B = N_B+N_B_i
            S_B = S_B+S_B_i  

        items = (post_A.rvs(samples) < post_B.rvs(samples))
        
        proba = np.mean(list(map(lambda x: float(x),items)))
        
        return proba
    
    def run_bayesian_test(self,df_TS):
        '''
        This is the wrapper for bayesian test. Call this script to calculate Bayesian A/B for multiple products
        
        pre-requisites:
        prior_sales_rates - listed in the config file. 
                              This is a dictionary that contains a prior sales rate for given product. 
                              It acts not only as the basis for the prior but also the products to cycle over
                              
        Inputs:
        df_TS - IMPORTANT this is a time series dataframe. It is NOT the same structure that is used for the frquentist method. 
                A typical schema should look like this...
                Index([u'email_date', u'segment_cut', u'vol_all', u'vol_live', u'vol_cntrl', u'vol_motor', u'vol_home', u'vol_life', 
                u'vol_pmi', u'vol_cic', u'vol_travel', u's_motor', u's_home', u's_life', u's_pmi', u's_cic', u's_travel', u's_all', 
                u'cntrl_s_motor', u'cntrl_s_home', u'cntrl_s_life', u'cntrl_s_pmi', u'cntrl_s_cic', u'cntrl_s_travel'], dtype='object')
                
        Output:
        df_out - a simple dateframe containing the results.
        
        '''
        product_list = self.prior_sales_rates.keys()
        
        proba_list = [] 
        dataframe_dict = {}
        
        for i in product_list:
            try:
                print 'Running test for product ',i
                proba = self.bayesian_test(df_TS,i)
                print 'Proba B will be beat A = ',proba
                proba_list.append(proba)
            except:
                print('failure - check product name')
                proba_list.append(0)
        
        dataframe_dict['product'] = product_list
        dataframe_dict['proba_B_over_A'] = proba_list
        
        df_out = pd.DataFrame(dataframe_dict)
        
        return df_out
        
        
        
        
        
        
        
        
       