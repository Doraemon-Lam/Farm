# crops.py（重构版）

import random

class CropType:
    def __init__(self, name, grow_days, temp_range, drought_tolerance, 
                 cost_per_mu, yield_per_mu, disease_chance, 
                 water_need, sun_preference):
        self.name = name
        self.grow_days = grow_days
        self.temp_range = temp_range
        self.drought_tolerance = drought_tolerance  # (0-1), a factor for reducing water damage
        self.cost_per_mu = cost_per_mu
        self.yield_per_mu = yield_per_mu
        self.disease_chance = disease_chance  # Daily chance of disease
        self.water_need = water_need  # Base water consumption per day (mm)
        self.sun_preference = sun_preference  # Tuple (ideal_intensity, tolerance_range)

    def description(self):
        return (f"{self.name} | 生长周期: {self.grow_days}天 | 适宜温度: {self.temp_range[0]}-{self.temp_range[1]}℃ | "
                f"抗旱性: {self.drought_tolerance} | 需水量: {self.water_need}mm/天 | "
                f"喜光: {self.sun_preference[0]}±{self.sun_preference[1]}")


class CropInstance:
    def __init__(self, crop_type: CropType, planted_day: int):
        self.crop_type = crop_type
        self.day_counter = 0
        self.hour_counter = 0
        self.planted_day = planted_day
        
        self.matured = False
        self.dead = False
        self.harvested = False
        
        self.health = 100.0  # (0-100)
        self.water_level = 100.0  # (0-100) percentage
        self.sun_stress = 0.0  # (0-100)
        self.nutrition = 0.0 # Final nutrition value
        self.freshness = 100.0
        self.days_since_harvest = 0
        
        self.pesticide_effect_hours = 0
        self.damage_reasons = set()

    def update_hourly(self, weather_hour):
        if self.dead or self.harvested:
            return

        self.hour_counter += 1
        if self.hour_counter % 24 == 0:
            self.day_counter += 1
            self.check_maturity()
            # Daily disease check
            self.check_disease()

        # 1. Water Level Update
        # Evaporation/Consumption: increases with sun and temp, decreases with rain
        hourly_consumption = self.crop_type.water_need / 24
        evaporation = (weather_hour.current_sunlight / 10) * (max(0, weather_hour.current_temperature - 10) / 20)
        self.water_level -= (hourly_consumption + evaporation)
        
        # Rainfall bonus
        if weather_hour.current_rainfall > 0:
            self.water_level += weather_hour.current_rainfall * 2 # Rainfall is more effective
            self.damage_reasons.discard("缺水")

        self.water_level = max(0, min(120, self.water_level)) # Can be over 100

        # 2. Sunlight Stress Update
        ideal_sun, tolerance = self.crop_type.sun_preference
        sun_intensity = weather_hour.current_sunlight
        if not (ideal_sun - tolerance <= sun_intensity <= ideal_sun + tolerance):
            self.sun_stress += 2  # Stress accumulates faster
            self.damage_reasons.add("光照")
        else:
            self.sun_stress = max(0, self.sun_stress - 1) # Stress recovers slowly
            self.damage_reasons.discard("光照")
        self.sun_stress = min(100, self.sun_stress)

        # 3. Health Update based on status
        # Water damage
        water_damage_threshold = 30 * (1 + self.crop_type.drought_tolerance) # Drought tolerance helps
        if self.water_level < water_damage_threshold:
            self.health -= (water_damage_threshold - self.water_level) * 0.1
            self.damage_reasons.add("缺水")
        elif self.water_level > 115: # Overwatering
            self.health -= (self.water_level - 115) * 0.2
            self.damage_reasons.add("积水")
        else:
            self.damage_reasons.discard("缺水")
            self.damage_reasons.discard("积水")

        # Sun stress damage
        if self.sun_stress > 50:
            self.health -= (self.sun_stress - 50) * 0.05
            self.damage_reasons.add("光照")

        # Temperature damage
        min_temp, max_temp = self.crop_type.temp_range
        if not (min_temp <= weather_hour.current_temperature <= max_temp):
            self.health -= 0.5
            self.damage_reasons.add("温度")
        else:
            self.damage_reasons.discard("温度")
            
        # Extreme weather damage
        if weather_hour.extreme_event:
            self.health -= 5
            self.damage_reasons.add("极端天气")
        else:
            self.damage_reasons.discard("极端天气")

        # Pesticide effect countdown
        if self.pesticide_effect_hours > 0:
            self.pesticide_effect_hours -= 1

        # Health recovery if conditions are good
        if not self.damage_reasons:
            self.health = min(100, self.health + 0.2)

        self.health = max(0, self.health)
        if self.health == 0:
            self.dead = True

    def check_maturity(self):
        if not self.matured and self.day_counter >= self.crop_type.grow_days:
            self.matured = True

    def check_disease(self):
        disease_chance = self.crop_type.disease_chance
        if self.pesticide_effect_hours > 0:
            disease_chance *= 0.1  # Pesticide reduces chance by 90%
        
        if random.random() < disease_chance:
            self.health -= 10
            self.damage_reasons.add("病害")

    def apply_manual_action(self, action, value=0):
        if action == "water":
            self.water_level += 30 # A full watering
            self.water_level = min(120, self.water_level)
            self.damage_reasons.discard("缺水")
        elif action == "fertilize":
            # Fertilizing can boost health recovery or nutrition
            self.health = min(100, self.health + 5)
        elif action == "pesticide":
            self.pesticide_effect_hours = 48 # Effective for 48 hours (2 days)
            self.damage_reasons.discard("病害")

    def harvest(self):
        if not self.matured or self.dead or self.harvested:
            return None

        self.harvested = True
        
        # Yield is affected by final health
        yield_modifier = self.health / 100.0
        yield_final = round(self.crop_type.yield_per_mu * yield_modifier, 1)

        # Nutrition is also based on health
        self.nutrition = round(self.health, 1)

        return {
            "name": self.crop_type.name,
            "yield": yield_final,
            "nutrition": self.nutrition,
            "freshness": self.freshness
        }

    def update_freshness(self):
        if self.harvested and self.freshness > 0:
            self.days_since_harvest += 1
            decay = 10 / (self.days_since_harvest + 2)
            self.freshness = max(0.0, self.freshness - decay)

    def status(self):
        crop = self.crop_type
        if self.dead:
            return f"{crop.name} | ❌ 已死亡 (原因: {', '.join(self.damage_reasons)})"
        if self.harvested:
            return f"{crop.name} | 🎉 已收获 | 营养值: {self.nutrition} | 新鲜度: {self.freshness:.1f}%"
        
        status_str = f"{crop.name} | 第 {self.day_counter}/{crop.grow_days} 天 | {'✅成熟' if self.matured else '🌱生长中'} | "
        status_str += f"健康: {self.health:.1f}% | 水分: {self.water_level:.1f}%"
        
        if self.damage_reasons:
            status_str += f" | ⚠受损({', '.join(self.damage_reasons)})"
        
        return status_str


def get_default_crop_types():
    # Added water_need (mm/day) and sun_preference (ideal_intensity, tolerance)
    return {
        "小麦": CropType("小麦", 9, (10, 25), 0.6, 300, 350, 0.01, 3, (6, 3)),
        "玉米": CropType("玉米", 10, (15, 30), 0.4, 320, 400, 0.02, 5, (7, 2)),
        "番茄": CropType("番茄", 7, (18, 28), 0.3, 350, 300, 0.05, 6, (8, 2)),
        "大米": CropType("大米", 11, (20, 32), 0.1, 360, 380, 0.03, 10, (6, 3)),
        "大豆": CropType("大豆", 9, (16, 30), 0.5, 300, 360, 0.01, 4, (7, 3)),
        "草莓": CropType("草莓", 6, (16, 26), 0.3, 400, 180, 0.06, 5, (5, 2)),
        "辣椒": CropType("辣椒", 8, (20, 32), 0.3, 350, 260, 0.04, 5, (8, 2)),
        "黄瓜": CropType("黄瓜", 6, (18, 30), 0.4, 320, 240, 0.03, 7, (6, 3)),
        "葡萄": CropType("葡萄", 10, (15, 28), 0.4, 450, 300, 0.05, 4, (8, 2)),
    }
