# weather.py （添加分钟级更新）

import random
from datetime import datetime, timedelta

class Weather:
    def __init__(self, date: datetime):
        self.date = date
        self.season = self._get_season(date.month)
        self.temperature = None
        self.rainfall = None
        self.sunshine_hours = None
        self.wind_speed = None
        self.extreme_event = None
        self.generate_weather()

    def _get_season(self, month):
        if month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        elif month in [9, 10, 11]:
            return "Autumn"
        else:
            return "Winter"

    def generate_weather(self):
        # 月平均温度范围（北京）
        month_temp = {
            1: (-3, 4),  2: (0, 8),   3: (4, 14),
            4: (10, 20), 5: (15, 25), 6: (20, 30),
            7: (24, 34), 8: (22, 32), 9: (16, 26),
            10: (10, 20), 11: (2, 12), 12: (-2, 6)
        }
        self.temperature = round(random.uniform(*month_temp[self.date.month]), 1)

        # 降水（毫米）
        # 月降水概率 & 降水强度范围（单位 mm）
        month_rain = {
            1: (0.1, (1, 8)),   2: (0.15, (1, 10)), 3: (0.25, (1, 15)),
            4: (0.35, (3, 20)), 5: (0.45, (5, 25)), 6: (0.6, (8, 35)),
            7: (0.65, (10, 40)),8: (0.55, (8, 30)), 9: (0.4, (5, 20)),
            10: (0.2, (2, 12)), 11: (0.1, (1, 6)),  12: (0.05, (1, 5))
        }
        rain_chance, rain_range = month_rain[self.date.month]
        self.rainfall = round(random.uniform(*rain_range), 1) if random.random() < rain_chance else 0.0

        # 日照时长（小时）
        month_sunlight = {
            1: (3, 6),   2: (4, 7),   3: (5, 8),
            4: (6, 9),   5: (7, 10),  6: (7.5, 11),
            7: (7, 10.5),8: (6.5, 10),9: (6, 9),
            10: (5, 8),  11: (4, 7),  12: (3, 6)
        }
        self.sunshine_hours = round(random.uniform(*month_sunlight[self.date.month]), 1)

        # 风速（m/s）
        self.wind_speed = round(random.uniform(0.5, 6.0), 1)

        # 极端天气事件
        self.extreme_event = self._generate_extreme_event()

    def _generate_extreme_event(self):
        chance = random.random()
        if self.season == "Summer" and chance < 0.05:
            return "Thunderstorm"
        elif self.season == "Winter" and chance < 0.03 and self.temperature < 0:
            return "Snowstorm"
        elif self.season == "Spring" and chance < 0.02:
            return "Strong Wind"
        return None

    def summary(self):
        summary_text = (
            f"[{self.date.strftime('%Y-%m-%d')} | {self.season}] "
            f"🌡温度: {self.temperature}℃ | ☔ 降水: {self.rainfall}mm | ☀ 日照: {self.sunshine_hours}h | "
            f"💨风速: {self.wind_speed}m/s"
        )
        if self.extreme_event:
            summary_text += f" | ⚠ 极端天气: {self.extreme_event}"
        return summary_text
    
## 分钟级更新

class WeatherDynamic:
    def __init__(self, date: datetime):
        self.date = date
        self.time = datetime(date.year, date.month, date.day, 0, 0)
        self.current_temperature = None
        self.current_rainfall = 0.0
        self.current_sunlight = 0.0
        self.current_wind = 0.0
        self.extreme_event = None
        self.rainfall_today = 0.0

        self.daily_temperature_curve = self._generate_daily_temperature_curve()
        self._generate_daily_weather_base()

    @property
    def rainfall(self):
        return self.rainfall_today

    def _generate_daily_temperature_curve(self):
        # 模拟一天内 24 小时的温度曲线（贝尔状）
        month_temp = {
            1: (-3, 4),  2: (0, 8),   3: (4, 14),
            4: (10, 20), 5: (15, 25), 6: (20, 30),
            7: (24, 34), 8: (22, 32), 9: (16, 26),
            10: (10, 20), 11: (2, 12), 12: (-2, 6)
        }
        low, high = month_temp[self.date.month]
        midday = random.uniform((high + low) / 2, high)
        midnight = random.uniform(low, (high + low) / 2)

        # 返回一个 24 小时温度表
        curve = []
        for hour in range(24):
            if 6 <= hour <= 18:
                factor = (1 - abs(hour - 12) / 6)
            else:
                factor = 0
            temp = midnight + (midday - midnight) * factor
            curve.append(round(temp + random.uniform(-0.3, 0.3), 1))
        return curve

    def _generate_daily_weather_base(self):
        # 每天决定降雨概率
        month_rain = {
            1: (0.1, (1, 8)),  2: (0.15, (1, 10)), 3: (0.25, (1, 15)),
            4: (0.35, (3, 20)),5: (0.45, (5, 25)), 6: (0.6, (8, 35)),
            7: (0.65, (10, 40)),8: (0.55, (8, 30)),9: (0.4, (5, 20)),
            10: (0.2, (2, 12)),11: (0.1, (1, 6)),  12: (0.05, (1, 5))
        }
        chance, rain_range = month_rain[self.date.month]
        self.rainfall_today = round(random.uniform(*rain_range), 1) if random.random() < chance else 0.0

        # 降雨时间段（若下雨）
        self.rain_start = random.randint(0, 20) if self.rainfall_today > 0 else None
        self.rain_duration = random.randint(1, 4) if self.rainfall_today > 0 else 0

        # 极端天气
        month = self.date.month
        extreme = None
        if month in [6, 7, 8] and random.random() < 0.05:
            extreme = "Thunderstorm"
        elif month in [12, 1, 2] and random.random() < 0.03:
            extreme = "Snowstorm"
        elif month in [3, 4] and random.random() < 0.02:
            extreme = "Strong Wind"
        self.extreme_event = extreme

    def start_new_day(self, date):
        self.date = date
        self.time = datetime(date.year, date.month, date.day, 0, 0)
        self.daily_temperature_curve = self._generate_daily_temperature_curve()
        self._generate_daily_weather_base()

    def update_hour(self):
        hour = self.time.hour
        self.current_temperature = self.daily_temperature_curve[hour]
        self.current_wind = round(random.uniform(0.5, 5.0), 1)

        # 降水模拟
        if self.rain_start is not None and self.rain_start <= hour < self.rain_start + self.rain_duration:
            self.current_rainfall = round(self.rainfall_today / self.rain_duration, 1)
        else:
            self.current_rainfall = 0.0

        # 日照强度
        if 6 <= hour <= 18:
            base_sunlight = (1 - abs(hour - 12) / 6) * 10
            noisy_sunlight = base_sunlight + random.uniform(-1, 1)
            self.current_sunlight = round(max(0, noisy_sunlight), 1)
        else:
            self.current_sunlight = 0.0

        self.time += timedelta(hours=1)

    def summary(self):
        return (
            f"[{self.time.strftime('%H:%M')}] 🌡{self.current_temperature}℃ | ☔{self.current_rainfall}mm | "
            f"☀ 日照: {self.current_sunlight} | 💨风速: {self.current_wind}m/s"
            + (f" | ⚠ {self.extreme_event}" if self.extreme_event else "")
        )

    def is_new_day(self):
        return self.time.hour == 0 and self.time.minute == 0
