"""SWEX JSON 파서"""

import json
from typing import List, Dict, Any, Optional
from .types import Rune, SubStat, SET_ID_NAME, STAT_ID_NAME


def parse_rune(raw: Dict[str, Any]) -> Optional[Rune]:
    """SWEX JSON에서 룬 파싱"""
    try:
        rune_id = raw.get("rune_id")
        slot = raw.get("slot_no")
        set_id = raw.get("set_id")
        main_stat_id = raw.get("pri_eff", [0])[0]
        main_stat_value = raw.get("pri_eff", [0, 0])[1]
        level = raw.get("class", 0)
        quality = raw.get("rank", 0)
        
        # prefix_eff 파싱 ([stat_id, value] 또는 0)
        prefix_eff = raw.get("prefix_eff", 0)
        prefix_stat_id = 0
        prefix_stat_value = 0.0
        if prefix_eff and prefix_eff != 0 and isinstance(prefix_eff, list) and len(prefix_eff) >= 2:
            prefix_stat_id = prefix_eff[0]
            prefix_stat_value = prefix_eff[1]
        
        # 서브 스탯 파싱
        subs: List[SubStat] = []
        sec_eff_list = raw.get("sec_eff", [])
        
        for sec_eff in sec_eff_list:
            if len(sec_eff) >= 2:
                stat_id = sec_eff[0]
                base = sec_eff[1]
                enchanted = sec_eff[2] if len(sec_eff) > 2 else False
                grind = sec_eff[3] if len(sec_eff) > 3 else 0.0
                
                # 최종 값 = base + grind
                final_value = base + grind
                
                subs.append(SubStat(
                    stat_id=stat_id,
                    value=final_value,
                    enchanted=enchanted,
                    grind=grind
                ))
        
        return Rune(
            rune_id=rune_id,
            slot=slot,
            set_id=set_id,
            main_stat_id=main_stat_id,
            main_stat_value=main_stat_value,
            subs=subs,
            level=level,
            quality=quality,
            prefix_stat_id=prefix_stat_id,
            prefix_stat_value=prefix_stat_value
        )
    except (KeyError, TypeError, IndexError) as e:
        print(f"룬 파싱 오류: {e}, raw={raw}")
        return None


def parse_swex_json(json_data: Dict[str, Any]) -> List[Rune]:
    """SWEX JSON 전체 파싱 (rune_list + unit_list 병합)"""
    runes: List[Rune] = []
    seen_rune_ids = set()
    
    # 1. rune_list에서 룬 파싱
    rune_list = json_data.get("runes", [])
    for raw_rune in rune_list:
        rune = parse_rune(raw_rune)
        if rune and rune.rune_id not in seen_rune_ids:
            runes.append(rune)
            seen_rune_ids.add(rune.rune_id)
    
    # 2. unit_list에서 장착된 룬 파싱 (units와 unit_list 둘 다 확인)
    unit_list = json_data.get("unit_list", [])  # unit_list 우선
    if not unit_list:
        unit_list = json_data.get("units", [])  # units도 확인
    
    for unit in unit_list:
        unit_runes = unit.get("runes", [])
        for raw_rune in unit_runes:
            rune = parse_rune(raw_rune)
            if rune and rune.rune_id not in seen_rune_ids:
                runes.append(rune)
                seen_rune_ids.add(rune.rune_id)
    
    return runes


def load_swex_json(file_path: str) -> List[Rune]:
    """SWEX JSON 파일 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return parse_swex_json(data)

