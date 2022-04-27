import requests
import json
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

try:
    with open("CACHE.json","r") as f:
        TRANSLATION_CACHE=json.load(f)
except:
    TRANSLATION_CACHE={}


def get_numeric(alph_code)->str:
    """Get r030 value of cc code.
        Example:
             >>> get_numeric("USD")
        Args:
          alph_code: cc code of a currency
        Returns:
          r030 code.
    """
    with open("numeric.json","r") as f:
        data = json.load(f)
    for d in data:
        if d['AlphabeticCode']==alph_code:
            return int(d['NumericCode'])

def get_alph(code)->int:
    """Get cc value of r030 code.
        Example:
             >>> get_alph(978)
        Args:
          code: r030 code of a currency
        Returns:
          cc code.
    """
    with open("numeric.json","r") as f:
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
            with open("CACHE.json","w",encoding='utf-8') as f:
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


banks=["BTA Bank","PrivatBank"]
plot_data([i for i in plotable(ask_minfin_period((2015,11,2),(2021,1,2),"USD")) if i["bank"] in banks])

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

#save_csv("my_sss.csv",ask_minfin("USD",(2015,11,2)))


#save_json("my_sss.json",ask_minfin_period((2015,11,2),(2021,1,2),"EUR"))

#print(ask_minfin('USD',(2022,3,11)))

#plot_all(plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR")))

# print(len(plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR"))))
# print(plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR")))
# print(len([i for i in plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR")) if i['bank']=="PrivatBank"]))
# print(len([i for i in plotable(ask_minfin_period((2014,11,2),(2021,1,2),"EUR")) if i['bank']=='BTA Bank']))

# def get_currency_rate_in_a_bank(name,currency,date):
#     date=datetime(*date)
#     if type(currency)==int:
#         currency=get_alph(currency)
#     currency=currency.lower()
#
#     if name not  in ALL_BANKS:
#         raise ValueError('I DO NOT HAVE INFO ABOUT THIS ONE(.')
#
#     rate=data_all_banks["curr_vals"][data_all_banks['banks'].index(name)]
#
#     formatted_date=date.strftime("%d.%m.%Y")
#     answer={
#         "bank":name,
#         "r030":get_numeric(currency.upper()),
#         "cc":currency.upper(),
#         "rate":rate,
#         "date":formatted_date
#
#     }
#     return answer


def ask_nbu(currency,date):
    formatted_date=date.strftime("%Y%m%d")
    response = requests.get(NBU_API_URL.format(date=formatted_date))
    answer=[record for record in response.json() if record['cc']==currency][0]
    answer_embellished={
        "bank":"NBU",
        "r030":answer['r030'],
        "cc":answer['cc'],
        "rate":answer['rate'],
        "date":answer["exchangedate"]
    }
    return answer_embellished

