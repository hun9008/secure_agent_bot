from fastapi import APIRouter, HTTPException
import asyncio
import subprocess
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

import pandas as pd
import re
import os

from models.model import user_info, chat_prompt

from konlpy.tag import Okt
import anthropic
from dotenv import load_dotenv

router = APIRouter()

okt = Okt()

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# 형태소 분석 및 명사+형용사 추출
def preprocess_and_tokenize(text: str) -> str:
    # 소문자 변환 및 불필요한 공백 제거
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()

    # 명사와 형용사 추출
    tokens = okt.pos(text, stem=True)  # stem=True를 사용하면 동사 및 형용사의 기본형을 추출
    words = [word for word, pos in tokens if pos in ['Noun', 'Adjective']]  # 명사(Noun)와 형용사(Adjective)만 추출
    
    return ' '.join(words)

# 보고서 로드 및 전처리 + 토큰화
def load_and_preprocess_report(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as file:
        report_text = file.read()
    
    # 보고서 문장 단위로 분리 및 전처리
    report_lines = [preprocess_and_tokenize(line) for line in report_text.splitlines()]

    # TF-IDF 벡터화 (n-gram 추가)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_df=0.95, min_df=0.05)
    report_vectors = vectorizer.fit_transform(report_lines)
    
    return report_lines, report_vectors, vectorizer

report_path = "report.md"
report_lines, report_vectors, vectorizer = load_and_preprocess_report(report_path)

async def fetch_ans_llama31(prompt: str):
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            ["ollama", "run", "llama3.1", prompt],
            capture_output=True,
            text=True
        )
    )
    
    output = result.stdout.strip()
    return output

async def fetch_ans_claude(prompt: str):
    print("[Claude Prompt]:", prompt)
    try:
        # 프롬프트 형식을 'Human'과 'Assistant' 구조로 맞춤
        full_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"  # Human 질문으로 시작하고 Assistant의 응답으로 이어지게끔 포맷

        message = client.completions.create(
            model="claude-2",
            prompt=full_prompt,
            max_tokens_to_sample=1024,
            temperature=0.2
        )

        return message.completion.strip()

    except Exception as e:
        print(f"Claude API 호출 실패: {e}")
        raise HTTPException(status_code=500, detail="Claude API 호출 실패")

def search_report_for_answer(query: str, max_results: int = 3):
    # 질문을 전처리 및 토큰화
    query = preprocess_and_tokenize(query)
    print("[Tokenized Query]:", query)

    # 질문을 벡터화
    query_vector = vectorizer.transform([query])
    print("[Query Vector Shape]:", query_vector.shape)

    # 보고서 벡터 정보 확인
    print("[Report Vectors Shape]:", report_vectors.shape)

    # 코사인 유사도 계산
    cosine_similarities = cosine_similarity(query_vector, report_vectors).flatten()

    # 유사도가 가장 높은 문장 3개 선택
    related_indices = cosine_similarities.argsort()[-max_results:][::-1]
    
    # 유사도가 0인 경우 필터링
    related_results = [report_lines[i] for i in related_indices if cosine_similarities[i] > 0]
    print("[Search] Found related results : ", related_results)

    return "\n".join(related_results) if related_results else "관련된 정보가 없습니다."

@router.post("/chat")
async def chat(chat_prompt: chat_prompt):

    prev_chat = chat_prompt.prev_chat
    prompt = chat_prompt.prompt

    try:

        relevant_info = search_report_for_answer(prompt)

        extended_prompt = f"""
        문서에서 찾은 정보:\n{relevant_info}\n\n
        질문: {prompt}\n\n
        이전 대화: {prev_chat}\n\n

        위 정보를 바탕으로 질문에 대한 답변을 3~5문장 이내로 작성해주세요.
        """

        response = await fetch_ans_claude(extended_prompt)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"response": response}

@router.post("/report")
async def report(user_info: user_info):

    # ./src에서 .csv 파일을 읽어옴.
    asset_size_data = pd.read_csv('./src/asset_size_data.csv')
    asset_style_data = pd.read_csv('./src/asset_style_data.csv')
    grade_data = pd.read_csv('./src/grade_data.csv')
    style_data = pd.read_csv('./src/style_data.csv')

    label = {
        '총자산 10만원 미만 고객 비율': 'sb10r',
        '총자산 100만원 미만 고객 비율': 'sb11r',
        '총자산 1,000만원 미만 고객 비율': 'sb12r',
        '총자산 5,000만원 미만 고객 비율': 'sb13r',
        '총자산 1억원 미만 고객 비율': 'sb14r',
        '총자산 1억원 이상 고객 비율': 'sb15r',
        '지분증권 자산 비율': 'sb16r',
        '채무증권 자산 비율': 'sb17r',
        '수익증권 자산 비율': 'sb18r',
        '파생결합증권 자산 비율': 'sb19r',
        '금전총액 자산 비율': 'sb20r',
        '투자등급_공격투자형 비율': 'sc11r',
        '투자등급_적극투자형 비율': 'sc12r',
        '투자등급_위험중립형 비율': 'sc13r',
        '투자등급_안정추구형 비율': 'sc14r',
        '투자등급_안정형 비율': 'sc15r',
        '주식 거래유형_단타거래 고객 비율': 'sb37r',
        '주식 거래유형_백화점포트폴리오 고객 비율': 'sb38r',
        '주식 거래유형_저자산 일반주 고객 비율': 'sb39r',
        '주식 거래유형_우량주 중심 안전형 고객 비율': 'sb40r',
        '주식 거래유형_CMA중심 무거래 고객 비율': 'sb41r',
        '주식 거래유형_초우량 고객 비율': 'sb42r'
    }      

    prompt = f"""{asset_size_data}\n{asset_style_data}\n{grade_data}\n{style_data}\n{label}\n
        
주어진 데이터를 기반으로 고객에게 맞춤형 투자 보고서를 작성해 주세요. {user_info.info} 각 항목에 대해 데이터를 분석하여 고객의 투자 성향과 자산 분포를 설명하고, 데이터를 바탕으로 맞춤형 투자 전략을 제안해 주세요.

보고서는 다음과 같은 형식으로 작성해 주세요:

1. **개요**: 고객의 상황과 보고서의 목적을 설명합니다.
2. **자산 분포 분석**: 주어진 데이터를 통해 고객의 자산 규모와 자산 종류별 분포를 분석합니다. 관련 수치를 반영하여 고객의 자산 현황을 설명합니다.
3. **투자 등급 분석**: 데이터를 기반으로 고객의 투자 성향(공격적, 안정적 등)을 분석하여 설명합니다.
4. **주식 거래 유형 분석**: 주식 거래 데이터를 바탕으로 고객의 주식 거래 방식(단타, 우량주 투자 등)을 분석합니다.
5. **맞춤형 투자 전략 제안**: 데이터를 기반으로 고객의 상황에 맞는 맞춤형 투자 전략을 제안합니다. 안정적이고 장기적인 투자 방안을 포함해주세요.
6. **결론**: 보고서의 핵심 내용을 요약하고 고객이 앞으로 나아가야 할 방향을 제안합니다.

보고서는 한글로 작성해야 하며 보고서 내의 내용만 알려줘."""
    
    try:
        response = await fetch_ans_llama31(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    ## save as markdown file
    with open('report.md', 'w') as f:
        f.write(response)

    return {"response": response}

@router.get("/get_report")
async def get_report():
    with open('report.md', 'r') as f:
        response = f.read()

    return {"response": response}
