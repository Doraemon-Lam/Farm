import random

class Storage:
    def __init__(self):
        self.stock = []

    def add_crop(self, crop_info):
        self.stock.append({
            "name": crop_info["name"],
            "yield": crop_info["yield"],
            "nutrition": crop_info["nutrition"],
            "freshness": crop_info["freshness"],
            "cost": crop_info.get("cost", 0), # Get cost, default to 0 if not present
            "days": 0
        })

    def update_all(self, storage_cost_per_crop=2.0):
        total_cost = 0
        for crop in self.stock:
            crop['days'] += 1
            # 更加平滑的腐烂曲线，初期腐烂较慢
            decay_factor = 0.5 + (crop['days'] / 30) # 腐烂速度随时间增加
            decay = random.uniform(0.8, 1.2) * decay_factor
            crop['freshness'] = max(0.0, crop['freshness'] - decay)
            total_cost += storage_cost_per_crop
        return round(total_cost, 2)

    def sell_crop(self, index, market_price, quality_bonus=1.0):
        if index < 0 or index >= len(self.stock):
            return None, 0.0
        crop = self.stock.pop(index)
        multiplier = (crop['nutrition'] * 0.5 + crop['freshness'] * 0.5) / 100
        final_price = round(crop['yield'] * market_price * multiplier * quality_bonus, 2)
        return crop['name'], final_price

    def list_storage(self):
        if not self.stock:
            print("📦 仓库为空")
            return
        for i, crop in enumerate(self.stock):
            print(f"{i + 1}. {crop['name']} | 营养值: {crop['nutrition']} | 新鲜度: {crop['freshness']:.1f}% | 重量: {crop['yield']}kg")