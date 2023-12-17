from pymongo import MongoClient
import pprint
from datetime import datetime


def research_summary_from_DB(k = 5):
    '''
        날짜를 선정 후, 최근 5개까지 
    '''
    client = MongoClient("localhost", 27017)

    db = client.Research_Summary
    collection = db.Summary_collection
    posts = db.posts

    research_summary_list = []
    for post in posts.find({"Date": {"$gte": "2023-11-10", "$lte": "2023-12-17"}}).sort("Date",-1):
        research_summary_list.append(pprint.pformat(post))
        
    recent_research_k = research_summary_list[:k]
    #print(len(recent_research_5))
    return recent_research_k
if __name__ == '__main__':
    print(research_summary_from_DB())
    

