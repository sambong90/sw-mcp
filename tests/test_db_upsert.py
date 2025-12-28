"""DB upsert 테스트"""

import pytest
import tempfile
import os
from src.sw_mcp.db.repo import MonsterRepository
from src.sw_mcp.db.models import MonsterBase
from src.sw_mcp.db.engine import get_engine, get_session


@pytest.fixture
def temp_db():
    """임시 DB 세션"""
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = db_file.name
    db_file.close()
    
    db_url = f"sqlite:///{db_path}"
    
    # 테이블 생성
    MonsterRepository.create_tables(db_url)
    
    yield db_url
    
    # 정리
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_upsert_insert(temp_db):
    """Insert 테스트"""
    repo = MonsterRepository()
    
    monster_data = {
        "id": 1,
        "com2us_id": 14105,
        "name": "Lushen",
        "element": "wind",
        "archetype": "attack",
        "base_hp": 9225,
        "base_attack": 900,
        "base_defense": 494,
        "speed": 110,
        "crit_rate": 15.0,
        "crit_damage": 50.0,
        "natural_stars": 4,
        "skills": [1, 2, 3],
    }
    
    monster = repo.upsert(monster_data)
    repo.commit()
    
    assert monster.com2us_id == 14105
    assert monster.name == "Lushen"
    assert monster.base_attack == 900
    assert monster.speed == 110
    
    repo.close()


def test_upsert_update(temp_db):
    """Update 테스트 (같은 com2us_id로 두 번 upsert)"""
    repo = MonsterRepository()
    
    # 첫 번째 insert
    monster_data1 = {
        "id": 1,
        "com2us_id": 14105,
        "name": "Lushen",
        "element": "wind",
        "base_hp": 9225,
        "base_attack": 900,
        "base_defense": 494,
        "speed": 110,
        "natural_stars": 4,
    }
    
    monster1 = repo.upsert(monster_data1)
    repo.commit()
    original_id = monster1.id
    
    # 두 번째 update (같은 com2us_id)
    monster_data2 = {
        "id": 1,
        "com2us_id": 14105,
        "name": "Lushen Updated",
        "element": "wind",
        "base_hp": 10000,  # 변경
        "base_attack": 950,  # 변경
        "base_defense": 494,
        "speed": 115,  # 변경
        "natural_stars": 4,
    }
    
    monster2 = repo.upsert(monster_data2)
    repo.commit()
    
    # 같은 레코드여야 함 (id 동일)
    assert monster2.id == original_id
    assert monster2.name == "Lushen Updated"
    assert monster2.base_hp == 10000
    assert monster2.base_attack == 950
    assert monster2.speed == 115
    
    # DB에서 직접 조회해서 확인
    monster3 = repo.get_by_com2us_id(14105)
    assert monster3 is not None
    assert monster3.name == "Lushen Updated"
    assert monster3.base_attack == 950
    
    repo.close()


def test_get_by_com2us_id(temp_db):
    """com2us_id로 조회 테스트"""
    repo = MonsterRepository()
    
    monster_data = {
        "id": 1,
        "com2us_id": 14105,
        "name": "Lushen",
        "element": "wind",
        "base_hp": 9225,
        "base_attack": 900,
        "base_defense": 494,
        "speed": 110,
        "natural_stars": 4,
    }
    
    repo.upsert(monster_data)
    repo.commit()
    
    # 조회
    monster = repo.get_by_com2us_id(14105)
    assert monster is not None
    assert monster.name == "Lushen"
    assert monster.base_attack == 900
    
    # 없는 경우
    monster_none = repo.get_by_com2us_id(99999)
    assert monster_none is None
    
    repo.close()


