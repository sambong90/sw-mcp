"""SWARFARM 클라이언트 테스트"""

import pytest
import json
from unittest.mock import Mock, patch
from src.sw_mcp.swarfarm_client import SwarfarmClient


@pytest.fixture
def sample_monster_page():
    """샘플 몬스터 페이지 JSON"""
    return {
        "count": 2,
        "next": "https://swarfarm.com/api/v2/monsters/?format=json&page=2",
        "previous": None,
        "results": [
            {
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
                "resistance": 0.0,
                "accuracy": 0.0,
                "base_stars": 4,
                "natural_stars": 4,
                "awaken_level": 1,
                "family_id": 141,
                "skill_group_id": 1,
                "skills": [1, 2, 3],
            },
            {
                "id": 2,
                "com2us_id": 14104,
                "name": "Julie",
                "element": "wind",
                "archetype": "attack",
                "base_hp": 9885,
                "base_attack": 823,
                "base_defense": 461,
                "speed": 100,
                "crit_rate": 15.0,
                "crit_damage": 50.0,
                "resistance": 0.0,
                "accuracy": 0.0,
                "base_stars": 4,
                "natural_stars": 4,
                "awaken_level": 1,
                "family_id": 141,
                "skill_group_id": 1,
                "skills": [4, 5, 6],
            },
        ]
    }


def test_swarfarm_client_get_monsters_list(sample_monster_page):
    """get_monsters_list 테스트"""
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_monster_page
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = SwarfarmClient(sleep_ms=0)  # 테스트 속도 향상
        
        # 첫 페이지만 가져오기
        monsters = client.get_monsters_list(max_pages=1)
        
        assert len(monsters) == 2
        assert monsters[0]["com2us_id"] == 14105
        assert monsters[0]["name"] == "Lushen"
        assert monsters[1]["com2us_id"] == 14104
        assert monsters[1]["name"] == "Julie"
        
        client.close()


def test_swarfarm_client_pagination(sample_monster_page):
    """Pagination 테스트"""
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        
        # 첫 페이지
        page1 = sample_monster_page.copy()
        page1["next"] = "https://swarfarm.com/api/v2/monsters/?format=json&page=2"
        
        # 두 번째 페이지 (마지막)
        page2 = {
            "count": 2,
            "next": None,
            "previous": "https://swarfarm.com/api/v2/monsters/?format=json&page=1",
            "results": [
                {
                    "id": 3,
                    "com2us_id": 14103,
                    "name": "Arang",
                    "element": "wind",
                    "base_hp": 10230,
                    "base_attack": 747,
                    "base_defense": 461,
                    "speed": 100,
                }
            ]
        }
        
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2
        
        mock_client.request.side_effect = [mock_response1, mock_response2]
        mock_client_class.return_value = mock_client
        
        client = SwarfarmClient(sleep_ms=0)
        
        monsters = list(client.get_monsters_all(max_pages=2))
        
        assert len(monsters) == 3
        assert monsters[0]["name"] == "Lushen"
        assert monsters[1]["name"] == "Julie"
        assert monsters[2]["name"] == "Arang"
        
        client.close()

