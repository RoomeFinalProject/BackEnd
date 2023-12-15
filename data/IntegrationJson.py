import os
import json
from datetime import datetime

directory_path = "Results_Summary/231215"

files = os.listdir(directory_path)

# Read the content of each JSON file
today_jsons = []
for json_file in files:
    file_path = os.path.join(directory_path, json_file)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    today_jsons.append(data)
        # Process the data as needed

with open('Research_daily/20231215/todayResearch_file_urls_20231215.json', 'r', encoding='utf-8') as file:
    todayResearch_file_urls = json.load(file)
    
#print(todayResearch_file_urls)

for filename in todayResearch_file_urls:
    for doc_sum in today_jsons:
        if filename == doc_sum['document_summary']['title']:
            doc_sum['document_summary']['Link'] = todayResearch_file_urls[filename]
        else:
            continue

today_date_str = datetime.now().strftime("%Y%m%d")
output_file_path = f'modified_today_{today_date_str}.json'
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(today_jsons, output_file, ensure_ascii=False, indent=2)

print(f"Modified data saved to {output_file_path}")
        