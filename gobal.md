# FarmerSimPy - 简约农民模拟器 项目结构草案

# 📁 项目文件结构
.
├── main.py                     # 游戏主循环
├── config.py                   # 游戏配置（初始资金、API密钥、本地参数）
├── weather.py                  # 实时天气接口模块 ✅ 已实现
├── market.py                   # 农产品价格获取与管理
├── crops.py                    # 作物类与作物库 ✅ 已实现
├── farm.py                     # 农田/田块状态与操作逻辑 ✅ 已实现
├── economy.py                  # 经济系统（账本、贷款、收入、支出）
├── game_state.py               # 存档/读档管理
├── events.py                   # 随机事件（虫害、旱灾等）
├── utils.py                    # 通用工具函数（如时间推进、界面打印）
├── data/
│   ├── crop_data.json          # 作物数据库
│   ├── market_price.json       # 模拟或历史价格数据
│   └── savegame.json           # 存档文件
└── requirements.txt            # 所需依赖库列表

# ✅ 核心模块简要说明

## main.py
- 初始化游戏
- 读取配置与接口密钥
- 启动每日/每周循环：天气 → 决策输入 → 田地更新 → 市场结算

## config.py
```python
STARTING_FUNDS = 100000
LOCATION = "Beijing"
TIME_STEP = "daily"  # 或 "weekly"
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_KEY"
PRICE_API_SOURCE = "simulated"  # 或 "real"
```

## weather.py ✅
```python
import requests

class Weather:
    def __init__(self, api_key, location="Beijing"):
        self.api_key = api_key
        self.location = location

    def get_weather(self):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={self.location}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        weather = {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": data["weather"][0]["description"]
        }
        return weather
```

## market.py
- 可选两种模式：
  1. **模拟模式**：使用历史价格波动规则（波动幅度、随机因子）
  2. **实时模式**：可从以下网站/API中爬取或抓取：
     - FAOSTAT: [https://www.fao.org/faostat/](https://www.fao.org/faostat/)
     - IndexMundi（部分 API）：[https://www.indexmundi.com/commodities/](https://www.indexmundi.com/commodities/)
     - 国内批发价可模拟来自中农网、菜价网
- 支持价格缓存与趋势输出

## crops.py ✅
```python
class Crop:
    def __init__(self, name, grow_days, temp_range, water_need, season, seed_cost, yield_per_mu):
        self.name = name
        self.grow_days = grow_days
        self.temp_range = temp_range  # tuple (min_temp, max_temp)
        self.water_need = water_need  # 高/中/低
        self.season = season          # 春、夏、秋、冬
        self.seed_cost = seed_cost
        self.yield_per_mu = yield_per_mu

# 示例作物库
crop_library = [
    Crop("小麦", 120, (10, 25), "中", "春", 300, 400),
    Crop("玉米", 90, (15, 30), "高", "夏", 350, 500),
    Crop("番茄", 100, (18, 28), "高", "春", 500, 300),
    Crop("苹果", 180, (5, 20), "秋", 800, 600)
]
```

## farm.py ✅
```python
class Farmland:
    def __init__(self, id, area_mu):
        self.id = id
        self.area_mu = area_mu
        self.crop = None
        self.days_grown = 0
        self.status = "空地"  # 空地、已播种、可收获

    def plant(self, crop):
        self.crop = crop
        self.days_grown = 0
        self.status = "已播种"

    def grow(self):
        if self.status == "已播种":
            self.days_grown += 1
            if self.days_grown >= self.crop.grow_days:
                self.status = "可收获"

    def harvest(self):
        if self.status == "可收获":
            yield_total = self.crop.yield_per_mu * self.area_mu
            self.crop = None
            self.days_grown = 0
            self.status = "空地"
            return yield_total
        return 0
```

## economy.py
- 每日结算收入与支出
- 贷款利息计算与自动扣除
- 玩家资产、负债、净收入追踪

## game_state.py
- 保存游戏进度至 JSON 文件
- 加载游戏状态、校验存档完整性

## events.py
- 随机生成自然灾害事件（干旱、暴雨、病虫害）
- 基于天气联动发生，影响作物质量和产量

## utils.py
- 日期推进逻辑
- CLI 输出美化：颜色提示、警告、表格格式化
- 可选日志系统

# ✅ 后续开发建议：
- 已完成 weather.py、crops.py、farm.py 三大基础模块
- 下一步建议：economy.py + market.py
- 所有决策通过 CLI input() 实现简单交互
- 后期可添加：GUI 显示、地图式界面、成就系统等

# 👉 如需我继续完成市场价格模块或经济结算逻辑，请指定模块