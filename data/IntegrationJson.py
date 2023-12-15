import os
import json

directory_path = "Results_Summary"

files = os.listdir(directory_path)

# Read the content of each JSON file
today_jsons = []
for json_file in files:
    file_path = os.path.join(directory_path, json_file)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    today_jsons.append(data)
        # Process the data as needed

with open('todayResearch_file_urls.json', 'r', encoding='utf-8') as file:
    todayResearch_file_urls = json.load(file)
    
#print(todayResearch_file_urls)

for filename in todayResearch_file_urls:
    for doc_sum in today_jsons:
        if filename == doc_sum['document_summary']['title']:
            doc_sum['document_summary']['링크'] = todayResearch_file_urls[filename]
        else:
            continue


output_file_path = 'modified_today_jsons.json'
with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(today_jsons, output_file, ensure_ascii=False, indent=2)

print(f"Modified data saved to {output_file_path}")
        


