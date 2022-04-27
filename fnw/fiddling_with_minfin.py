import requests
import json
import os
import csv
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
from googletrans import Translator

translator = Translator(service_urls=[
      'translate.google.com',
      'translate.google.co.uk',
    ])

MONO_API_URL="https://api.monobank.ua/bank/currency"
PRIVAT_API_URL="https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
NBU_API_URL="https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date={date}&json"
MINFIN_URL="https://minfin.com.ua/ua/currency/banks/{curr}/{date}/"
PYTHONPATH=os.path.dirname(os.path.abspath(__file__))
try:
    with open("CACHE.json","r") as f:
        TRANSLATION_CACHE=json.load(f)
except:
    TRANSLATION_CACHE={}


def get_numeric(alph_code)->int:
    """Get r030 value of cc code.
        Example:
             >>> get_numeric("USD")
        Args:
          alph_code: cc code of a currency
        Returns:
          r030 code.
    """
    with open(f"{PYTHONPATH}/numeric.json","r") as f:
        data = json.load(f)
    for d in data:
        if d['AlphabeticCode']==alph_code:
            return int(d['NumericCode'])

def get_alph(code)->str:
    """Get cc value of r030 code.
        Example:
             >>> get_alph(978)
        Args:
          code: r030 code of a currency
        Returns:
          cc code.
    """
    with open(f"{PYTHONPATH}/numeric.json","r") as f:
        data = json.load(f)
    for d in data:
        if d['NumericCode']==code:
            return d['AlphabeticCode']


def ask_minfin(currency,date)->list:
    """Get information about cash exchange rates of  all Ukrainian banks at a certain time.
        Example:
             >>> ask_minfin("USD",(2021,4,3))
        Args:
            currency: Chosen currency,
            date: Selected date exchange rates
        Returns:
          List of dicts which contain (bank_name,currency,rate,date) .
    """
    date_tup=datetime(*date)
    if type(currency)==int:
        currency=get_alph(currency)
    currency=currency.lower()

    formatted_date=date_tup.strftime("%Y-%m-%d")
    print(formatted_date)
    header = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"}
    response = requests.get(MINFIN_URL.format(curr=currency,date=formatted_date), headers=header)
    table_currs = pd.read_html(response.text)[1]
    pd.set_option('display.max_columns', None)


    if not list(table_currs.iloc[:, 0])[:-1]:
        raise ValueError('SOMETHING WENT WRONG (MAYBE THE CURRENCY IS NOT PRESENT IN THE BANKS),(AND DATES FROM 2015 ARE REQUIRED)(.')



    banks=list(table_currs.iloc[:, 0])[:-1]
    rates=list(table_currs.iloc[:, 1])[:-1]

    for b in banks:
        if b not in TRANSLATION_CACHE.keys():
            TRANSLATION_CACHE[b]=translator.translate(b,src='uk', dest='en').text
            with open(f"{PYTHONPATH}/CACHE.json","w",encoding='utf-8') as f:
                json.dump(TRANSLATION_CACHE,f)

    banks_translted=[TRANSLATION_CACHE[b] for b in banks]

    answer=[]
    for i in range(len(banks)):
        answer.append({
            "bank":banks_translted[i],
            "r030":get_numeric(currency.upper()),
            "cc":currency.upper(),
            "rate":rates[i],
            "date":date_tup.strftime("%d.%m.%Y")
        })

    return answer



#print(ask_minfin('USD',(2022,3,11)))

