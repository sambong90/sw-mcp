"""몬스터 레지스트리 테스트"""

import pytest
import tempfile
import csv
import os
from pathlib import Path
from src.sw_core.monster_registry import MonsterRegistry
from src.sw_core.types import MonsterBaseStats
from src.sw_db.models import get_session, Monster, Base, get_engine


@pytest.fixture
def temp_csv():
    """임시 CSV 파일 생성"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'master_id', 'name_en', 'name_ko', 'element', 'awakened',
            'nat_stars', 'base_hp', 'base_atk', 'base_def', 'base_spd', 'base_cr', 'base_cd'
        ])
        writer.writeheader()
        writer.writerow({
            'master_id': '14105',
            'name_en': 'Lushen',
            'name_ko': '루쉔',
            'element': 'wind',
            'awakened': 'true',
            'nat_stars': '4',
            'base_hp': '9225',
            'base_atk': '900',
            'base_def': '494',
            'base_spd': '110',
            'base_cr': '15',
            'base_cd': '50',
        })
        temp_path = f.name
    
    yield temp_path
    
    # 정리
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_db():
    """임시 DB 세션 생성"""
    import tempfile
    db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = db_file.name
    db_file.close()
    
    db_url = f"sqlite:///{db_path}"
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 테스트 데이터 추가
    monster = Monster(
        master_id=14105,
        name_ko="루쉔",
        name_en="Lushen",
        element="wind",
        awakened=True,
        nat_stars=4,
        base_hp=9225,
        base_atk=900,
        base_def=494,
        base_spd=110,
        base_cr=15,
        base_cd=50,
    )
    session.add(monster)
    session.commit()
    
    yield session, db_url
    
    # 정리
    session.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_registry_load_csv(temp_csv):
    """CSV에서 몬스터 로드 테스트"""
    registry = MonsterRegistry(data_dirs=[os.path.dirname(temp_csv)])
    
    # CSV 파일명을 맞춰야 함
    csv_dir = os.path.dirname(temp_csv)
    csv_name = os.path.basename(temp_csv)
    
    # 임시로 파일명 변경 (monsters*.csv 패턴)
    new_path = os.path.join(csv_dir, "monsters_test.csv")
    os.rename(temp_csv, new_path)
    
    try:
        registry.warm_cache()
        
        # master_id로 조회
        stats = registry.get(master_id=14105)
        assert stats is not None
        assert stats.master_id == 14105
        assert stats.name_en == "Lushen"
        assert stats.name_ko == "루쉔"
        assert stats.base_atk == 900
        assert stats.base_spd == 110
        
        # 이름으로 조회
        stats2 = registry.get(name="Lushen")
        assert stats2 is not None
        assert stats2.master_id == 14105
        
        stats3 = registry.get(name="루쉔")
        assert stats3 is not None
        assert stats3.master_id == 14105
    finally:
        if os.path.exists(new_path):
            os.unlink(new_path)


def test_registry_load_from_db(temp_db):
    """DB에서 몬스터 로드 테스트"""
    session, db_url = temp_db
    registry = MonsterRegistry(db_session=session)
    
    stats = registry.get(master_id=14105)
    assert stats is not None
    assert stats.master_id == 14105
    assert stats.name_en == "Lushen"
    assert stats.base_atk == 900


def test_registry_priority_db_over_csv(temp_db, temp_csv):
    """DB 우선순위 테스트 (DB > CSV)"""
    session, db_url = temp_db
    
    # DB에 다른 값으로 설정
    monster = session.query(Monster).filter(Monster.master_id == 14105).first()
    monster.base_atk = 950  # CSV(900)와 다른 값
    session.commit()
    
    # CSV도 준비
    csv_dir = os.path.dirname(temp_csv)
    new_path = os.path.join(csv_dir, "monsters_test.csv")
    os.rename(temp_csv, new_path)
    
    try:
        registry = MonsterRegistry(db_session=session, data_dirs=[csv_dir])
        
        # DB 값이 우선되어야 함
        stats = registry.get(master_id=14105)
        assert stats is not None
        assert stats.base_atk == 950  # DB 값
    finally:
        if os.path.exists(new_path):
            os.unlink(new_path)


def test_registry_get_default():
    """기본값 반환 테스트"""
    registry = MonsterRegistry()
    default = registry.get_default()
    
    assert default.master_id == 0
    assert default.base_atk == 900
    assert default.base_spd == 104
    assert default.base_hp == 10000
    assert default.base_def == 500


def test_registry_name_normalization():
    """이름 정규화 테스트"""
    registry = MonsterRegistry()
    
    # 대소문자/공백 무시
    normalized1 = registry._normalize_name("Lushen")
    normalized2 = registry._normalize_name("lushen")
    normalized3 = registry._normalize_name("Lu shen")
    normalized4 = registry._normalize_name("Lu-shen")
    
    assert normalized1 == normalized2 == normalized3 == normalized4


def test_seed_and_export_roundtrip(temp_db):
    """DB → CSV → DB round-trip 테스트"""
    session, db_url = temp_db
    
    # Export
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        export_path = f.name
    
    try:
        from src.sw_api.manage import export_monsters, seed_monsters
        
        # Export
        export_monsters(export_path, db_url)
        assert os.path.exists(export_path)
        
        # 새 DB에 import
        import tempfile
        db_file2 = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path2 = db_file2.name
        db_file2.close()
        db_url2 = f"sqlite:///{db_path2}"
        
        try:
            seed_monsters(export_path, db_url2)
            
            # 검증
            session2 = get_session(db_url2)
            monster = session2.query(Monster).filter(Monster.master_id == 14105).first()
            assert monster is not None
            assert monster.name_en == "Lushen"
            assert monster.base_atk == 900
        finally:
            if os.path.exists(db_path2):
                os.unlink(db_path2)
    finally:
        if os.path.exists(export_path):
            os.unlink(export_path)


