import pandas as pd
import os

columns=['reviewr_name',"reviewr_id","reviewr_url"]
path ="output"
dirList= os.listdir(path)
df = pd.DataFrame(columns=columns)

for file in dirList:
    reviewr_info=pd.read_csv("./"+path+"/"+file)
    reviewr_info=reviewr_info.drop(columns='store_name')
    df=pd.concat([df,reviewr_info])

df=df.drop_duplicates(subset='reviewr_url')
df.to_csv("./output_integrate/all_reviewr.csv",index=False)