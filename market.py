# market.py

import random

class Product:
    def __init__(self, name, base_price, min_price, max_price, unit):
        self.name = name
        self.base_price = base_price
        self.min_price = min_price
        self.max_price = max_price
        self.unit = unit
        self.price = base_price

    def update_price(self, weather=None):
        # 基础波动 ±5%
        change_rate = random.uniform(-0.05, 0.05)

        # 天气影响
        if weather:
            if weather.rainfall > 20:
                if self.name in ["小麦", "玉米", "草莓", "番茄", "大豆", "大米", "辣椒"]:
                    change_rate += 0.03  # 降雨致减产 → 提价
            if weather.extreme_event:
                change_rate += 0.05

        new_price = self.price * (1 + change_rate)
        self.price = round(min(max(new_price, self.min_price), self.max_price), 2)

    def info(self):
        return f"{self.name}: ￥{self.price}/{self.unit}"


class Market:
    def __init__(self):
        self.products = []
        self.init_products()

    def init_products(self):
        self.products = [
            Product("小麦", 2.0, 1.5, 2.5, "公斤"),
            Product("玉米", 2.2, 1.6, 2.8, "公斤"),
            Product("大米", 2.6, 2.0, 3.2, "公斤"),
            Product("大豆", 3.1, 2.4, 4.0, "公斤"),
            Product("草莓", 10.0, 6.0, 15.0, "公斤"),
            Product("番茄", 3.5, 2.5, 4.8, "公斤"),
            Product("辣椒", 6.5, 4.5, 8.5, "公斤"),
            Product("苹果", 4.0, 3.0, 5.5, "公斤"),
            Product("黄瓜", 3.2, 2.2, 4.5, "公斤"),
            Product("葡萄", 6.0, 4.0, 8.0, "公斤"),
            Product("鸡蛋", 5.0, 3.8, 6.5, "公斤"),
            Product("牛奶", 4.2, 3.5, 5.0, "公斤"),
            Product("猪肉", 24.0, 18.0, 32.0, "公斤")
        ]

    def update_prices(self, weather=None):
        for product in self.products:
            product.update_price(weather)

    def print_market_summary(self):
        print("📊 今日市场价格（元/公斤）：")
        for product in self.products:
            print("  -", product.info())

    def get_price(self, name):
        for product in self.products:
            if product.name == name:
                return product.price
        return None
