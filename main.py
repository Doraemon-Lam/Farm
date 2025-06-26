

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from datetime import datetime, timedelta
import json
import os

from weather import Weather, WeatherDynamic
from market import Market
from crops import get_default_crop_types, CropInstance
from storage import Storage

SAVE_FILE = "farmersimpy_save.json"
LOG_FILE = "farmersimpy_log.txt"

class FarmerSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧑‍🌾 FarmerSimPy 农民模拟器")
        self.root.geometry("900x720")
        
        self.dynamic_mode = False
        self.timer_running = False

        self.date = datetime(2025, 3, 1)
        self.funds = 10000
        self.weather = WeatherDynamic(self.date) # Always use dynamic weather internally
        self.market = Market()
        self.market.update_prices(self.weather)
        self.crop_types = get_default_crop_types()
        self.storage = Storage()
        self.fields = [None for _ in range(5)]
        self.field_buttons = []

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
        self.storage_text = tk.Text(self.tab_storage, height=12, font=("Arial", 10))
        self.storage_text.pack(expand=True, fill="both")

        self.setup_field_grid()

        op_frame = tk.Frame(root)
        op_frame.pack(fill="x", pady=5)
        tk.Button(op_frame, text="查看天气", command=self.show_weather).pack(side="left", padx=5)
        tk.Button(op_frame, text="播种", command=self.plant_crop).pack(side="left", padx=5)
        tk.Button(op_frame, text="浇水", command=lambda: self.apply_field_action("water", 150)).pack(side="left", padx=5)
        tk.Button(op_frame, text="施肥", command=lambda: self.apply_field_action("fertilize", 100)).pack(side="left", padx=5)
        tk.Button(op_frame, text="喷药", command=lambda: self.apply_field_action("pesticide", 120)).pack(side="left", padx=5)
        tk.Button(op_frame, text="收获", command=self.harvest_crop).pack(side="left", padx=5)
        tk.Button(op_frame, text="出售仓库", command=self.sell_crop).pack(side="left", padx=5)
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
        self.info_var.set(f"📅 {time_str}    💰 资金: ￥{self.funds:.2f}")

    def log(self, msg, level="info"):
        ts = self.weather.time.strftime("%H:%M")
        prefix = {"info": "INFO", "warn": "WARN", "error": "ERROR"}.get(level, "INFO")
        entry = f"[{prefix} {ts}] {msg}\n"
        self.log_box.insert("end", entry)
        self.log_box.see("end")

    def setup_field_grid(self):
        self.field_buttons.clear()
        grid = tk.Frame(self.tab_fields)
        grid.pack(expand=True, fill="both", padx=10, pady=10)
        for i in range(5):
            btn = tk.Button(
                grid, text=f"田地 {i+1}\n（空地）", width=20, height=5,
                relief="groove", bg="#e0ffe0", font=("Arial", 10, "bold"),
                command=lambda idx=i: self.on_field_click(idx), justify="left", anchor="nw",
                wraplength=150
            )
            btn.grid(row=i//3, column=i % 3, padx=10, pady=10, sticky="nsew")
            self.field_buttons.append(btn)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(2, weight=1)


    def on_field_click(self, idx):
        crop = self.fields[idx]
        if not crop:
            if messagebox.askquestion("播种", f"田地 {idx+1} 是空的, 是否现在播种?") == "yes":
                self.manual_plant(idx)
        else:
            self.show_crop_details(idx)

    def show_crop_details(self, idx):
        crop = self.fields[idx]
        win = tk.Toplevel(self.root)
        win.title(f"田地 {idx+1} 详情")
        win.geometry("300x250")
        
        tk.Label(win, text=crop.status(), justify="left", wraplength=280).pack(pady=10, padx=10)

        if crop.dead or crop.harvested:
            if messagebox.askquestion("清理田地", "作物已死亡或收获, 是否清理这块田地?") == "yes":
                self.fields[idx] = None
                self.log(f"田地 {idx+1} 已被清理。")
                self.refresh_all()
            win.destroy()
            return

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        def create_action(action, cost, text):
            def func():
                self.apply_direct_field_action(idx, action, cost)
                win.destroy()
                self.show_crop_details(idx) # Reopen to show updated status
            return func

        actions = [
            ("water", 150, "💧 浇水"), ("fertilize", 100, "🌿 施肥"),
            ("pesticide", 120, "🧴 喷药"), ("harvest", 0, "🎉 收获")
        ]
        for action, cost, text in actions:
            tk.Button(btn_frame, text=text, command=create_action(action, cost, text), width=12).pack(pady=3)

    def apply_direct_field_action(self, idx, action, cost):
        crop = self.fields[idx]
        if not crop or crop.dead or crop.harvested:
            self.log("无效操作: 作物不存在或已处理。", "warn")
            return
        if self.funds < cost:
            self.log(f"资金不足, 需要 ￥{cost:.2f}", "error")
            return
        
        if action == "harvest":
            self.manual_harvest(idx)
            return

        self.funds -= cost
        crop.apply_manual_action(action)
        self.log(f"在田地 {idx+1} 上执行了 '{action}' 操作, 花费 ￥{cost:.2f}")
        self.refresh_all()

    def manual_plant(self, idx):
        crop_options = list(self.crop_types.keys())
        crop_name = simpledialog.askstring("播种", f"选择作物播种到田地 {idx+1}:\n" + "\n".join(crop_options))
        if crop_name not in self.crop_types:
            self.log(f"无效的作物名称: {crop_name}", "error")
            return
        
        cost = self.crop_types[crop_name].cost_per_mu
        if self.funds < cost:
            self.log(f"资金不足以播种 {crop_name}, 需要 ￥{cost:.2f}", "error")
            return
            
        self.fields[idx] = CropInstance(self.crop_types[crop_name], self.weather.date.dayofyear)
        self.funds -= cost
        self.log(f"在田地 {idx+1} 成功播种 {crop_name}, 花费 ￥{cost:.2f}")
        self.refresh_all()

    def manual_harvest(self, idx):
        crop = self.fields[idx]
        if not crop: return
        result = crop.harvest()
        if result:
            self.storage.add_crop(result)
            self.fields[idx] = None
            self.log(f"🎉 成功收获 {result['name']}! 产量: {result['yield']}kg, 营养: {result['nutrition']}")
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

    def refresh_field(self):
        for i, crop in enumerate(self.fields):
            btn = self.field_buttons[i]
            if not crop:
                btn.config(text=f"田地 {i+1}\n（空地）", bg="#c8e6c9")
            elif crop.dead:
                btn.config(text=f"田地 {i+1}\n❌ 死亡\n{crop.crop_type.name}", bg="#a0a0a0")
            elif crop.harvested:
                btn.config(text=f"田地 {i+1}\n🎉 已收获\n{crop.crop_type.name}", bg="#bbdefb")
            else:
                status_line = "✅成熟" if crop.matured else "🌱生长中"
                health_color = "#ffcdd2" if crop.damage_reasons else "#fff9c4"
                btn.config(
                    text=f"田地 {i+1}: {crop.crop_type.name}\n"
                         f"第{crop.day_counter}/{crop.crop_type.grow_days}天 | {status_line}\n"
                         f"健康: {crop.health:.1f}% | 水分: {crop.water_level:.1f}%\n"
                         f"受损原因: {', '.join(crop.damage_reasons) or '无'}",
                    bg=health_color
                )

    def refresh_market(self):
        self.market_text.delete("1.0", "end")
        for p in self.market.products:
            self.market_text.insert("end", f"{p.info()}\n")

    def refresh_storage(self):
        self.storage_text.delete("1.0", "end")
        if not self.storage.stock:
            self.storage_text.insert("end", "📦 仓库为空\n")
        else:
            for i, crop in enumerate(self.storage.stock):
                self.storage_text.insert("end", f"{i + 1}. {crop['name']} | 营养: {crop['nutrition']} | 新鲜度: {crop['freshness']:.1f}% | 重量: {crop['yield']}kg\n")

    def plant_crop(self):
        empty_indices = [i for i, f in enumerate(self.fields) if f is None]
        if not empty_indices:
            messagebox.showinfo("提示", "所有田地都已种植。")
            return
        self.manual_plant(empty_indices[0])

    def apply_field_action(self, action, cost):
        available_indices = [i+1 for i, f in enumerate(self.fields) if f and not f.dead and not f.harvested]
        if not available_indices:
            self.log("没有可进行操作的田地。", "warn")
            return
        idx_str = simpledialog.askstring("田地操作", f"在哪个田地执行 '{action}'? (可选: {', '.join(map(str, available_indices))})")
        try:
            idx = int(idx_str) - 1
            if idx + 1 not in available_indices: raise ValueError
            self.apply_direct_field_action(idx, action, cost)
        except (ValueError, TypeError):
            self.log("无效的田地编号。", "error")

    def harvest_crop(self):
        harvestable_indices = [i+1 for i, c in enumerate(self.fields) if c and c.matured and not c.dead and not c.harvested]
        if not harvestable_indices:
            self.log("没有可收获的作物。", "warn")
            return
        idx_str = simpledialog.askstring("收获", f"选择要收获的田地 (可选: {', '.join(map(str, harvestable_indices))})")
        try:
            idx = int(idx_str) - 1
            if idx + 1 not in harvestable_indices: raise ValueError
            self.manual_harvest(idx)
        except (ValueError, TypeError):
            self.log("无效的田地编号。", "error")

    def sell_crop(self):
        if not self.storage.stock:
            self.log("仓库是空的。", "warn")
            return
        self.refresh_storage()
        idx_str = simpledialog.askstring("出售", "输入要出售的作物的编号:")
        try:
            idx = int(idx_str) - 1
            if not (0 <= idx < len(self.storage.stock)): raise ValueError
            crop = self.storage.stock[idx]
            price = self.market.get_price(crop['name'])
            name, value = self.storage.sell_crop(idx, price)
            self.funds += value
            self.log(f"💰 成功出售 {name}, 获得 ￥{value:.2f}")
            self.refresh_all()
        except (ValueError, TypeError):
            self.log("无效的编号。", "error")

    def next_day(self):
        if self.timer_running:
            self.log("请先暂停动态模式。", "warn")
            return
        self.log("--- 新的一天开始了 ---", "info")
        for _ in range(24):
            self.update_hour_logic()
        self.log(f"--- 结束 {self.weather.date.strftime('%Y-%m-%d')} ---", "info")

    def save_game(self):
        data = {
            "date": self.weather.time.strftime("%Y-%m-%d %H:%M:%S"),
            "funds": self.funds,
            "fields": [c.__dict__ if c else None for c in self.fields],
            "storage": self.storage.stock,
        }
        for field_data in data["fields"]:
            if field_data:
                field_data['crop_type'] = field_data['crop_type'].name
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
            
            self.fields = []
            for field_data in data["fields"]:
                if field_data:
                    crop_type_name = field_data["crop_type"]
                    crop_type = self.crop_types[crop_type_name]
                    
                    # Create a new instance and load state
                    new_crop = CropInstance(crop_type, field_data["planted_day"])
                    for key, value in field_data.items():
                        if key != "crop_type":
                            setattr(new_crop, key, value)
                    self.fields.append(new_crop)
                else:
                    self.fields.append(None)

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
        is_new_day = self.weather.is_new_day() and self.weather.time.hour == 0
        
        self.weather.update_hour()
        
        if is_new_day:
            self.weather.start_new_day(self.weather.time)
            self.market.update_prices(self.weather)
            self.log('📈 市场价格已刷新。', "info")
            fee = self.storage.update_all()
            if fee > 0:
                self.funds -= fee
                self.log(f"📦 支付了仓储费 ￥{fee:.2f}", "info")

        log_messages = []
        for i, crop in enumerate(self.fields):
            if crop and not crop.dead and not crop.harvested:
                old_reasons = set(crop.damage_reasons)
                crop.update_hourly(self.weather)
                new_reasons = set(crop.damage_reasons)
                
                # Log new problems
                newly_added_reasons = new_reasons - old_reasons
                if newly_added_reasons:
                    log_messages.append(f"田地{i+1} ({crop.crop_type.name}) 出现问题: {', '.join(newly_added_reasons)}")

        if self.weather.time.hour % 3 == 0: # Log weather every 3 hours
             log_messages.append(self.weather.summary())
        
        if log_messages:
            self.log("\n".join(log_messages), "warn" if any("问题" in m for m in log_messages) else "info")

        self.storage.update_freshness()

    def update_dynamic_hour(self):
        if not self.timer_running:
            return
        
        self.update_hour_logic()
        self.refresh_all()
        self.root.after(2500, self.update_dynamic_hour)

if __name__ == "__main__":
    root = tk.Tk()
    app = FarmerSimGUI(root)
    root.mainloop()