# def ask_privat(currency,date):
#     formatted_date=date.strftime("%d.%m.%Y")
#     response= requests.get(PRIVAT_API_URL.format(date=formatted_date))
#     answer=[record for record in response.json()['exchangeRate'][1:] if record["currency"]==currency][0]
#     answer_embellished={
#         "bank":"Privat",
#         "r030":get_numeric(answer["currency"]),
#         "cc":answer["currency"],
#         "rate":answer["saleRate"],
#         "date":formatted_date
#
#     }
#     return answer_embellished
#
#
#
# def get_currency_rate_privat(currency,date):
#     if type(currency)==int:
#         currency=get_alph(currency)
#     return ask_privat(currency,datetime(*date))
#
# def get_currency_rate_mono(currencyA,currencyB):
#     if type(currencyA)==str:
#         currencyA=get_numeric(currencyA)
#     if type(currencyB)==str:
#         currencyB=get_numeric(currencyB)
#     response= requests.get(MONO_API_URL)
#     while response.status_code!=200:
#         response= requests.get(MONO_API_URL)
#     return [record for record in response.json() if int(record["currencyCodeA"])==currencyA and int(record["currencyCodeB"])==currencyB][0]
#
#
# def get_currency_rate_nbu(currency,date):
#     if type(currency)==int:
#         currency=get_alph(currency)
#     return ask_nbu(currency,datetime(*date))
#
#
#
#
# def plot_currency_rate(data):
#     if len(data)<2:
#         print("data set must consist of at least 2 components")
#         return
#     else:
#         dates=[]
#         values=[]
#         for d in data:
#             dates.append(datetime.strptime(d['date'],"%d.%m.%Y"))
#             values.append(d['rate'])
#
#         plt.ylabel(data[0]['cc'])
#         plt.xlabel("Date")
#         plt.plot(dates,values,label=data[0]['bank'])
#         plt.legend(loc="upper left")
#
#
#         plt.show()
#
# def plot_camparison(data1,data2):
#      if len(data1)<2 or len(data2)<2:
#         print("data set must consist of at least 2 components")
#         return
#      else:
#         dates=[]
#         dates1=[]
#         values=[]
#         values1=[]
#
#         for v in data1:
#             values.append(v['rate'])
#             dates.append(datetime.strptime(v['date'],"%d.%m.%Y"))
#         for v1 in data2:
#             values1.append(v1['rate'])
#             dates1.append(datetime.strptime(v1['date'],"%d.%m.%Y"))
#
#         plt.ylabel(data1[0]['cc'])
#         plt.xlabel("Date")
#         plt.plot(dates,values,color='r',label=data1[0]['bank'])
#         plt.plot(dates1,values1,color='g',label=data2[0]['bank'])
#         plt.legend(loc="upper left")
#         plt.show()
#
#
# def save_csv_single(data,filename,flag='w'):
#     if type(data)==list:
#             print("try 'save_csv_period'")
#             return
#
#     if flag=='w':
#
#         myheaders=data.keys()
#         myvalues=data.values()
#         with open(filename, 'w', newline='') as myfile:
#             writer = csv.writer(myfile)
#             writer.writerow(myheaders)
#             writer.writerow(myvalues)
#
#     elif flag=='a':
#         myvalues=data.values()
#         with open(filename, 'a') as f_object:
#             writer_object = csv.writer(f_object)
#             writer_object.writerow(myvalues)
#     else:
#         print("I did not procure for other flags")
#
#
# def save_csv_period(data,filename,flag='w'):
#     if type(data)!=list:
#         print("try 'save_csv_single'")
#         return
#     if flag=='w':
#         myheaders=data[0].keys()
#         with open(filename, 'w', newline='') as myfile:
#             writer = csv.DictWriter(myfile, fieldnames=myheaders)
#             writer.writeheader()
#             writer.writerows(data)
#     elif flag=='a':
#         with open(filename, 'a', newline='') as myfile:
#             writer = csv.writer(myfile)
#             for d in data:
#                 writer.writerow(list(d.values()))
#     else:
#         print("I did not procure for other flags")


# def save_json(data,filename,flag='w'):
#     if flag=='w':
#         with open(filename, 'w', encoding='utf-8') as f:
#             if type(data)!=list:
#                 data=[data]
#             json.dump(data, f)
#
#     elif flag=='a':
#         with open(filename) as json_file:
#             data_got = json.load(json_file)
#         with open(filename, 'w', encoding='utf-8') as f:
#             if type(data)!=list:
#                 data=[data]
#             data_got+=data
#             json.dump(data_got, f)
#
#     else:
#         print("I did not procure for other flags")





#save_json(get_period("NBU",978,(2015, 1, 1),(2021, 1, 1),by="year"),"NBU.json")
#save_csv_period(get_currency_rate_nbu("USD",(2020, 4, 1)),"NBU.csv")
#save_csv_period(get_period("NBU",978,(2015, 1, 1),(2021, 1, 1),by="month"),"NBU.csv",flag='a')
# plot_currency_rate(get_period("Privat",978,(2015, 1, 1),(2021, 1, 1)))
#plot_currency_rate(get_period("NBU",978,(2015, 1, 1),(2021, 1, 1),by="month"))
#plot_camparison(get_period("Privat",978,(2015, 1, 1),(2021, 1, 1)),get_period("NBU",978,(2015, 1, 1),(2021, 1, 1)))










# print(response1.json())
# print(response2.json())
#response = requests.get(BANK_API_URL.format(date=formatted_date))