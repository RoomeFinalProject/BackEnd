from pymongo import MongoClient
import json


'''
   DB에 파일 저장하는 것 까지만 완료
   tutorial: https://pymongo.readthedocs.io/en/stable/tutorial.html
'''

client = MongoClient("localhost", 27017)

db = client.Research_Summary          
collection = db.Summary_collection    
posts = db.posts

#with open("./data/modified_toprank_20231217.json", 'r', encoding='utf-8') as file:
#    data = json.load(file)

with open("./data/modified_today_20231219.json", 'r', encoding='utf-8') as file:
    data = json.load(file)
    
#print(data)
def insert_DB(data):
    result = posts.insert_many(data)
    result.inserted_ids
    return print("업데이트가 완료되었습니다.")

if __name__ == '__main__':
    insert_DB(data)
    pass