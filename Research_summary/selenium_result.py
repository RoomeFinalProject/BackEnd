
from selenium_todayResearch import researchToday
from fastapi.responses import JSONResponse

result = researchToday()


async def research_jsonize():
#     li = []
#     for title, url, date_ in result.items():
#         video_info = get_video_info(channel_id, channel_name)
#         all_video_data.append(video_info)
#     print(all_video_data)
    print(result)
    return JSONResponse(content=result)


