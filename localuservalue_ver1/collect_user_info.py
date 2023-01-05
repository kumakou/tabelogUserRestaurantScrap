import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
import warnings

class UserInfo:
    def __init__(self):
        self.reviewr_name =""
        self.reviewr_id =""
        self.reviewr_url =""
        self.zenkoku_num=0
        self.hakodate_num=0
        self.columns=['reviewr_name',"reviewr_id","reviewr_url","zenkoku_num","hakodate_num","rate"]
        self.df = pd.DataFrame(columns=self.columns)
        
        restaurantsTabelogInfo = pd.read_csv("./output_integrate/all_reviewr.csv")
        for data in restaurantsTabelogInfo.itertuples():
            self.reviewr_name =data[1]
            self.reviewr_id =data[3].replace("https://tabelog.com/rvwr/","").replace("/","")
            self.reviewr_url =data[3]
            self.reviewr_zenkoku_info(self.reviewr_url)
            self.reviewr_hakodate_info(self.reviewr_url)
            print(self.reviewr_name, self.reviewr_zenkoku_info,self.reviewr_hakodate_info)
            self.make_df()
            self.df.to_csv("./output_user_info/userinfo17.csv" ,index=False)
    
    def reviewr_zenkoku_info(self,url):
        r = requests.get(url)
        time.sleep(1.5)
        print(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        self.zenkoku_num =soup.find("span",class_="rvwr-navi__count").text
        return
    
    def reviewr_hakodate_info(self,url):
        r = requests.get(url+"visited_restaurants/list?pal=hokkaido&LstPrf=A0105&LstAre=A010501")
        print(url+"visited_restaurants/list?pal=hokkaido&LstPrf=A0105&LstAre=A010501")
        time.sleep(1.5)
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            num_list=soup.find_all("span",class_="c-page-count__num")
            self.hakodate_num=num_list[2].text
        except:
            self.hakodate_num=1

        return 
    
    def make_df(self):
        se = pd.Series([self.reviewr_name, self.reviewr_id, self.reviewr_url,self.zenkoku_num,self.hakodate_num,int(self.hakodate_num)/int(self.zenkoku_num)],self.columns)
        self.df = self.df.append(se, self.columns) # データフレームに行を追加
        return

warnings.simplefilter('ignore')
review = UserInfo()
