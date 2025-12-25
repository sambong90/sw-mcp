"""실행 예제"""

from src.sw_mcp.swex_parser import parse_swex_json
from src.sw_mcp.optimizer import optimize_lushen
import json

# 예제: SWEX JSON 파일 경로
# json_file = "swex_export.json"
# runes = load_swex_json(json_file)

# 또는 직접 JSON 데이터 사용
example_json = {
    "runes": [],
    "units": []
}

if __name__ == "__main__":
    # JSON 로드
    # runes = parse_swex_json(example_json)
    
    # 최적화 실행
    # results = optimize_lushen(runes, target="B", top_n=10)
    
    # 결과 출력
    # for i, result in enumerate(results, 1):
    #     print(f"#{i} Score: {result['score']:.2f}")
    #     print(f"  CR: {result['cr_total']:.1f}%")
    #     print(f"  CD: {result['cd_total']:.1f}%")
    #     print(f"  ATK%: {result['atk_pct_total']:.1f}%")
    #     print(f"  무형 배치: {result['intangible_assignment']}")
    #     print()
    
    print("예제 스크립트입니다. 실제 JSON 파일을 로드하여 사용하세요.")

