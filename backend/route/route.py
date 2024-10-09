from fastapi import APIRouter, HTTPException
import asyncio
import subprocess
import pandas as pd

from models.model import user_info

router = APIRouter()

async def fetch_ans_llama31(prompt_type: str):
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(
        None,
        lambda: subprocess.run(
            ["ollama", "run", "llama3.1", prompt_type],
            capture_output=True,
            text=True
        )
    )
    
    output = result.stdout.strip()
    return output

@router.post("/chat")
async def chat(prompt: str):
    try:
        response = await fetch_ans_llama31(prompt)
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
