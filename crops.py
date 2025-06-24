# crops.py（更新版）

from weather import Weather

class CropType:
    def __init__(self, name, grow_days, temp_range, drought_tolerance, cost_per_mu, yield_per_mu, disease_chance):
        self.name = name
        self.grow_days = grow_days
        self.temp_range = temp_range
        self.drought_tolerance = drought_tolerance
        self.cost_per_mu = cost_per_mu
        self.yield_per_mu = yield_per_mu
        self.disease_chance = disease_chance  # 每天发病几率（0~1）


class CropInstance:
    def __init__(self, crop_type: CropType, planted_day: int):
        self.crop_type = crop_type
        self.day_counter = 0
        self.planted_day = planted_day
        self.matured = False
        self.healthy = True
        self.dead = False
        self.consecutive_unhealthy_days = 0

        self.watered_today = False
        self.fertilized_today = False
        self.pesticide_today = False
        self.total_water = 0
        self.total_fertilizer = 0
        self.total_sun = 0.0
        self.pesticide_effect = 0  # 连续有效天数

        self.harvested = False
        self.nutrition = None
        self.freshness = 100.0
        self.days_since_harvest = 0
        
    ## 替换成分钟级生长逻辑
    def absorb_weather(self, weather_minute):
        self.total_sun += weather_minute.current_sunlight / 60.0
        if weather_minute.current_rainfall > 0:
            self.total_water += weather_minute.current_rainfall / 24


    def update_one_day(self, weather_minute: Weather):
        import random
        if self.dead or self.harvested:
            return

        self.day_counter += 1
        
        # 天气判断来自前一天的累计数据
        min_temp, max_temp = self.crop_type.temp_range
        healthy_today = True
        
        avg_temp = self.total_sun / self.day_counter # 用日照强度近似生长温度判断
        if avg_temp < min_temp or avg_temp > max_temp:
            healthy_today = False
            
        # 土壤水分判断 (以每日总水为单位，粗略处理)
        water_ratio = self.total_water / self.day_counter
        if water_ratio < 0.5 and not self.watered_today and self.crop_type.drought_tolerance < 0.5:
            healthy_today = False
            
        # 极端天气
        if weather_minute.extreme_event in ["Thunderstorm", "Snowstorm", "Strong Wind"]:
            healthy_today = False
            
        # 病害
        disease_chance = self.crop_type.disease_chance
        if self.pesticide_effect > 0:
            disease_chance *= 0.1  # 农药降低90%
            self.pesticide_effect -= 1
            
        if random.random() < disease_chance:
            healthy_today = False
            print(f"⚠ {self.crop_type.name} 出现病害！")

        if not healthy_today:
            self.consecutive_unhealthy_days += 1
            if self.consecutive_unhealthy_days >= 3:
                self.dead = True
                return
            self.healthy = False
        else:
            self.consecutive_unhealthy_days = 0
            self.healthy = True

        # 状态清理
        if self.watered_today:
            self.total_water += 1
        if self.fertilized_today:
            self.total_fertilizer += 1
        if self.pesticide_today:
            self.pesticide_effect = 2  # 农药效果持续2天

        self.watered_today = False
        self.fertilized_today = False
        self.pesticide_today = False

    def harvest(self):
        if not self.matured or self.dead or self.harvested:
            return None

        self.harvested = True

        fertilizer_bonus = min(self.total_fertilizer * 0.02, 0.2)
        yield_final = round(self.crop_type.yield_per_mu * (1 + fertilizer_bonus), 1)

        water_ratio = self.total_water / self.crop_type.grow_days
        water_penalty = 0.2 if (water_ratio > 1.2 or water_ratio < 0.5) else 0.0
        avg_sun = self.total_sun / self.crop_type.grow_days
        nutrition_base = 100 * (1 - water_penalty) * (avg_sun / 10)
        nutrition = round(min(nutrition_base + self.total_fertilizer * 1.0, 100), 1)
        self.nutrition = nutrition

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
            return f"{crop.name} | ❌ 已死亡"
        if self.harvested:
            return f"{crop.name} | 🎉 已收获 | 营养值: {self.nutrition} | 新鲜度: {self.freshness:.1f}%"
        return (f"{crop.name} | 第 {self.day_counter}/{crop.grow_days} 天 | "
                f"{'✅成熟' if self.matured else '🌱生长中'} | "
                f"{'🟢健康' if self.healthy else '⚠ 受损'}")


def get_default_crop_types():
    return {
        "小麦": CropType("小麦", 9, (10, 25), 0.5, 300, 350, 0.01),
        "玉米": CropType("玉米", 10, (15, 30), 0.4, 320, 400, 0.02),
        "番茄": CropType("番茄", 7, (18, 28), 0.3, 350, 300, 0.05),
        "大米": CropType("大米", 11, (20, 32), 0.2, 360, 380, 0.03),
        "大豆": CropType("大豆", 9, (16, 30), 0.5, 300, 360, 0.01),
        "草莓": CropType("草莓", 6, (16, 26), 0.3, 400, 180, 0.06),
        "辣椒": CropType("辣椒", 8, (20, 32), 0.3, 350, 260, 0.04),
        "黄瓜": CropType("黄瓜", 6, (18, 30), 0.4, 320, 240, 0.03),
        "葡萄": CropType("葡萄", 10, (15, 28), 0.4, 450, 300, 0.05),
    }
