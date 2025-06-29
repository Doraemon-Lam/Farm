import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from datetime import datetime, timedelta
import json
import os

from weather import WeatherDynamic
from market import Market
from plant import get_all_crop_data
from crops import Field
from storage import Storage
from loan import LoanManager

SAVE_FILE = "farmersimpy_save.json"
LOG_FILE = "farmersimpy_log.txt"

class FarmerSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧑‍🌾 FarmerSimPy 农民模拟器 v2.0")
        self.root.geometry("960x760")
        
        self.dynamic_mode = False
        self.timer_running = False

        self.date = datetime(2025, 3, 1)
        self.funds = 10000
        self.weather = WeatherDynamic(self.date)
        self.market = Market()
        self.market.update_prices(self.weather)
        self.crop_data = get_all_crop_data()
        self.storage = Storage()
        self.fields = [Field() for _ in range(2)] # Start with two Fields
        self.field_buttons = []
        self.field_base_price = 2000

        self.loan_manager = LoanManager()

        self.info_var = tk.StringVar()
        self.info_label = tk.Label(root, textvariable=self.info_var, font=("Arial", 14), anchor="w", bg="#e6ffe6")
        self.info_label.pack(fill="x", ipady=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_fields = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fields, text="🌾 田地状态")

        self.tab_market = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_market, text="📈 市场行情")
        self.market_text = tk.Text(self.tab_market, height=12, font=("Arial", 10))
        self.market_text.pack(expand=True, fill="both")

        self.tab_storage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_storage, text="📦 仓库存储")

        self.tab_finance = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_finance, text="💰 财务与贷款")
        self.finance_text = tk.Text(self.tab_finance, height=12, font=("Arial", 10))
        self.finance_text.pack(expand=True, fill="both")

        self.setup_field_grid()

        op_frame = tk.Frame(root)
        op_frame.pack(fill="x", pady=5)
        tk.Button(op_frame, text="查看天气", command=self.show_weather).pack(side="left", padx=5)
        tk.Button(op_frame, text="播种", command=self.plant_crop).pack(side="left", padx=5)
        tk.Button(op_frame, text="浇水", command=lambda: self.apply_field_action("water")).pack(side="left", padx=5)
        tk.Button(op_frame, text="施氮肥(N)", command=lambda: self.apply_fertilizer_action('N')).pack(side="left", padx=5)
        tk.Button(op_frame, text="施磷肥(P)", command=lambda: self.apply_fertilizer_action('P')).pack(side="left", padx=5)
        tk.Button(op_frame, text="施钾肥(K)", command=lambda: self.apply_fertilizer_action('K')).pack(side="left", padx=5)
        tk.Button(op_frame, text="喷药", command=lambda: self.apply_field_action("pesticide")).pack(side="left", padx=5)
        tk.Button(op_frame, text="收获", command=self.harvest_crop).pack(side="left", padx=5)
        tk.Button(op_frame, text="借款", command=self.borrow_money).pack(side="left", padx=5)
        tk.Button(op_frame, text="推进一天", command=self.next_day).pack(side="right", padx=5)

        log_frame = tk.Frame(root)
        log_frame.pack(fill="both", expand=True)
        self.log_box = scrolledtext.ScrolledText(log_frame, height=15, font=("Arial", 10))
        self.log_box.pack(fill="both", expand=True)
        
        bottom_bar = tk.Frame(root)
        bottom_bar.pack(fill="x", pady=5)
        tk.Button(bottom_bar, text="保存存档", command=self.save_game).pack(side="left", padx=5)
        tk.Button(bottom_bar, text="读取存档", command=self.load_game).pack(side="left", padx=5)
        self.dynamic_button = tk.Button(bottom_bar, text="▶️ 启动动态模式", command=self.toggle_dynamic_mode, bg="#d0f0d0")
        self.dynamic_button.pack(side="right", padx=5)
        tk.Button(bottom_bar, text="退出游戏", command=root.quit).pack(side="right", padx=5)

        self.update_info_bar()
        self.refresh_all()

    def update_info_bar(self):
        time_str = self.weather.time.strftime('%Y-%m-%d %H:%M')
        weather_summary = f"🌡{self.weather.current_temperature}°C | ☀{self.weather.current_sunlight} | 💧{self.weather.current_rainfall}mm"
        self.info_var.set(f"📅 {time_str}    💰 资金: ￥{self.funds:.2f}    {weather_summary}")

    def log(self, msg, level="info"):
        ts = self.weather.time.strftime("%H:%M")
        prefix = {"info": "INFO", "warn": "WARN", "error": "ERROR"}.get(level, "INFO")
        entry = f"[{prefix} {ts}] {msg}\n"
        self.log_box.insert("end", entry)
        self.log_box.see("end")

    def setup_field_grid(self):
        for widget in self.tab_fields.winfo_children():
            widget.destroy()
        self.field_buttons.clear()

        grid = tk.Frame(self.tab_fields)
        grid.pack(expand=True, fill="both", padx=10, pady=10)
        
        num_fields = len(self.fields)
        for i in range(num_fields):
            btn = tk.Button(
                grid, text=f"田地 {i+1}\n（空地）", width=25, height=7,
                relief="groove", bg="#e0ffe0", font=("Arial", 10, "bold"),
                command=lambda idx=i: self.on_field_click(idx), justify="left", anchor="nw",
                wraplength=180
            )
            btn.grid(row=i//3, column=i % 3, padx=10, pady=10, sticky="nsew")
            self.field_buttons.append(btn)

        if num_fields < 9:
            buy_button = tk.Button(
                grid, text=f"购买新田地\n价格: ￥{self.get_next_field_price()}",
                width=25, height=7, relief="groove", bg="#d0e0f0",
                font=("Arial", 10, "bold"), command=self.buy_field
            )
            buy_button.grid(row=num_fields//3, column=num_fields % 3, padx=10, pady=10, sticky="nsew")

        for i in range(3):
            grid.grid_rowconfigure(i, weight=1)
            grid.grid_columnconfigure(i, weight=1)

    def get_next_field_price(self):
        return self.field_base_price * (1.5 ** (len(self.fields) - 1))

    def buy_field(self):
        price = self.get_next_field_price()
        if self.funds < price:
            messagebox.showerror("资金不足", f"购买新田地需要 ￥{price:.2f}")
            return
        
        if messagebox.askquestion("确认购买", f"确定要花费 ￥{price:.2f} 购买一块新田地吗?") == "yes":
            self.funds -= price
            self.fields.append(Field())
            self.log(f"成功购买了一块新田地，花费 ￥{price:.2f}", "info")
            self.setup_field_grid()
            self.refresh_all()

    def on_field_click(self, idx):
        field = self.fields[idx]
        if not field.crop:
            if messagebox.askquestion("播种", f"田地 {idx+1} 是空的, 是否现在播种?") == "yes":
                self.manual_plant(idx)
        else:
            self.show_crop_details(idx)

    def show_crop_details(self, idx):
        field = self.fields[idx]
        crop = field.crop
        win = tk.Toplevel(self.root)
        win.title(f"田地 {idx+1} 详情")
        win.geometry("350x400")
        
        details = crop.status() + "\n\n"
        details += f"--- 作物需求 ---\n"
        details += f"适宜温度: {crop.crop_data.temp_range[0]}-{crop.crop_data.temp_range[1]}°C\n"
        details += f"理想光照: {crop.crop_data.sun_preference[0]} ± {crop.crop_data.sun_preference[1]}\n"
        details += f"每日需水: {crop.crop_data.water_need}mm\n"
        details += f"NPK偏好: {crop.crop_data.npk_preference}\n"

        tk.Label(win, text=details, justify="left", wraplength=320, anchor="nw").pack(pady=10, padx=10)

        if crop.dead or crop.harvested:
            if messagebox.askquestion("清理田地", "作物已死亡或收获, 是否清理这块田地?") == "yes":
                field.clear_field()
                self.log(f"田地 {idx+1} 已被清理。")
                self.refresh_all()
            win.destroy()
            return

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        def create_action(action):
            def func():
                self.apply_direct_field_action(idx, action)
                win.destroy()
            return func

        actions = {
            "water": "💧 浇水",
            "pesticide": "🧴 喷药",
            "harvest": "🎉 收获"
        }
        for action, text in actions.items():
            tk.Button(btn_frame, text=text, command=create_action(action), width=12).pack(pady=3)

    def apply_direct_field_action(self, idx, action):
        field = self.fields[idx]
        crop = field.crop
        if not crop or crop.dead or crop.harvested:
            self.log("无效操作: 作物不存在或已处理。", "warn")
            return

        action_costs = {"water": 10, "pesticide": 120}
        cost = action_costs.get(action, 0)
        action_cn = {"water": "浇水", "pesticide": "喷药"}.get(action, action)

        if self.funds < cost:
            self.log(f"资金不足! 操作 '{action_cn}' 需要 ￥{cost:.2f}", "error")
            return

        if action == "harvest":
            self.manual_harvest(idx)
            return

        self.funds -= cost
        crop.apply_manual_action(action)
        self.log(f"在田地 {idx+1} 上执行了 '{action_cn}' 操作, 花费 ￥{cost:.2f}")
        self.refresh_all()

    def manual_plant(self, idx):
        field = self.fields[idx]
        if field.crop:
            messagebox.showerror("错误", "这块田地已经种上作物了。")
            return

        win = tk.Toplevel(self.root)
        win.title(f"选择作物播种到田地 {idx+1}")
        win.geometry("550x450")

        tk.Label(win, text="选择一种作物进行播种:", font=("Arial", 12)).pack(pady=5)
        
        canvas = tk.Canvas(win)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def plant_action(crop_name):
            crop_data = self.crop_data[crop_name]
            cost = crop_data.cost_per_mu
            if self.funds < cost:
                messagebox.showerror("资金不足", f"播种 {crop_name} 需要 ￥{cost:.2f}", parent=win)
                return
            
            if field.plant_crop(crop_data, self.weather.date.timetuple().tm_yday):
                self.funds -= cost
                self.log(f"在田地 {idx+1} 成功播种 {crop_name}, 花费 ￥{cost:.2f}")
                self.refresh_all()
                win.destroy()
            else:
                messagebox.showerror("错误", "无法播种，请稍后再试。", parent=win)

        for name, crop_data in self.crop_data.items():
            frame = tk.Frame(scrollable_frame, borderwidth=2, relief="groove", padx=5, pady=5)
            desc = crop_data.description()
            tk.Label(frame, text=desc, justify="left", wraplength=450).pack(side="left", fill="x", expand=True)
            tk.Button(frame, text="播种", command=lambda n=name: plant_action(n)).pack(side="right", padx=10)
            frame.pack(fill="x", pady=5, padx=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def manual_harvest(self, idx):
        field = self.fields[idx]
        if not field.crop: return
        result = field.crop.harvest()
        if result:
            self.storage.add_crop(result)
            field.clear_field()
            tags = f" (品质: {', '.join(result['quality_tags'])})" if result['quality_tags'] else ""
            self.log(f"🎉 成功收获 {result['name']}! 产量: {result['yield']}kg{tags}")
        else:
            self.log("无法收获: 作物未成熟, 或已死亡/收获。", "warn")
        self.refresh_all()

    def show_weather(self):
        self.log("天气预报: " + self.weather.summary())

    def refresh_all(self):
        self.update_info_bar()
        self.refresh_field()
        self.refresh_market()
        self.refresh_storage()
        self.refresh_finance()

    def refresh_field(self):
        for i, field in enumerate(self.fields):
            btn = self.field_buttons[i]
            status_text = field.status()
            
            bg_color = "#c8e6c9"
            if field.crop:
                if field.crop.dead:
                    bg_color = "#a0a0a0"
                elif field.crop.harvested:
                    bg_color = "#bbdefb"
                elif field.crop.damage_reasons:
                    bg_color = "#ffcdd2"
                else:
                    bg_color = "#fff9c4"

            btn.config(text=f"田地 {i+1}\n{status_text}", bg=bg_color)

    def refresh_market(self):
        self.market_text.delete("1.0", "end")
        for p in self.market.products:
            self.market_text.insert("end", f"{p.info()}\n")

    def refresh_storage(self):
        for widget in self.tab_storage.winfo_children():
            widget.destroy()

        op_frame = tk.Frame(self.tab_storage)
        op_frame.pack(fill="x", pady=5)
        tk.Button(op_frame, text="一键出售所有作物", command=self.sell_crop).pack(side="left", padx=10)

        if not self.storage.stock:
            tk.Label(self.tab_storage, text="📦 仓库为空").pack(pady=20)
            return

        canvas = tk.Canvas(self.tab_storage)
        scrollbar = ttk.Scrollbar(self.tab_storage, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for i, crop in enumerate(self.storage.stock):
            tags = f" ({', '.join(crop['quality_tags'])})" if crop.get('quality_tags') else ""
            btn_text = f"{crop['name']}{tags} ({crop['yield']}kg)\n新鲜度: {crop['freshness']:.0f}% | 营养: {crop['nutrition']}"
            tk.Button(
                scrollable_frame, text=btn_text, justify="left",
                command=lambda idx=i: self.show_storage_item_details(idx)
            ).pack(fill="x", padx=10, pady=3)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_storage_item_details(self, idx):
        crop = self.storage.stock[idx]
        win = tk.Toplevel(self.root)
        win.title(f"出售详情: {crop['name']}")
        win.geometry("320x280")

        market_price = self.market.get_price(crop['name'])
        
        quality_bonus = 1.0 + (len(crop.get('quality_tags', [])) * 0.25)
        tags_str = f" ({', '.join(crop['quality_tags'])})" if crop.get('quality_tags') else ""

        multiplier = (crop['nutrition'] * 0.5 + crop['freshness'] * 0.5) / 100
        estimated_value = round(crop['yield'] * market_price * multiplier * quality_bonus, 2)
        profit = estimated_value - crop.get('cost', 0)

        details = f"作物: {crop['name']}{tags_str}\n"
        details += f"重量: {crop['yield']} kg\n"
        details += f"新鲜度: {crop['freshness']:.1f}% | 营养值: {crop['nutrition']}\n\n"
        details += f"--- 财务信息 ---\n"
        details += f"市场价: ￥{market_price:.2f}/kg\n"
        details += f"品质加成: {quality_bonus:.2f}x\n"
        details += f"总成本: ￥{crop.get('cost', 0):.2f}\n"
        details += f"预估售价: ￥{estimated_value:.2f}\n"
        details += f"预估利润: ￥{profit:.2f}"

        tk.Label(win, text=details, justify="left", padx=10, pady=10).pack(fill="x")
        
        def sell_action():
            self.sell_crop(idx)
            win.destroy()

        tk.Button(win, text=f"以此价格出售", command=sell_action).pack(pady=10)

    def refresh_finance(self):
        self.finance_text.delete("1.0", "end")
        status = self.loan_manager.get_status()
        self.finance_text.insert("end", f"--- 贷款与信用 ---\n{status}")

    def plant_crop(self):
        empty_indices = [i for i, f in enumerate(self.fields) if f.crop is None]
        if not empty_indices:
            messagebox.showinfo("提示", "所有田地都已种植。")
            return
        self.manual_plant(empty_indices[0])

    def _prompt_for_field(self, prompt_title, valid_indices_provider):
        valid_indices = valid_indices_provider()
        if not valid_indices:
            self.log("没有符合条件的田地。", "warn")
            return None
        
        idx_str = simpledialog.askstring(prompt_title, f"选择田地 (可选: {', '.join(map(str, [i+1 for i in valid_indices]))})")
        try:
            idx = int(idx_str) - 1
            if idx not in valid_indices:
                raise ValueError
            return idx
        except (ValueError, TypeError):
            self.log("无效的田地编号。", "error")
            return None

    def apply_field_action(self, action):
        idx = self._prompt_for_field(
            f"执行 '{action}'",
            lambda: [i for i, f in enumerate(self.fields) if f.crop and not f.crop.dead and not f.crop.harvested]
        )
        if idx is not None:
            self.apply_direct_field_action(idx, action)

    def apply_fertilizer_action(self, nutrient_type):
        cost = 50
        if self.funds < cost:
            messagebox.showerror("资金不足", f"施肥需要 ￥{cost:.2f}")
            return

        idx = self._prompt_for_field(
            f"施加 {nutrient_type} 肥",
            lambda: [i for i, f in enumerate(self.fields)]
        )
        if idx is not None:
            self.funds -= cost
            message = self.fields[idx].apply_fertilizer(nutrient_type)
            self.log(f"在田地 {idx+1} {message} 花费 ￥{cost:.2f}", "info")
            self.refresh_all()

    def harvest_crop(self):
        idx = self._prompt_for_field(
            "收获作物",
            lambda: [i for i, f in enumerate(self.fields) if f.crop and f.crop.matured and not f.crop.dead and not f.crop.harvested]
        )
        if idx is not None:
            self.manual_harvest(idx)

    def sell_crop(self, index_to_sell=None):
        if not self.storage.stock:
            self.log("仓库是空的。", "warn")
            return

        if index_to_sell is None:
            if messagebox.askquestion("一键出售", "确定要出售仓库里所有的作物吗?") != "yes":
                return
            
            total_revenue = 0
            num_sold = len(self.storage.stock)
            
            for i in range(len(self.storage.stock) - 1, -1, -1):
                crop = self.storage.stock[i]
                price = self.market.get_price(crop['name'])
                quality_bonus = 1.0 + (len(crop.get('quality_tags', [])) * 0.25)
                name, value = self.storage.sell_crop(i, price, quality_bonus)
                self.funds += value
                total_revenue += value
            
            self.log(f"💰 一键出售完成! 共售出 {num_sold}批作物, 总收入 ￥{total_revenue:.2f}", "info")

        else:
            try:
                idx = int(index_to_sell)
                if not (0 <= idx < len(self.storage.stock)): raise ValueError
                crop = self.storage.stock[idx]
                price = self.market.get_price(crop['name'])
                quality_bonus = 1.0 + (len(crop.get('quality_tags', [])) * 0.25)
                name, value = self.storage.sell_crop(idx, price, quality_bonus)
                self.funds += value
                self.log(f"💰 成功出售 {name}, 获得 ￥{value:.2f}")
            except (ValueError, TypeError):
                self.log("无效的编号。", "error")
        
        self.refresh_all()

    def next_day(self):
        if self.timer_running:
            self.log("请先暂停动态模式。", "warn")
            return
        self.log("--- 新的一天开始了 ---", "info")
        for _ in range(24):
            self.update_hour_logic()
        self.log(f"--- 结束 {self.weather.date.strftime('%Y-%m-%d')} ---", "info")
        self.refresh_all()

    def save_game(self):
        data = {
            "date": self.weather.time.strftime("%Y-%m-%d %H:%M:%S"),
            "funds": self.funds,
            "fields": [],
            "storage": self.storage.stock,
            "loan_info": {
                "total_debt": self.loan_manager.total_debt,
                "credit_score": self.loan_manager.credit_score
            }
        }
        
        for field in self.fields:
            field_data = {"soil_npk": field.soil_npk, "crop": None}
            if field.crop:
                crop = field.crop
                field_data["crop"] = {
                    "crop_data_name": crop.crop_data.name,
                    "planted_day": crop.planted_day,
                    "day_counter": crop.day_counter,
                    "hour_counter": crop.hour_counter,
                    "growth_points": crop.growth_points,
                    "matured": crop.matured,
                    "dead": crop.dead,
                    "harvested": crop.harvested,
                    "health": crop.health,
                    "water_level": crop.water_level,
                    "sun_stress": crop.sun_stress,
                    "nutrient_satisfaction": crop.nutrient_satisfaction,
                    "quality_tags": list(crop.quality_tags),
                    "pesticide_effect_hours": crop.pesticide_effect_hours,
                    "damage_reasons": list(crop.damage_reasons),
                    "total_cost": crop.total_cost,
                }
            data["fields"].append(field_data)

        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(self.log_box.get("1.0", "end"))
            self.log("💾 游戏已保存。", "info")
        except Exception as e:
            self.log(f"❌ 保存失败: {e}", "error")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.log("没有找到存档文件。", "warn")
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.date = datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S")
            self.weather = WeatherDynamic(self.date)
            self.weather.time = self.date
            
            self.funds = data["funds"]
            self.storage.stock = data["storage"]
            
            if "loan_info" in data:
                self.loan_manager.total_debt = data["loan_info"].get("total_debt", 30000)
                self.loan_manager.credit_score = data["loan_info"].get("credit_score", 100)
            
            self.fields = []
            from crops import CropInstance
            for field_data in data["fields"]:
                new_field = Field()
                new_field.soil_npk = field_data["soil_npk"]
                if field_data.get("crop"):
                    crop_save_data = field_data["crop"]
                    crop_data_name = crop_save_data["crop_data_name"]
                    crop_data = self.crop_data[crop_data_name]
                    
                    new_crop = CropInstance(crop_data, crop_save_data["planted_day"], new_field)
                    
                    for key, value in crop_save_data.items():
                        if key == "damage_reasons" or key == "quality_tags":
                            setattr(new_crop, key, set(value))
                        elif key not in ["crop_data_name", "field"]:
                            setattr(new_crop, key, value)
                    new_field.crop = new_crop
                self.fields.append(new_field)

            self.setup_field_grid()
            self.market.update_prices(self.weather)
            self.log("📂 游戏已加载。", "info")
            self.refresh_all()
        except Exception as e:
            self.log(f"❌ 加载失败: {e}", "error")

    def toggle_dynamic_mode(self):
        self.dynamic_mode = not self.dynamic_mode
        if self.dynamic_mode:
            self.log("▶️ 动态模式已启动。游戏将每2.5秒更新一小时。", "info")
            self.dynamic_button.config(text="⏸️ 暂停动态模式", bg="#f0d0d0")
            self.timer_running = True
            self.root.after(2500, self.update_dynamic_hour)
        else:
            self.log("⏸️ 动态模式已暂停。", "info")
            self.dynamic_button.config(text="▶️ 启动动态模式", bg="#d0f0d0")
            self.timer_running = False

    def update_hour_logic(self):
        is_new_day = self.weather.is_new_day()
        if is_new_day:
            if self.weather.time.day == self.loan_manager.repayment_day:
                self.handle_loan_payment()

            self.weather.start_new_day(self.weather.time)
            self.market.update_prices(self.weather)
            self.log('📈 市场价格已刷新。', "info")
            fee = self.storage.update_all()
            if fee > 0:
                self.funds -= fee
                self.log(f"📦 支付了仓储费 ￥{fee:.2f}", "info")

        self.weather.update_hour()

        log_messages = []
        for i, field in enumerate(self.fields):
            if field.crop and not field.crop.dead and not field.crop.harvested:
                old_reasons = set(field.crop.damage_reasons)
                
                field.crop.update_hourly(self.weather)
                
                new_reasons = set(field.crop.damage_reasons)
                newly_added_reasons = new_reasons - old_reasons
                if newly_added_reasons:
                    log_messages.append(f"田地{i+1} ({field.crop.crop_data.name}) 出现问题: {', '.join(newly_added_reasons)}")

                if field.crop.dead:
                    self.log(f"田地{i+1} ({field.crop.crop_data.name}) 已经死亡。原因: {', '.join(field.crop.damage_reasons)}", "warn")
                elif field.crop.matured and not old_reasons and field.crop.growth_points >= field.crop.crop_data.grow_days:
                     self.log(f"田地{i+1} ({field.crop.crop_data.name}) 已经成熟，可以收获了！", "info")

        if self.weather.time.hour % 6 == 0:
             log_messages.append(self.weather.summary())
        
        if log_messages:
            self.log("\n".join(log_messages), "warn" if any("问题" in m for m in log_messages) else "info")

    def update_dynamic_hour(self):
        if not self.timer_running:
            return
        
        self.update_hour_logic()
        self.refresh_all()
        self.root.after(2500, self.update_dynamic_hour)

    def borrow_money(self):
        max_loan = self.loan_manager.max_loan_amount
        amount_str = simpledialog.askstring("借款", f"请输入借款金额 (最多 ￥{max_loan:.2f}):")
        if not amount_str: return

        try:
            amount = float(amount_str)
            success, message = self.loan_manager.borrow_money(amount)
            if success:
                self.funds += amount
                self.log(message, "info")
                messagebox.showinfo("借款成功", message)
            else:
                self.log(message, "error")
                messagebox.showerror("借款失败", message)
            self.refresh_all()
        except ValueError:
            messagebox.showerror("输入无效", "请输入一个有效的数字。")

    def handle_loan_payment(self):
        self.log("--- 还款日 ---", "info")
        status, amount_paid, message = self.loan_manager.handle_repayment(self.funds)
        
        if status == "paid_full" or status == "paid_partial":
            self.funds -= amount_paid
            self.log(message, "info")
            messagebox.showinfo("还款成功", message)
        elif status == "overdue":
            self.log(message, "warn")
            messagebox.showwarning("还款逾期", message)
        else:
            self.log(message, "info")

        if self.loan_manager.credit_score <= 0:
            self.game_over("你的信用分已降至0，无法继续经营，游戏结束。")
        
        self.refresh_all()

    def game_over(self, reason):
        self.timer_running = False
        messagebox.showinfo("游戏结束", reason)
        self.log(f"--- 游戏结束: {reason} ---", "error")
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, tk.Button):
                        btn.config(state="disabled")
        self.dynamic_button.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = FarmerSimGUI(root)
    root.mainloop()