# crops.py (重构版)

import random
from plant import CropData

class Field:
    """Represents a single piece of farmland with its own soil properties."""
    def __init__(self):
        self.soil_npk = {'N': 100.0, 'P': 100.0, 'K': 100.0} # N-P-K values of the soil
        self.crop: CropInstance | None = None

    def apply_fertilizer(self, nutrient_type, amount=25):
        """Applies fertilizer to the soil."""
        if nutrient_type in self.soil_npk:
            self.soil_npk[nutrient_type] += amount
            return f"成功为田地施加了{amount}单位的{nutrient_type}肥。"
        return "无效的肥料类型。"

    def plant_crop(self, crop_data: CropData, planted_day: int):
        if not self.crop:
            self.crop = CropInstance(crop_data, planted_day, self)
            return True
        return False

    def clear_field(self):
        self.crop = None

    def status(self):
        if self.crop:
            return self.crop.status()
        else:
            npk_str = f"N: {self.soil_npk['N']:.1f}, P: {self.soil_npk['P']:.1f}, K: {self.soil_npk['K']:.1f}"
            return f"（空地）\n土壤养分: {npk_str}"

class CropInstance:
    def __init__(self, crop_data: CropData, planted_day: int, field: Field):
        self.crop_data = crop_data
        self.field = field
        self.planted_day = planted_day
        
        self.day_counter = 0
        self.hour_counter = 0
        self.growth_points = 0.0
        
        self.matured = False
        self.dead = False
        self.harvested = False
        
        self.health = 100.0
        self.water_level = 100.0
        self.sun_stress = 0.0
        self.nutrient_satisfaction = {'N': 0.0, 'P': 0.0, 'K': 0.0, 'total_days': 0}
        self.quality_tags = set()
        
        self.pesticide_effect_hours = 0
        self.damage_reasons = set()
        self.total_cost = crop_data.cost_per_mu

    def update_hourly(self, weather_hour):
        if self.dead or self.harvested:
            return

        self._update_counters()
        self._update_water_level(weather_hour)
        self._update_sun_stress(weather_hour)
        self._update_health(weather_hour)

        if self.pesticide_effect_hours > 0:
            self.pesticide_effect_hours -= 1

        if self.health <= 0:
            self.dead = True

    def _update_counters(self):
        self.hour_counter += 1
        if self.hour_counter % 24 == 0:
            self.day_counter += 1
            self._daily_nutrient_update()
            self.check_maturity()
            self.check_disease()

    def _daily_nutrient_update(self):
        """Handles daily nutrient uptake and growth point calculation."""
        pref_n, pref_p, pref_k = self.crop_data.npk_preference
        total_pref = pref_n + pref_p + pref_k
        
        # Ideal uptake for each nutrient
        ideal_uptake = {
            'N': self.crop_data.npk_uptake * (pref_n / total_pref),
            'P': self.crop_data.npk_uptake * (pref_p / total_pref),
            'K': self.crop_data.npk_uptake * (pref_k / total_pref)
        }

        # Actual uptake from soil
        actual_uptake = {
            'N': min(ideal_uptake['N'], self.field.soil_npk['N']),
            'P': min(ideal_uptake['P'], self.field.soil_npk['P']),
            'K': min(ideal_uptake['K'], self.field.soil_npk['K'])
        }

        # Consume nutrients from soil
        for nutrient, value in actual_uptake.items():
            self.field.soil_npk[nutrient] -= value

        # Calculate satisfaction (0-1 scale for the day)
        daily_satisfaction = sum(actual_uptake.values()) / sum(ideal_uptake.values())
        
        # Update total satisfaction
        self.nutrient_satisfaction['total_days'] += 1
        for nutrient in 'NPK':
            satisfaction_ratio = actual_uptake[nutrient] / ideal_uptake[nutrient] if ideal_uptake[nutrient] > 0 else 1
            self.nutrient_satisfaction[nutrient] += satisfaction_ratio

        # Update growth points based on satisfaction
        self.growth_points += daily_satisfaction # If satisfaction is 1, grows 1 day. If 0.5, grows 0.5 day.

        # Special Traits (e.g., Nitrogen Fixation for Soybeans)
        if self.crop_data.special_trait == 'nitrogen_fixer':
            self.field.soil_npk['N'] += 0.5 # Soybeans fix some nitrogen back into the soil

    def _update_water_level(self, weather_hour):
        hourly_consumption = self.crop_data.water_need / 24
        evaporation = (weather_hour.current_sunlight / 10) * (max(0, weather_hour.current_temperature - 10) / 20)
        self.water_level -= (hourly_consumption + evaporation)
        
        if weather_hour.current_rainfall > 0:
            self.water_level += weather_hour.current_rainfall * 2
            self.damage_reasons.discard("缺水")

        self.water_level = max(0, min(120, self.water_level))

    def _update_sun_stress(self, weather_hour):
        sun_intensity = weather_hour.current_sunlight
        if sun_intensity <= 1.0:
            self.sun_stress = max(0, self.sun_stress - 1)
            self.damage_reasons.discard("光照")
            return

        ideal_sun, tolerance = self.crop_data.sun_preference
        if not (ideal_sun - tolerance <= sun_intensity <= ideal_sun + tolerance):
            self.sun_stress += 2
            self.damage_reasons.add("光照")
        else:
            self.sun_stress = max(0, self.sun_stress - 1)
            self.damage_reasons.discard("光照")
        self.sun_stress = min(100, self.sun_stress)

    def _update_health(self, weather_hour):
        # Reset damage flags that can recover
        self.damage_reasons.discard("养分")

        # Nutrient damage
        avg_satisfaction = self.growth_points / self.day_counter if self.day_counter > 0 else 1
        if avg_satisfaction < 0.6:
            self.health -= (0.6 - avg_satisfaction) * 5
            self.damage_reasons.add("养分")

        # Water damage
        if self.water_level < 30:
            self.health -= (30 - self.water_level) * 0.1
            self.damage_reasons.add("缺水")
        elif self.water_level > 115:
            self.health -= (self.water_level - 115) * 0.2
            self.damage_reasons.add("积水")

        # Other damages...
        min_temp, max_temp = self.crop_data.temp_range
        if not (min_temp <= weather_hour.current_temperature <= max_temp):
            self.health -= 0.5
            self.damage_reasons.add("温度")

        if not self.damage_reasons:
            self.health = min(100, self.health + 0.2)

        self.health = max(0, self.health)

    def check_maturity(self):
        if not self.matured and self.growth_points >= self.crop_data.grow_days:
            self.matured = True
            self._finalize_quality_tags()

    def _finalize_quality_tags(self):
        """Check nutrient satisfaction at maturity to award quality tags."""
        total_days = self.nutrient_satisfaction['total_days']
        if total_days == 0: return

        for nutrient, tag in self.crop_data.quality_tags.items():
            avg_satisfaction = self.nutrient_satisfaction[nutrient] / total_days
            if avg_satisfaction >= 0.9:
                self.quality_tags.add(tag)

    def check_disease(self):
        disease_chance = self.crop_data.disease_chance
        if self.pesticide_effect_hours > 0:
            disease_chance *= 0.1
        if random.random() < disease_chance:
            self.health -= 10
            self.damage_reasons.add("病害")

    def apply_manual_action(self, action, value=0):
        if action == "water":
            self.water_level = min(120, self.water_level + 30)
            self.damage_reasons.discard("缺水")
        elif action == "pesticide":
            self.pesticide_effect_hours = 48
            self.damage_reasons.discard("病害")
            self.total_cost += 120

    def harvest(self):
        if not self.matured or self.dead or self.harvested:
            return None

        self.harvested = True
        
        # Yield is affected by overall nutrient satisfaction
        total_days = self.nutrient_satisfaction['total_days']
        avg_satisfaction = sum(self.nutrient_satisfaction[n] for n in 'NPK') / (total_days * 3) if total_days > 0 else 0
        yield_modifier = 0.2 + (avg_satisfaction * 0.8) # Base 20% yield, max 100%
        yield_final = round(self.crop_data.yield_per_mu * yield_modifier, 1)

        # Nutrition is based on final health
        nutrition = round(self.health, 1)

        return {
            "name": self.crop_data.name,
            "yield": yield_final,
            "nutrition": nutrition,
            "freshness": 100.0,
            "cost": self.total_cost,
            "quality_tags": list(self.quality_tags)
        }

    def status(self):
        crop = self.crop_data
        if self.dead:
            return f"{crop.name} | ❌ 已死亡 (原因: {', '.join(self.damage_reasons)})"
        if self.harvested:
            tags = f" ({', '.join(self.quality_tags)})" if self.quality_tags else ""
            return f"{crop.name} | 🎉 已收获{tags}"
        
        status_str = f"{crop.name} | {self.day_counter}天 | {'✅成熟' if self.matured else '🌱生长中'} ({self.growth_points:.1f}/{crop.grow_days})\n"
        status_str += f"健康: {self.health:.1f}% | 水分: {self.water_level:.1f}%\n"
        
        if self.damage_reasons:
            status_str += f"⚠受损({', '.join(self.damage_reasons)})\n"
        
        npk_str = f"土: N:{self.field.soil_npk['N']:.1f} P:{self.field.soil_npk['P']:.1f} K:{self.field.soil_npk['K']:.1f}"
        status_str += npk_str
        return status_str
