# plant.py

class CropData:
    def __init__(self, name, grow_days, temp_range, drought_tolerance, 
                 cost_per_mu, yield_per_mu, disease_chance, 
                 water_need, sun_preference, 
                 npk_preference, npk_uptake, quality_tags, special_trait=None):
        self.name = name
        self.grow_days = grow_days
        self.temp_range = temp_range
        self.drought_tolerance = drought_tolerance
        self.cost_per_mu = cost_per_mu
        self.yield_per_mu = yield_per_mu
        self.disease_chance = disease_chance
        self.water_need = water_need
        self.sun_preference = sun_preference
        # N-P-K System
        self.npk_preference = npk_preference  # Tuple (N, P, K) ratio, e.g., (3, 1, 2)
        self.npk_uptake = npk_uptake          # Base total nutrient uptake per day
        self.quality_tags = quality_tags      # Dict mapping nutrient to quality tag, e.g., {'N': '高蛋白质'}
        self.special_trait = special_trait    # e.g., 'nitrogen_fixer'

    def description(self):
        return (
            f"{self.name} | 生长周期: {self.grow_days}天 | 适宜温度: {self.temp_range[0]}-{self.temp_range[1]}℃ | "
            f"成本: ￥{self.cost_per_mu}/亩 | 基础产量: {self.yield_per_mu}kg/亩\n"
            f"NPK偏好: {self.npk_preference[0]}:{self.npk_preference[1]}:{self.npk_preference[2]} | "
            f"每日需水: {self.water_need}mm | 喜光: {self.sun_preference[0]}±{self.sun_preference[1]}"
        )

def get_all_crop_data():
    """Returns a dictionary of all available crop data."""
    return {
        # Ratios are simplified for gameplay. Uptake is a value representing daily consumption.
        "小麦": CropData("小麦", 9, (10, 25), 0.6, 300, 350, 0.01, 3, (6, 3), 
                       npk_preference=(4, 2, 1), npk_uptake=2.0, quality_tags={'N': '高筋'}),
        
        "玉米": CropData("玉米", 10, (15, 30), 0.4, 320, 400, 0.02, 5, (7, 2), 
                       npk_preference=(5, 2, 2), npk_uptake=2.5, quality_tags={'N': '高蛋白'}),
        
        "番茄": CropData("番茄", 7, (18, 28), 0.3, 350, 300, 0.05, 6, (8, 2), 
                       npk_preference=(3, 2, 5), npk_uptake=2.2, quality_tags={'K': '高糖分'}),
        
        "大米": CropData("大米", 11, (20, 32), 0.1, 360, 380, 0.03, 10, (6, 3), 
                       npk_preference=(4, 2, 3), npk_uptake=2.8, quality_tags={'N': '优质'}),
        
        "大豆": CropData("大豆", 9, (16, 30), 0.5, 300, 360, 0.01, 4, (7, 3), 
                       npk_preference=(2, 4, 3), npk_uptake=2.0, quality_tags={'N': '高蛋白'}, special_trait='nitrogen_fixer'),
        
        "草莓": CropData("草莓", 6, (16, 26), 0.3, 400, 180, 0.06, 5, (5, 2), 
                       npk_preference=(2, 3, 4), npk_uptake=1.8, quality_tags={'K': '高糖分'}),
        
        "辣椒": CropData("辣椒", 8, (20, 32), 0.3, 350, 260, 0.04, 5, (8, 2), 
                       npk_preference=(3, 2, 4), npk_uptake=2.1, quality_tags={'K': '香辣'}),
        
        "黄瓜": CropData("黄瓜", 6, (18, 30), 0.4, 320, 240, 0.03, 7, (6, 3), 
                       npk_preference=(2, 3, 6), npk_uptake=2.3, quality_tags={'P': '清脆'}),
        
        "葡萄": CropData("葡萄", 10, (15, 28), 0.4, 450, 300, 0.05, 4, (8, 2), 
                       npk_preference=(2, 2, 5), npk_uptake=2.6, quality_tags={'K': '高糖分'}),
    }

