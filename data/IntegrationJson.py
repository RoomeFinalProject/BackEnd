import os
import json
from datetime import datetime

#summary_JSON_directory_path = "./data/Results_Summary/toprank_231217"
#url_JSON_directory_path = './data/Research_toprank/TopRank_file_urls_20231217.json'

summary_JSON_directory_path = "./data/Results_Summary/daily_231214"
url_JSON_directory_path = "./data/Research_daily/todayResearch_file_urls_20231214.json"

files = os.listdir(summary_JSON_directory_path)

json_list = []
for json_file in files:
    file_path = os.path.join(summary_JSON_directory_path, json_file)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    json_list.append(data)
        

with open(url_JSON_directory_path, 'r', encoding='utf-8') as file:
    todayResearch_file_urls = json.load(file)
    
#print(todayResearch_file_urls)

for filename in todayResearch_file_urls:
    for doc_sum in json_list:
        if filename == doc_sum['title']:
            doc_sum['Link'] = todayResearch_file_urls[filename]
        else:
            continue

#today_date_str = datetime.now().strftime("%Y%m%d")
today_date_str = "20231214"
output_file_path = f'./data/modified_today_{today_date_str}.json'
#output_file_path = f'./data/modified_toprank_{today_date_str}.json'
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(json_list, output_file, ensure_ascii=False, indent=2)

print(f"Modified data saved to {output_file_path}")
        