def ask_minfin_period(currency,start_date,end_date,by="year")->list:
    """Get information about cash exchange rates of  all Ukrainian banks in a certain period of time.
        Example:
             >>> ask_minfin("USD",(2015,4,3),(2021,4,3))
        Args:
            currency: Chosen currency,
            start_date: date from
            end_date: ending date
            by:
                flag, values:
                    "year",
                    "month",
                    "day"(not desireable)
        Returns:
          List of lists of dicts which contain (bank_name,currency,rate,date) .
    """
    if type(currency)==int:
        currency=get_alph(currency)
    currency=currency.lower()

    collected_data=[]
    if by=='year':
        diff=end_date[0]-start_date[0]
        for i in range(diff+1):
            print("[COLLECTING...]")
            date_incremented=datetime(*start_date) + relativedelta(years=i)
            collected_data.append(ask_minfin(currency,(date_incremented.year,date_incremented.month,date_incremented.day)))

    elif by=='month':
        diff=(end_date[0] - start_date[0]) * 12 + (end_date[1] - start_date[1])
        for i in range(diff+1):
            print("[COLLECTING...]")
            date_incremented=datetime(*start_date) + relativedelta(months=i)
            date_tuple=(date_incremented.year,date_incremented.month,date_incremented.day)
            collected_data.append(ask_minfin(currency,date_tuple))

    elif by=='day':
        diff=(datetime(*end_date)-datetime(*start_date)).days
        for i in range(diff+1):
            print("[COLLECTING...]")
            date_incremented=datetime(*start_date) + relativedelta(days=i)
            collected_data.append(ask_minfin(currency,(date_incremented.year,date_incremented.month,date_incremented.day)))
    else:
        print("too much data to retrieve")

    return collected_data

#print(ask_minfin_period((2014,11,2),(2021,1,2),"EUR"))
def show_variants()->None:
    """Print all cached bank names.
        Example:
             >>> show_variants()


    """
    for b in TRANSLATION_CACHE.values():
        print(b)

def plotable(data_set)->list:
    """ensure that data is valid for plotting i.e. removes data that is not present in all dicts.
        Example:
             >>> plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR")
        Args:
            data_set: list of dicts from ask_minfin_period function or ask_minfin,

        Returns:
          Polished list.
    """
    if len(data_set)<2:
        raise ValueError('DATA MUST CONTAIN MORE THAN 1 RECORD')
    merged=[j for i in data_set for j in i]
    list_names=[b['bank'] for b in merged]
    plotable_fin=[]
    used_names=[]
    for n,i in enumerate(list_names):
        if list_names.count(i)==len(data_set) and n not in used_names:
            plotable_fin.append(merged[n])
            used_names.append(n)
    return merged


def plot_data(data_set)->None:
    """plots date.
        Example:
             >>> banks=["BTA Bank","PrivatBank"]
             >>> plot_data([i for i in plotable(ask_minfin_period((2015,11,2),(2021,1,2),"USD")) if i["bank"] in banks])

        Args:
            data_set: list of dicts from ask_minfin_period function or ask_minfin,


    """
    if len(data_set)<2:
        raise ValueError('DATA MUST CONTAIN MORE THAN 1 RECORD')
    # dates=[]
    # for rec in data_set:
    #     dates.append(datetime.strptime(rec[0]['date'],"%d.%m.%Y"))
    values={}
    for rec in data_set:
        if rec["bank"] not in values.keys():
            values[rec["bank"]]=[]
        else:
            values[rec["bank"]].append((rec["rate"],datetime.strptime(rec["date"],"%d.%m.%Y")))

    for k,val in values.items():
        dates=[]
        vals=[]
        for v in val:
            dates.append(v[1])
            vals.append(v[0])
        plt.plot(dates,vals,label=k)


    plt.legend(loc="upper left")
    plt.show()




def save_json(filename,data):
    """ saves json.
        Example:
             >>> save_json("my_sss.json",ask_minfin_period((2015,11,2),(2021,1,2),"EUR"))

        Args:
            filename: name of the file
            data: list of dicts from ask_minfin_period function or ask_minfin,


    """
    if ".json" not in filename or filename=="CACHE.json":
         raise ValueError("FILENAME MUST CONTAIN .json and MUST NOT BE CACHE.json")
    with open(filename,"w",encoding='utf-8') as f:
                json.dump(data,f)

def save_csv(filename,data):
    """ saves csv.
        Example:
             >>> save_csv("my_sss.csv",ask_minfin("USD",(2015,11,2)))

        Args:
            filename: name of the file
            data: list of dicts from ask_minfin_period function or ask_minfin,


    """
    if all([type(d)==list for d in data]):
        data=[j for i in data for j in i]

    if ".csv" not in filename:
        raise ValueError("FILENAME MUST CONTAIN .csv")

    myheaders=data[0].keys()
    rows=[d.values() for d in data]
    with open(filename, 'w', newline='') as myfile:
            writer = csv.writer(myfile)
            writer.writerow(myheaders)
            writer.writerows(rows)