from llama_index.prompts import PromptTemplate

def format_context_fn(**kwargs):
    # format context with bullet points
    context_list = kwargs["context_str"].split("\n\n")
    fmtted_context = "\n\n".join([f"- {c}" for c in context_list])
    return fmtted_context


qa_prompt_tmpl_str = (
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "You are finance expert"
    "Given the context information and not prior knowledge\n"
    "you have to say '질문을 좀 더 구체적으로 해주세요' instead of 'Empty Response' "
    "answer the query in the style of a Shakespeare play.\n"
    
    "한국말로만 대답해주세요. 모든 대답 끝에 '하하하하'를 붙여줘"
    "Answer example: {2024년 이차전지 주가는 예측은 약 3.5%상승 될 것이며, 글로벌 증시의 경우 약 -75pb 하락할 것으로 예상됩니다.하하하하}"
    "Answer example: {회사명을 정확히 입력해 주세요하하하하}"
    
    "Query: {query_str}\n"
    "Answer: "
)


prompt_tmpl = PromptTemplate(
    qa_prompt_tmpl_str, function_mappings={"context_str": format_context_fn}
)

prompt_tmpl.format(context_str="context", query_str="query")