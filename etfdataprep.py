"""
Comparing the S&P 500 index and the S&P 500 ESG index via their SPDR ETF trackers
Holdings data downloaded from SSGA website:

https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-etf-trust-spy

https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-esg-etf-efiv

'ESG: Why Not? Insignificant Alpha Observed between the S&P 500 ESG Index and the S&P 500' at https://www.spglobal.com/en/research-insights/articles/esg-why-not-insignificant-alpha-observed-between-the-sp-500-esg-index-and-the-sp-500
"""
"""
S&P 500
"The S&P 500, or simply the S&P, is a stock market index that measures the stock performance of 500 large companies listed on stock exchanges in the United States."

S&P 500 ESG Index
"The S&P 500 ESG Index is a broad-based, market-cap-weighted index that is designed to measure the performance of securities meeting sustainability criteria, while maintaining similar overall industry group weights as the S&P 500."
https://www.spglobal.com/spdji/en/indices/equity/sp-500-esg-index/#overview

"""

import pandas as pd
import numpy as np
import openpyxl
import altair as alt

"""
SPY is the ticker for the SPDR S&P 500 ETF
EFIV is the ticker for the SPDR S&P 500 ESG ETF
"""

#read in the holdings files from the State Street Global Adviser website

#S&P 500 ETF holdings updated daily
dfspy = pd.read_excel('https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx', engine='openpyxl')

#S&P 500 ESG ETF holdings updated daily
dfefiv = pd.read_excel('https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-efiv.xlsx', engine='openpyxl')

#Drop the first 3 rows as they are not part of the table of index holdings
dfspy.drop(index=dfspy.index[[0,1,2]], inplace=True)
dfefiv.drop(index=dfefiv.index[[0,1,2]], inplace=True)

#Drop the columns with all NA values

dfspy.dropna(axis=1, how='all', inplace=True)
dfefiv.dropna(axis=1, how='all', inplace=True)

#Grab the first row of the resulting dataframe and assign it to the column names
dfspy = dfspy.rename(columns=dfspy.iloc[0]).drop(dfspy.index[0])
dfefiv = dfefiv.rename(columns=dfefiv.iloc[0]).drop(dfefiv.index[0])

#Drop rows with NA values

dfspy.dropna(axis=0, inplace=True)
dfefiv.dropna(axis=0, inplace=True)

# Add a column with the relevant index name to each of these dataframes
dfspy['Index'] = 'S&P 500'
dfefiv['Index'] = 'S&P 500 ESG'

dfspy.rename(columns = {'Weight':'Weight %'}, inplace = True) #rename the 'Weight' column as 'Weight %' as the figures in this column are percentages
dfefiv.rename(columns = {'Weight':'Weight %'}, inplace = True) #rename the 'Weight' column as 'Weight %' as the figures in this column are percentages

#We see from the above that the weights column is not numeric, and zero weights appear as "-". We will assign the value '0' to these rows, and change the datatype of the 'Weights %' column to numeric.

dfspy["Weight %"].replace({"-": "0"}, inplace=True)
dfefiv["Weight %"].replace({"-": "0"}, inplace=True)

# The weight column should be a float data type, not object
dfspy["Weight %"] = pd.to_numeric(dfspy["Weight %"])
dfefiv["Weight %"] = pd.to_numeric(dfefiv["Weight %"])

# Remove unnecessary columns such as 'Identifier', 'SEDOL' and 'Shares Held'

dfspy.drop(['Identifier','SEDOL','Shares Held'],axis=1,inplace=True)
dfefiv.drop(['Identifier','SEDOL','Shares Held'],axis=1,inplace=True)

frames = [dfspy, dfefiv]
df = pd.concat(frames, ignore_index=True) #concatenate the two dataframes and reset the index to count the total rows

# We will remove the securities that are in the 'Unassigned' sector and rebalance the rest of the weights
# This is because the ETF will have some of these securities for liquidity purposes, but the index itself will not

unassign_wt_spy = dfspy.loc[dfspy['Sector'] == 'Unassigned','Weight %'].sum()
unassign_wt_efiv = dfefiv.loc[dfefiv['Sector'] == 'Unassigned','Weight %'].sum()

