"""Rules engine that validates and applies rules"""

from typing import List, Dict, Any, Optional
from .schema import Ruleset, RuneRules, SetRules, SlotSpecialRule
from ..sw_core.types import Rune


class RulesEngine:
    """Rules engine for validating runes and builds"""
    
    def __init__(self, ruleset: Ruleset):
        """
        Args:
            ruleset: Loaded ruleset
        """
        self.ruleset = ruleset
        self.rune_rules = ruleset.rune_rules
        self.set_rules = ruleset.set_rules
    
    def validate_rune(self, rune: Rune) -> tuple[bool, Optional[str]]:
        """
        Validate a single rune against rules
        
        Args:
            rune: Rune to validate
        
        Returns:
            (is_valid, error_message)
        """
        slot = rune.slot
        
        # Check slot main stat disallowed
        disallowed_main = self.rune_rules.slot_main_disallowed.get(slot, [])
        if rune.main_stat_id in disallowed_main:
            return False, f"Slot {slot}: main stat {rune.main_stat_id} is disallowed"
        
        # Check slot main stat allowed (if specified)
        if self.rune_rules.slot_main_allowed:
            allowed_main = self.rune_rules.slot_main_allowed.get(slot)
            if allowed_main is not None and rune.main_stat_id not in allowed_main:
                return False, f"Slot {slot}: main stat {rune.main_stat_id} is not in allowed list"
        
        # Check slot special rules
        for special_rule in self.rune_rules.slot_special_rules:
            if special_rule.slot == slot:
                # Check main stat
                if rune.main_stat_id in special_rule.disallowed_main:
                    return False, f"Slot {slot}: main stat {rune.main_stat_id} disallowed by special rule"
                
                # Check prefix
                if rune.has_prefix and rune.prefix_stat_id in special_rule.disallowed_prefix:
                    return False, f"Slot {slot}: prefix stat {rune.prefix_stat_id} disallowed by special rule"
                
                # Check substats
                for sub in rune.subs:
                    if sub.stat_id in special_rule.disallowed_sub:
                        return False, f"Slot {slot}: substat {sub.stat_id} disallowed by special rule"
        
        # Check sub disallowed (general)
        disallowed_sub = self.rune_rules.sub_disallowed.get(slot, [])
        for sub in rune.subs:
            if sub.stat_id in disallowed_sub:
                return False, f"Slot {slot}: substat {sub.stat_id} is disallowed"
        
        # Check sub no dup main
        if self.rune_rules.sub_no_dup_main:
            for sub in rune.subs:
                if sub.stat_id == rune.main_stat_id:
                    return False, f"Substat {sub.stat_id} duplicates main stat {rune.main_stat_id}"
            
            if rune.has_prefix and rune.prefix_stat_id == rune.main_stat_id:
                return False, f"Prefix stat {rune.prefix_stat_id} duplicates main stat {rune.main_stat_id}"
        
        return True, None
    
    def validate_build(self, runes: List[Rune]) -> tuple[bool, Optional[str]]:
        """
        Validate a 6-rune build
        
        Args:
            runes: List of 6 runes
        
        Returns:
            (is_valid, error_message)
        """
        if len(runes) != 6:
            return False, f"Build must have 6 runes, got {len(runes)}"
        
        # Check unique slots
        slots = [rune.slot for rune in runes]
        if len(set(slots)) != 6:
            return False, "Duplicate slots found"
        
        # Check unique rune IDs
        rune_ids = [rune.rune_id for rune in runes]
        if len(set(rune_ids)) != 6:
            return False, "Duplicate rune IDs found"
        
        # Validate each rune
        for rune in runes:
            is_valid, error = self.validate_rune(rune)
            if not is_valid:
                return False, f"Invalid rune (slot {rune.slot}, id {rune.rune_id}): {error}"
        
        # Check intangible count (max 1)
        intangible_count = sum(1 for rune in runes if rune.intangible)
        if intangible_count > 1:
            return False, f"Too many intangible runes: {intangible_count} (max 1)"
        
        return True, None
    
    def apply_set_bonus(self, stats: Dict[str, float], runes: List[Rune], intangible_assignment: Optional[Dict[int, str]] = None) -> Dict[str, float]:
        """
        Apply set bonuses to stats
        
        Args:
            stats: Current stats dictionary
            runes: List of runes in build
            intangible_assignment: Optional intangible assignment {rune_id: "to_Rage"/"to_Fatal"/"to_Blade"/"none"}
        
        Returns:
            Updated stats dictionary with set bonuses applied
        """
        # Count sets
        set_counts: Dict[int, int] = {}
        for rune in runes:
            if rune.intangible:
                # Intangible: check assignment
                if intangible_assignment and rune.rune_id in intangible_assignment:
                    assignment = intangible_assignment[rune.rune_id]
                    if assignment == "to_Rage":
                        set_counts[10] = set_counts.get(10, 0) + 1
                    elif assignment == "to_Fatal":
                        set_counts[8] = set_counts.get(8, 0) + 1
                    elif assignment == "to_Blade":
                        set_counts[2] = set_counts.get(2, 0) + 1
                    # "none" means no set contribution
                # If no assignment, don't count
            else:
                set_counts[rune.set_id] = set_counts.get(rune.set_id, 0) + 1
        
        # Apply bonuses
        result_stats = stats.copy()
        
        for set_id, count in set_counts.items():
            if set_id in self.set_rules.sets:
                set_bonus = self.set_rules.sets[set_id]
                
                # Apply 2-set bonus
                if count >= 2 and set_bonus.bonus_2:
                    for stat_name, value in set_bonus.bonus_2.items():
                        result_stats[stat_name] = result_stats.get(stat_name, 0.0) + value
                
                # Apply 4-set bonus
                if count >= 4 and set_bonus.bonus_4:
                    for stat_name, value in set_bonus.bonus_4.items():
                        result_stats[stat_name] = result_stats.get(stat_name, 0.0) + value
        
        return result_stats
    
    def check_content_applicability(self, content_name: str, build: List[Rune], **kwargs) -> tuple[bool, Optional[str]]:
        """
        Check if build is applicable to content (stub)
        
        Args:
            content_name: Content name
            build: List of runes
            **kwargs: Additional context
        
        Returns:
            (is_applicable, reason)
        """
        # Stub implementation
        # TODO: Implement content-specific rules
        return True, None
    
    def get_gem_eligibility(self, stat_id: int) -> bool:
        """Check if stat can be gemmed"""
        return stat_id in self.ruleset.gem_grind_rules.gem_allowed_stats
    
    def get_grind_eligibility(self, stat_id: int) -> bool:
        """Check if stat can be grinded"""
        return stat_id in self.ruleset.gem_grind_rules.grind_allowed_stats
    
    def get_gem_cap(self, stat_id: int, is_ancient: bool = False) -> Optional[float]:
        """Get gem cap for stat"""
        for cap in self.ruleset.gem_grind_rules.caps:
            if cap.stat_id == stat_id:
                return cap.ancient_cap if is_ancient else cap.normal_cap
        return None
    
    def get_grind_cap(self, stat_id: int, is_ancient: bool = False) -> Optional[float]:
        """Get grind cap for stat (same as gem cap)"""
        return self.get_gem_cap(stat_id, is_ancient)

