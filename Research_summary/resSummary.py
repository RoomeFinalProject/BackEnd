from .JSONFormat import convert_to_jsonformat
from llama_index.indices.document_summary import DocumentSummaryIndex
from .PromptandSum import doc_summary_index
from .Loading import file_names
from .selenium_todayResearch import researchToday
from pymongo import MongoClient

def summary_list(file_names):
   
    # 1. mongo
    mongo_client = MongoClient('mongodb://localhost:27017/')                                                # MongoDB 연결 정보
    db = mongo_client['research_db']
    collection = db['research']

    company_name = "유안타 증권" 

    summary_list = []
    # for file_name in file_names:
    for file_name  in file_names:
        content = doc_summary_index.get_document_summary(f"{file_name}")
        json_result = convert_to_jsonformat(file_name, content)
        summary_list.append(json_result)

        # # MongoDB에 title, url, date 자료 저장
        # existing_research = collection.find_one({"title": result[i]['title'], "url": result[i]['url']})
        # if existing_research:
        #     title = existing_research['title']
        #     url = existing_research['url']
        #     date = existing_research['date']
        #     content = existing_research['content']

        # else:
        #     collection.update_one(                                                                      # MongoDB에 자막 요약 정보 저장
        #     {"title": result[i]['title'], "url": result[i]['url']},                             # collection.update_one: 문서가 있을 경우 덮어쓰기
        #     {"$set": {"title": result[i]['title'], "url": result[i]['url'], "date": result[i]['date'], "content": content}},                        
        #     upsert=True                                                                             # upsert 문서가 없는 경우 새로운 문서를 추가
        # )
            
    return summary_list

# if __name__ == 'main':
#     summary_list(file_names)