dfspy['Reweight %'] = np.round((dfspy['Weight %']/(100-unassign_wt_spy))*100, decimals=2)
dfefiv['Reweight %'] = np.round((dfefiv['Weight %']/(100-unassign_wt_efiv))*100, decimals=2)

# We will now re-order the columns in the preferred order

dfspy = dfspy[['Index', 'Name', 'Ticker', 'Weight %', 'Reweight %', 'Sector','Local Currency']]
dfefiv = dfefiv[['Index', 'Name', 'Ticker', 'Weight %', 'Reweight %', 'Sector','Local Currency']]

# We will now drop the rows with the 'Unassigned' sector securities

dfsp500 = dfspy[dfspy.Sector != 'Unassigned']
dfsp500esg = dfefiv[dfefiv.Sector != 'Unassigned']

# We will also drop the 'Weight %' column, as we will only be considering the rebalanced weights
# Then we'll rename the 'Reweight %' column as 'Weight %'

dfsp500.drop(['Weight %'],axis=1,inplace=True)
dfsp500.rename(columns = {"Reweight %": "Weight %"}, 
          inplace = True)
          
dfsp500esg.drop(['Weight %'],axis=1,inplace=True)
dfsp500esg.rename(columns = {"Reweight %": "Weight %"}, 
          inplace = True)

#Plotting in Altair

# Now we'll plot this data using Altair
# For each index dataframe, we will make two connected charts.
# One is a bar chart showing the sector breakdown for the index
# The other is a bar chart showing all the companies and their weights in the index
# Clicking on the bar for any sector in the first chart modifies the second chart to show the companies in that sector

color = alt.Color('Sector:N')
click = alt.selection_multi(encodings=['color'])

#Chart for SP500

chart_sp500 = alt.Chart(dfsp500,width=600, height=200).mark_bar().encode(
    x=alt.X('Sector:O', title=" "),
    y=alt.Y('sum_of_weights:Q', title='Weight %'),
    color=alt.condition(click, color, alt.value('lightgray')),
    tooltip=['no_of_names:Q','sum_of_weights:Q']
    ).transform_aggregate(
    sum_of_weights='sum(Weight %):Q',no_of_names='count(Name):Q',
    groupby=["Sector"]
    ).add_selection(
        click
    ).properties(title="Sector Breakdown for S&P 500")

chart_sp500_comp = alt.Chart(dfsp500, width = 600, height = 200).mark_bar().encode(
    x=alt.X('Name:O', title=" "),
    y=alt.Y('Weight %:Q', title='Weight %'),
    color='Sector:N',
    tooltip=['Name:N','Weight %:Q']
    ).transform_filter(
    click
    ).properties(title="Companies in S&P 500")


#Chart for SP500 ESG

chart_sp500esg = alt.Chart(dfsp500esg,width=600, height=200).mark_bar().encode(
    x=alt.X('Sector:O', title=" "),
    y=alt.Y('sum_of_weights:Q', title='Weight %'),
    color=alt.condition(click, color, alt.value('lightgray')),
    tooltip=['no_of_names:Q','sum_of_weights:Q']
    ).transform_aggregate(
    sum_of_weights='sum(Weight %):Q', no_of_names='count(Name):Q',
    groupby=["Sector"]
    ).add_selection(
        click
    ).properties(title="Sector Breakdown for S&P 500 ESG")

chart_sp500esg_comp = alt.Chart(dfsp500esg, width = 600, height = 200).mark_bar().encode(
    x=alt.X('Name:O', title=" "),
    y=alt.Y('Weight %:Q', title='Weight %'),
    color='Sector:N',
    tooltip=['Name:N','Weight %:Q']
    ).transform_filter(
    click
    ).properties(title="Companies in S&P 500 ESG")   

alt_chart = alt.hconcat(alt.vconcat(chart_sp500,chart_sp500_comp), alt.vconcat(chart_sp500esg,chart_sp500esg_comp))

alt_chart
