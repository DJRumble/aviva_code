class config(object):
    


    def __init__(self):
        
        A_test_colname = 'ADA1'
        B_test_colname = 'ADA2'
        metrics = ['sales_cnt','x_sales_cnt','quotes_cnt','x_quotes_cnt']
        suffixes = ['S','XS','Q','XQ']
        volume = 'volume_count'  
        component_header = 'segment_cut'
        prior_sales_rates = {"motor":0,
                             "home":0,
                             "life":0,
                             "pmi":0,
                             "cic":0,
                             "travel":0,
                             "all":0}

        self.config_dataset = {
            'A':A_test_colname,
            'B':B_test_colname,
            'metric_headers':metrics,
            'suffixes':suffixes,
            'vol_header':volume,
            'prior_sales_rates':prior_sales_rates,
            'component_header':component_header
        }