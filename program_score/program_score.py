import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import scipy.stats as scipy
import numpy as np
#import pymc3 as pm
from scipy.stats import beta


class program_score_prep(object):
    """
    This class contains a number of objects to carry out calculations around campaign metrics and also the cluster labels weighting
    """

    def __init__(self, config):
        """
        Class initiation.
        
        Pull key variables from the config file [config.py]
        """

        # Location-specific attributes:
        self.weightings = config.config_dataset['weightings']

        
    def calculate_program_score_from_weights(self,df):
        """
        In this preperation object weights (see config file) are asigned to the campaign clusters
        These are then summed with the normalised ACE score to create the program score
        There are a number of other minor clean steps
        
        input: program level dateframe
        output: program level dateframe
        
        """

        df['cluster_labels'].fillna('Grace',inplace=True)     
        df['ace_score'].fillna(0,inplace=True)
        df['norm_ace_score'].fillna(0,inplace=True)
        df['at_score'].fillna(0,inplace=True)
        df['cluster_weighting'] = df['cluster_labels'].map(self.weightings) 
        df['program_score'] = df['cluster_weighting']+df['norm_ace_score']

        return df         
    
    def calculate_campaign_metrics(self,df):
        """
        In this preperation object we generate and clean a varity of campaign metrics and features
        
        input: program level dateframe
        output: program level dateframe
      
        """
        
        #Remove campaigns for which we don't have a keycode
        df.dropna(subset=['keycode'],inplace=True)
        
        #Calculate Campaign metrics
        df['OpenRR'] = round((df['open_volume']/df['total_sends'])*100.,2)
        df['multiprodRR'] = round((df['total_MHP_sales']/df['total_sends'])*100.,2)
        df['ClickRR'] = round((df['click_volume']/df['total_sends'])*100.,2)
        df['PositiveRR'] = round((df['total_positive_engagements']/df['total_sends'])*100.,2)
        df['NegativeRR'] = round((df['unsub_volume']/df['total_sends'])*100.,2)
        df['QuoteRR'] = round((df['total_quotes_4wk']/df['total_sends'])*100.,2)
        df['logonRR'] = round((df['logon_volume']/df['total_sends'])*100.,2)
        df['RegisterRR'] = round((df['register_volume']/df['total_sends'])*100.,2)
        df['SalesRR'] = round((df['total_sales_4wk']/df['total_sends'])*100.,2)
        df['C2QR'] = round((df['total_quotes_4wk']/df['total_positive_engagements'])*100.,2)
        df['C2SR'] = round((df['total_sales_4wk']/df['total_positive_engagements'])*100.,2)
        df['ProdSaleRR'] = round((df['total_product_sales']/df['total_sends'])*100.,2)
        df['ProdQuoteRR'] = round((df['total_product_quotes']/df['total_sends'])*100.,2)

        #Clean up cooresponding metrics where necessary
        df[['mean_days_to_quote','mean_days_to_sale','mean_days_to_logon','mean_days_to_register','AVG_premium_per_program_all_prds','AVG_premium_per_program_target']] = df[['mean_days_to_quote','mean_days_to_sale','mean_days_to_logon','mean_days_to_register','AVG_premium_per_program_all_prds','AVG_premium_per_program_target']].round(1)
        df[['C2QR','C2SR']] = df[['C2QR','C2SR']].replace(np.inf,0)
        df[['C2QR','C2SR']] = df[['C2QR','C2SR']].fillna(0)
        df[['ProdSaleRR','ProdQuoteRR','multiprodRR']].fillna(0,inplace=True)
        df[['mean_days_to_quote','mean_days_to_sale','mean_days_to_logon','mean_days_to_register']].fillna(999,inplace=True)

        #Calculate months since active feature
        df['now'] = pd.to_datetime('today')
        df['last_send_date'] = pd.to_datetime(df['last_send_date'])
        df['months_since_active'] = (df['now']-df['last_send_date'])/np.timedelta64(1,'M')
        df['months_since_active'] = df['months_since_active'].astype(int)

        #Produce an arbitary group column (use later)
        df['group_column'] ='group'
    
        #clean unnecessary columns
        df.drop(['open_volume','click_volume','total_positive_engagements','now',
                 'total_negative_engagements','unsub_volume','total_quotes_4wk',
                 'total_sales_4wk','logon_volume','register_volume','total_MHP_sales'],axis=1)

        return df         
    
    def calculate_normalised_metrics(self,df):
        '''
        In this object our campaigns metrics are normalised by dividing by the average of each category. 
        This is done only for campaigns with total_send > 500. 
        
        input: program level dateframe
        output: program level dateframe
        
        '''

        df = df[df['total_sends'] > 500]

        df['openRR_nrm'] = (df['OpenRR']/df['avg_openRR'])
        df['posRR_nrm'] = (df['PositiveRR']/df['avg_posRR'])
        df['negRR_nrm'] = (df['NegativeRR']/df['avg_negRR'])
        df['quoteRR_nrm'] = (df['QuoteRR']/df['avg_quoteRR'])
        df['saleRR_nrm'] = (df['SalesRR']/df['avg_salesRR'])
        df['psaleRR_nrm'] = (df['ProdSaleRR']/df['avg_prdsalesRR'])
        df['pquoteRR_nrm'] = (df['ProdQuoteRR']/df['avg_prdquotesRR'])
        df['logonRR_nrm'] = (df['logonRR']/df['avg_logRR'])
        df['regRR_nrm'] = (df['RegisterRR']/df['avg_openRR'])
        df['c2qr_nrm'] = (df['C2QR']/df['avg_C2QR'])
        df['c2sr_nrm'] = (df['C2SR']/df['avg_C2SR'])
        df['multiprodrr_nrm'] = (df['multiprodRR']/df['avg_multiprodRR'])
        df['avg_revenue_nrm'] = (df['AVG_premium_per_program_all_prds']/df['avg_revenue'])
        df['avg_prd_revenue_nrm'] = (df['AVG_premium_per_program_target']/df['avg_prd_revenue'])

        df[['openRR_nrm','posRR_nrm','negRR_nrm','quoteRR_nrm','saleRR_nrm','psaleRR_nrm',
            'pquoteRR_nrm','logonRR_nrm','regRR_nrm','c2qr_nrm','c2sr_nrm','multiprodrr_nrm',
            'avg_revenue_nrm','avg_prd_revenue_nrm']].fillna(0,inplace=True)

        df.drop(['avg_openRR','avg_posRR','avg_negRR','avg_quoteRR','avg_salesRR','avg_prdsalesRR',
                 'avg_prdquotesRR','avg_logRR','avg_openRR','avg_C2QR','avg_C2SR','avg_multiprodRR',
                 'avg_revenue','avg_prd_revenue','now','group_column'],axis=1,inplace=True)

        df[['openRR_nrm','posRR_nrm','negRR_nrm','quoteRR_nrm','saleRR_nrm','psaleRR_nrm',
            'pquoteRR_nrm','logonRR_nrm','regRR_nrm','c2qr_nrm','c2sr_nrm','multiprodrr_nrm',
            'avg_revenue_nrm','avg_prd_revenue_nrm']] = df[['openRR_nrm','posRR_nrm','negRR_nrm','quoteRR_nrm','saleRR_nrm','psaleRR_nrm',
            'pquoteRR_nrm','logonRR_nrm','regRR_nrm','c2qr_nrm','c2sr_nrm','multiprodrr_nrm',
            'avg_revenue_nrm','avg_prd_revenue_nrm']].round(3)    

        return df
    
    
    def calculate_ace_scores(self,df):    
        '''
        This object we calculate the ACE, normalised ACE score and an Aviva Trading metric (to be revised) and return them in a dataframe

        input: program level dateframe
        output: program level dateframe

        '''

        ACE = (df['OpenRR']*df['PositiveRR']*10)-(df['NegativeRR']*100)
        df['ACE_score'] = ACE.round(0).astype(int)

        ACE_norm = 10*((df['openRR_nrm']*df['posRR_nrm'])-(df['negRR_nrm']))
        df['norm_ACE_score'] = ACE_norm.round(0).astype(int)

        ATP = (df["total_sends"]*df['psaleRR_nrm']*df['avg_prd_revenue_nrm'])+(df["total_sends"]*df['saleRR_nrm']*df['avg_revenue_nrm'])
        df['AT_score'] = ATP.fillna(0).round(0).astype(int)
    
        return df
    
    
    
    
    
    
    
    
    
    
    
    