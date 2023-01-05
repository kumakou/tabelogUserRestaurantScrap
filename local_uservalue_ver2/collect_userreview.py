import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import os
import warnings

class User:
    """
    食べログスクレイピングクラス
    test_mode=Trueで動作させると、最初のページの３店舗のデータのみを取得できる
    """
    def __init__(self, base_url,reviewr_name, test_mode=True, begin_page=1, end_page=60):
        #変数宣言
        self.reviewr_name=reviewr_name
        self.reviewr_url=base_url
        self.store_id=''
        self.store_id_num=0
        self.store_name=''
        self.store_address=''
        self.store_genre=''
        self.store_tellnum=''
        self.store_closedday=''
        self.store_homepage = '',
        self.store_dinner_price=''
        self.store_lunch_price_range=''
        self.store_score=0
        self.columns=["reviewr_name","reviewr_url",'store_id','store_name','store_address','store_genre','store_tellnum','store_closedday','store_homepage','store_dinner_price_range','store_lunch_price_range','store_score']
        self.df = pd.DataFrame(columns=self.columns)
        self.__regexcomp=re.compile(r'\n|\s')

        page_num = begin_page #店舗一覧ページ番号

        if test_mode:
            print("test_modeはtrueです")
            list_url = base_url + str(page_num) +'/visited_restaurants/list?PG='+str(page_num)+'&select_sort_flg=1'
            self.scrape_list(list_url, mode=test_mode)
        else:
            print("test_modeはfalseです")
            while True:
                list_url = base_url +'/visited_restaurants/list?PG='+str(page_num)+'&Srt=D&SrtT=rvcn'
                print(list_url)
                if self.scrape_list(list_url, mode=test_mode) != True:
                    break
                
                #INパラメータまでのページ数を取得する
                if page_num >= end_page:
                    break
                page_num +=1
        return
    
    def scrape_list(self, list_url, mode):
        """
        店舗一覧ページのパーシング
        """
        time.sleep(4)
        print("店舗一覧の取得")
        r =requests.get(list_url)
        print("店舗一覧の取得済み")
        if r.status_code != requests.codes.ok:
            print("店舗一覧終わり1")
            return False
        
        soup = BeautifulSoup(r.content, 'html.parser')
        soup_a_list = soup.find_all('a', class_='simple-rvw__rst-name-target')

        if len(soup_a_list)==0:
            print("店舗一覧終わり2")
            return False
        
        genre_info = soup.find_all("p",class_="simple-rvw__area-catg")
        genrelist=[]
        for genre in genre_info:
            genrelist.append(genre.text)
        

        if mode:
            for i, soup_a in enumerate(soup_a_list[:1]):
                item_url = soup_a.get('href') #店の個別ページURLを取得
                print('アイテムのurlは'+item_url+'です')
                self.store_id_num += 1
                self.scrape_item(item_url, mode, genrelist[i])
        else: 
            for i, soup_a in enumerate(soup_a_list):
                item_url = soup_a.get('href') #店の個別ページURLを取得
                self.store_id_num +=1
                self.scrape_item(item_url, mode, genrelist[i])
            
        return True 

    def scrape_item(self, item_url, mode,genre):
        """
        個別店舗情報ページのパーシング
        """
        time.sleep(4)
        print("個別店舗の取得")
        r = requests.get(item_url)
        print("個別店舗の取得済")
        if r.status_code != requests.codes.ok:
            print(f'error:not found{ item_url}')
            return

        soup = BeautifulSoup(r.content, 'html.parser')
        store_name_tag = soup.find('h2', class_='display-name')
        store_name = store_name_tag.span.string
        print('店名:{}'.format(store_name.strip()))
        self.store_name = store_name.strip()

        # 評価点数取得
        rating_score_tag = soup.find('b', class_='c-rating__val')
        rating_score = rating_score_tag.span.string
        print('  評価点数：{}点'.format(rating_score))
        self.store_score = rating_score

        # 店舗の住所取得
        store_address=soup.find('p',class_="rstinfo-table__address").text
        print(" 住所：{}".format(store_address))
        self.store_address = store_address

        #　店舗のジャンル取得
        self.store_genre=genre.replace(" ","").replace("　","").split('/')[1]
        print(" ジャンル：{}".format(self.store_genre))

        #電話番号の取得
        try:
            store_tellnum = soup.find_all('strong', class_="rstinfo-table__tel-num")
            store_tellnum = store_tellnum[1].text
        except:
            store_tellnum = "-"
        self.store_tellnum=store_tellnum
        print(" 電話番号：{}".format(store_tellnum))

        #定休日の取得
        try:
            store_closedday = soup.find('dd', class_="rdheader-subinfo__closed-text").string
        except:
            store_closedday = ""
        self.store_closedday=store_closedday.replace( '\n' , '' ).replace(' ', '')
        print(" 定休日：{}".format(self.store_closedday))

        #ホームページの取得
        try:
            store_homepage=soup.find('p', class_='homepage')
            store_homepage= store_homepage.find('span').text
        except:
            store_paymentmethod = ""
        
        self.store_homepage=store_homepage
        print(" ホームページ{}".format(store_homepage))
        # 店舗の予算取得
        #<a href="https://tabelog.com/hokkaido/A0105/A010501/1000077/dtlratings/#price-range" class="rdheader-budget__price-target">￥15,000～￥19,999</a>
        store_price_range_tag= soup.find_all('a', class_='rdheader-budget__price-target')
        #print(store_price_range_tag)
        store_dinner_price_range=store_price_range_tag[0].string
        store_lunch_price_range=store_price_range_tag[1].string
        print('  夜の予算：{}'.format(store_dinner_price_range))
        print('  昼の予算：{}'.format(store_lunch_price_range))
        self.store_dinner_price_range=store_dinner_price_range
        self.store_lunch_price_range=store_lunch_price_range

        # データフレームの生成
        self.make_df()
        return

    def make_df(self):
        self.store_id = str(self.store_id_num) #0パディング
        se = pd.Series([self.reviewr_name,self.reviewr_url,self.store_id, self.store_name, self.store_address, self.store_genre,self.store_tellnum ,self.store_closedday,self.store_homepage,self.store_dinner_price_range, self.store_lunch_price_range, self.store_score],self.columns)
        self.df = self.df.append(se, self.columns) # データフレームに行を追加
        return


warnings.simplefilter('ignore')
restaurantsTabelogInfo = pd.read_csv("./local_uservalue_ver2/integrate_reviewer/all_reviewr.csv")
count =63
#CSV保存
for user_data in restaurantsTabelogInfo.itertuples():
    count=count+1
    reviewr_name =user_data[1]
    reviewr_url =user_data[3]
    UserInfo = User(base_url=reviewr_url,reviewr_name=reviewr_name,test_mode=False,begin_page=1 )
    UserInfo.df.to_csv("./local_uservalue_ver2/output_user_visited_store/user{:d}.csv".format(count) ,index=False)
