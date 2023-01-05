import requests
import pandas as pd
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import warnings

restaurantsTabelogInfo = pd.read_csv("./input/restrant_info.csv").fillna("")
restaurantsTabelogPageDict = dict(restaurantsTabelogInfo[["store_name","tabelog_url"]].values)

class TabelogUser:
    def __init__(self,store_name,url):
        self.store_name=""
        self.store_tabelog_url=""
        self.reviewr_name =""
        self.reviewr_id =""
        self.reviewr_url =""
        self.count = 0
        self.columns=["store_name",'reviewr_name',"reviewr_id","reviewr_url"]
        self.df = pd.DataFrame(columns=self.columns)
                    
        self.store_name = store_name
        self.store_tabelog_url= url
        self.collect_store_info(url)
        return 

    def collect_store_info(self, url):
        if url == "":
            self.reviewr_name =""
            self.reviewr_id =""
            self.reviewr_url =""
            self.make_df()
            return
        page_num=1
        while True:
            list_url= url +"dtlrvwlst?PG="+ str(page_num)
            print(list_url)
            if self.scraping_reviewer(list_url) != True:
                break
            page_num +=1
        return

    def scraping_reviewer(self,url):
        r = requests.get(url)
        time.sleep(2)
        if r.status_code != requests.codes.ok:
            return False
        soup = BeautifulSoup(r.content, 'html.parser')
        soup_name_list = soup.find_all('p', class_='rvw-item__rvwr-name')
        for name in soup_name_list:
            self.reviewr_url=urljoin("https://tabelog.com/", name.find("a").get('href'))
            self.reviewr_name=name.find("span").text
            self.reviewr_id= name.find("a").get('href').replace("/rvwr/","").replace("/","")
            print(self.reviewr_url, self.reviewr_name,self.reviewr_id)
            self.make_df()
        return True

    def make_df(self):
        se = pd.Series([self.store_name, self.reviewr_name, self.reviewr_id, self.reviewr_url],self.columns)
        self.df = self.df.append(se, self.columns) # データフレームに行を追加
        return

warnings.simplefilter('ignore')
for store_name, url in restaurantsTabelogPageDict.items():
    review = TabelogUser(store_name,url)
    review.df.to_csv("./output/{:s}.csv".format(store_name.replace("/","")) ,index=False)

# count = 0
# for store_name, url in restaurantsTabelogPageDict.items():
#     count = count + 1
#     if count <= 3:
#         review = TabelogUser(store_name,url)
#         review.df.to_csv("./output/{:s}.csv".format(store_name) ,index=False)
#     else:
#         break


