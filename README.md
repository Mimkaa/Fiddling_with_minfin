# Retrieval of info about currency rates in Ukranian banks
### Frankly speaking it was a real hassle, but I made it somewhat working

# Quick functional description:

     # converts currency into a numeric code(do not ask me about it NBU says it is called "r030")
     
    print(get_numeric("USD"))
    #output: 840
\
&nbsp;

    # opposite of the previous one
    
    print(get_alph(978))
    # output: EUR
\
&nbsp;
    
    # gets info about all banks on this page :  https://minfin.com.ua/
    
    print(print(ask_minfin('USD',(2022,3,11))))
    # output:
    2022-03-11
    [{'bank': 'PrivatBank', 'r030': 840, 'cc': 'USD', 'rate': 29.255, 'date': '11.03.2022'}, {'bank': 'Raiffeisen Bank', 'r030': 840, 'cc': 'USD', 'rate': 29.25, 'date': '11.03.2022'}, ...)

\
&nbsp;
    
    # does the same stuff prevoius one does but return date for a period
    
    print(ask_minfin_period("USD",(2015,3,4),(2021,4,5)))
    # output:
     a gigantic list of lists of dicts

\
&nbsp;

    # these two just save .json and .csv files correspondingly 
    save_json("mm.json",ask_minfin_period("USD",(2015,11,2),(2021,1,2)))
    save_csv("mm.csv",ask_minfin_period("USD",(2015,11,2),(2021,1,2)))

\
&nbsp;
    
    # the most fun there:
    (plotable() is required removes data that is not present in all dicts i.e. ensure that the  data is valid for plotting)
    banks=["BTA Bank","PrivatBank"]
    plot_data([i for i in plotable(ask_minfin_period("USD",(2015,11,2),(2021,1,2))) if i["bank"] in banks])
    
    # it will plot a graph of values per year of banks you specify (please do not throw all of them in, it is a mess then)

![Alt text](images/inst1.png)
    
    # the same stuff but per month
    
    banks=["BTA Bank","PrivatBank"]
    plot_data([i for i in plotable(ask_minfin_period("USD",(2015,11,2),(2021,1,2),by='month')) if i["bank"] in banks])
    

![Alt text](images/inst2.png)

    

# Features
* do not know, maybe a simple caching to speed up the process a little cause I had to use translator to translate from Ukrainan names of banks, and it was taking quite a time, so I decided to help it a little
* maybe something else, do not remember
