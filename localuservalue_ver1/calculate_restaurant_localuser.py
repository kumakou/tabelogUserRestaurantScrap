import pandas as pd
import os 
import math
import warnings

# すべてのレビュワー情報
users_Info = pd.read_csv("output_user_info/total_userinfo.csv")

# outputの中にあるファイル名の配列
restaurant_list_path = "output"
restaurant_list = os.listdir(restaurant_list_path)

# ローカル客かどうかを判断する閾値
threshold= 0.5

# 列のカラム
columns=['store_name',"local_user","zenkoku_user","rate"]
output_df = pd.DataFrame(columns=columns)


columns_restaurant=['store_name','reviewr_name',"reviewr_url","zenkoku_num","hakodate_num","rate"]

warnings.simplefilter('ignore')

for restarant in restaurant_list:
    restrant_df= pd.read_csv(restaurant_list_path+"/"+restarant)
    store_name=""
    local_user= 0
    zenkoku_user = 0
    local_user_rate=0
    zenkoku_num=0
    hakodate_num=0
    reviewr_name=""
    reviewr_url=""
    rate=0
    store_name = restrant_df["store_name"][0]
    output_restaurant_df = pd.DataFrame(columns=columns_restaurant)
    for user in restrant_df.itertuples():
        reviewr_url=user[4]
        reviewr_name= user[3]
        if type(reviewr_url) is str:
            user_series=users_Info[users_Info["reviewr_url"]==reviewr_url]
            zenkoku_num=user_series["zenkoku_num"].item()
            hakodate_num=user_series["hakodate_num"].item()
            rate=user_series["rate"].item()
            # print(store_name,hakodate_num,zenkoku_num,rate)
            if rate > threshold:
                local_user=local_user+1
            else:
                zenkoku_user=zenkoku_user+1  
        se1 = pd.Series([store_name, reviewr_name, reviewr_url,zenkoku_num, hakodate_num,rate],columns_restaurant)   
        output_restaurant_df=output_restaurant_df.append(se1,columns_restaurant)   
    if not(local_user==0) and not(zenkoku_user ==0):
        local_user_rate=local_user/zenkoku_user
    output_restaurant_df.to_csv("./output_restaurant_local_rate/{:s}.csv".format(str(store_name).replace("/","")) ,index=False)

    # print(store_name,local_user,zenkoku_user,local_user_rate)
    se = pd.Series([store_name, local_user, zenkoku_user, local_user_rate],columns)
    output_df=output_df.append(se,columns)

output_df.to_csv("./output_restaurant_local_rate/local_rate.csv",index=False)