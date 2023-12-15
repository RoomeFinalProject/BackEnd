from pymongo import MongoClient
import pprint
import pymongo
import datetime
import json
import os

client = MongoClient("localhost", 27017)

db = client.Research_Summary          
collection = db.Summary_collection    
posts = db.posts


with open("modified_today_jsons.json", 'r', encoding='utf-8') as file:
    data = json.load(file)

def insert_DB(data):
    result = posts.insert_many(data)
    result.inserted_ids
    return print("업데이트가 완료되었습니다.")

matching_documents = posts.find({'document_summary.date': '2023-12-14'})

for document in matching_documents:
    pprint.pprint(document)
 
count = posts.count_documents({'document_summary.date': '2023-12-14'})
print(count)


'''
# DB에 삽입할 내용
def Research_Sum_Lis():
    Research_Sum_List = []
    Reseearch_Summary_path = './Results_Summary/'
    file_names = os.listdir(Reseearch_Summary_path)
    for i, file_name in enumerate(file_names):
        full_path = os.path.join(Reseearch_Summary_path, file_name)
        with open (full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            Research_Sum_List.append(data)
    print(f'{len(Research_Sum_List)}개의 리서치 summary json파일이 준비되었습니다.')
    return Research_Sum_List

# DB에 삽입
#Research_Sum_List = Research_Sum_Lis()

def insert_DB(Research_Sum_List):
    result = posts.insert_many(Research_Sum_List)
    result.inserted_ids
    return print("업데이트가 완료되었습니다.")

# 내용 확인
print(pprint.pprint(posts.find_one({"date": "2023-12-06"})))

for post in posts.find({"date": "2023-12-06"}):
    print(pprint.pprint(post))


if __name__ == "__main__":
    for post in posts.find({"date": "2023-12-07"}):
        pprint.pprint(post)


'''
