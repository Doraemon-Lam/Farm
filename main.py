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
        self.root.title("\U0001F33E FarmerSimPy 农民模拟器")
        self.root.geometry("880x680")
        
        # 添加动态模式切换
        self.dynamic_mode = False
        self.timer_running = False

        # 初始化数据
        self.date = datetime(2025, 3, 1)
        self.funds = 10000
        self.weather = Weather(self.date)
        self.market = Market()
        self.market.update_prices(self.weather)
        self.crop_types = get_default_crop_types()
        self.storage = Storage()
        self.fields = [None for _ in range(5)]
        self.field_buttons = []

        # 顶部信息栏
        self.info_var = tk.StringVar()
        self.info_label = tk.Label(root, textvariable=self.info_var, font=("Arial", 14), anchor="w", bg="#e6ffe6")
        self.info_label.pack(fill="x")

        # 标签页结构
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_fields = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fields, text="🌾 田地状态")

        self.tab_market = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_market, text="\U0001F4B2 市场行情")
        self.market_text = tk.Text(self.tab_market, height=12)
        self.market_text.pack(expand=True, fill="both")

        self.tab_storage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_storage, text="\U0001F4E6 仓库存储")
        self.storage_text = tk.Text(self.tab_storage, height=12)
        self.storage_text.pack(expand=True, fill="both")

        # 田地按钮
        self.setup_field_grid()

        # 操作按钮
        op_frame = tk.Frame(root)
        op_frame.pack(fill="x", pady=6)
        tk.Button(op_frame, text="查看天气", command=self.show_weather).pack(side="left")
        tk.Button(op_frame, text="播种", command=self.plant_crop).pack(side="left")
        tk.Button(op_frame, text="浇水", command=lambda: self.apply_field_action("water", 150)).pack(side="left")
        tk.Button(op_frame, text="施肥", command=lambda: self.apply_field_action("fertilize", 100)).pack(side="left")
        tk.Button(op_frame, text="喷药", command=lambda: self.apply_field_action("pesticide", 120)).pack(side="left")
        tk.Button(op_frame, text="收获", command=self.harvest_crop).pack(side="left")
        tk.Button(op_frame, text="出售仓库", command=self.sell_crop).pack(side="left")
        tk.Button(op_frame, text="推进一天", command=self.next_day).pack(side="right")

        # 日志与保存与模式切换
        log_frame = tk.Frame(root)
        log_frame.pack(fill="x")
        self.log_box = scrolledtext.ScrolledText(log_frame, height=24)
        self.log_box.pack(fill="both")
        btns = tk.Frame(log_frame)
        btns.pack(fill="x")
        tk.Button(btns, text="保存存档", command=self.save_game).pack(side="left")
        tk.Button(btns, text="读取存档", command=self.load_game).pack(side="left")
        tk.Button(btns, text="切换动态模式", command=self.toggle_dynamic_mode).pack(side="right")
        tk.Button(btns, text="退出游戏", command=root.quit).pack(side="right")

        self.update_info_bar()
        self.refresh_all()

    def update_info_bar(self):
        self.info_var.set(f"📅 {self.date.strftime('%Y-%m-%d')}    💰 资金: ￥{self.funds:.2f}")

    def log(self, msg):
        ts = self.date.strftime("%Y-%m-%d")
        entry = f"[{ts}] {msg}\n"
        self.log_box.insert("end", entry)
        self.log_box.see("end")
        # 不再每次都写入文件，减少IO

    def setup_field_grid(self):
        self.field_buttons.clear()
        grid = tk.Frame(self.tab_fields)
        grid.pack(expand=True, fill="both", padx=10, pady=10)
        for i in range(5):
            btn = tk.Button(
                grid,
                text=f"田地 {i+1}\n（空地）",
                width=15,
                height=4,
                relief="groove",
                bg="#e0ffe0",
                font=("Arial", 10),
                command=lambda idx=i: self.on_field_click(idx)
            )
            btn.grid(row=i//3, column=i % 3, padx=10, pady=10)
            self.field_buttons.append(btn)

    def on_field_click(self, idx):
        crop = self.fields[idx]
        if not crop:
            action = messagebox.askquestion(
                f"田地 {idx+1}",
                "该地尚未播种。\n是否播种？"
            )
            if action == "yes":
                self.manual_plant(idx)
        elif crop.dead:
            messagebox.showinfo("提示", "该作物已死亡")
        elif crop.harvested:
            messagebox.showinfo("提示", "已收获")
        else:
            win = tk.Toplevel(self.root)
            win.title(f"田地 {idx+1} 操作")
            win.geometry("250x220")

            tk.Label(win, text=crop.status(), fg="green").pack(pady=6)

            def do_water():
                self.apply_direct_field_action(idx, "water", 150)
                win.destroy()

            def do_fertilize():
                self.apply_direct_field_action(idx, "fertilize", 100)
                win.destroy()

            def do_pesticide():
                self.apply_direct_field_action(idx, "pesticide", 120)
                win.destroy()

            def do_harvest():
                self.manual_harvest(idx)
                win.destroy()

            for txt, fn in [("💧 浇水", do_water), ("🌿 施肥", do_fertilize), ("🧴 喷药", do_pesticide), ("🎉 收获", do_harvest)]:
                tk.Button(win, text=txt, command=fn, width=16).pack(pady=3)

    def apply_direct_field_action(self, idx, action, cost):
        crop = self.fields[idx]
        if not crop or crop.dead:
            self.log("❌ 无效作物")
            return
        if self.funds < cost:
            self.log("💸 资金不足")
            return
        self.funds -= cost
        if action == "water":
            crop.watered_today = True
            self.log(f"💧 已浇水（田地{idx+1}）")
        elif action == "fertilize":
            crop.fertilized_today = True
            self.log(f"🌿 已施肥（田地{idx+1}）")
        elif action == "pesticide":
            crop.pesticide_today = True
            self.log(f"🧴 已喷药（田地{idx+1}）")
        self.refresh_all()

    def manual_plant(self, idx):
        crop_name = simpledialog.askstring("播种", "输入作物名：\n" + ", ".join(self.crop_types.keys()))
        if crop_name not in self.crop_types:
            self.log("❌ 无此作物")
            return
        cost = self.crop_types[crop_name].cost_per_mu
        if self.funds < cost:
            self.log("💸 资金不足")
            return
        self.fields[idx] = CropInstance(self.crop_types[crop_name], 0)
        self.funds -= cost
        self.log(f"✅ 播种成功（田地{idx+1}）：{crop_name}，支出 ￥{cost}")
        self.refresh_all()

    def manual_harvest(self, idx):
        crop = self.fields[idx]
        if not crop:
            return
        result = crop.harvest()
        if result:
            self.storage.add_crop(result)
            self.fields[idx] = None
            self.log(f"🎉 收获 {result['name']} | 营养: {result['nutrition']} | 新鲜度: {result['freshness']:.1f}%")
        else:
            self.log("❌ 无法收获")
        self.refresh_all()

    def show_weather(self):
        self.log("🌤 " + self.weather.summary())

    def refresh_all(self):
        self.update_info_bar()
        self.refresh_field()
        self.refresh_market()
        self.refresh_storage()

    def refresh_field(self):
        for i, crop in enumerate(self.fields):
            btn = self.field_buttons[i]
            if not crop:
                btn.config(text=f"田地 {i+1}\n（空地）", bg="#e0ffe0")
            elif crop.dead:
                btn.config(text=f"田地 {i+1}\n❌ 死亡", bg="#aaaaaa")
            elif crop.harvested:
                btn.config(text=f"田地 {i+1}\n🎉 已收获", bg="#d0e0ff")
            else:
                status = "✅ 成熟" if crop.matured else "🌱 生长中"
                health = "🟢" if crop.healthy else "⚠"
                btn.config(text=f"田地 {i+1}\n{crop.crop_type.name}\n{status} {health}", bg="#ffffcc")

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
            messagebox.showinfo("提示", "所有田地已种植")
            return
        field_idx = simpledialog.askinteger("播种", "选择空田编号 (1-5)")
        if not field_idx or field_idx - 1 not in empty_indices:
            self.log("❌ 播种失败：编号错误")
            return
        crop_name = simpledialog.askstring("播种", "输入作物名：\n可选：" + ", ".join(self.crop_types.keys()))
        if crop_name not in self.crop_types:
            self.log("❌ 无此作物")
            return
        cost = self.crop_types[crop_name].cost_per_mu
        if self.funds < cost:
            self.log("💸 资金不足")
            return
        self.fields[field_idx - 1] = CropInstance(self.crop_types[crop_name], 0)
        self.funds -= cost
        self.log(f"✅ 播种完成：{crop_name} | 支出 ￥{cost}")
        self.refresh_all()

    def apply_field_action(self, action, cost):
        idx = simpledialog.askinteger("田地操作", "输入田地编号 (1-5)：")
        if not idx or not (1 <= idx <= 5):
            return
        c = self.fields[idx - 1]
        if not c or c.dead:
            self.log("❌ 操作失败：该田无有效作物")
            return
        if self.funds < cost:
            self.log("❌ 操作失败：资金不足")
            return
        self.funds -= cost
        if action == "water":
            c.watered_today = True
            self.log(f"💧 浇水成功（田地{idx}）")
        elif action == "fertilize":
            c.fertilized_today = True
            self.log(f"🌿 施肥成功（田地{idx}）")
        elif action == "pesticide":
            c.pesticide_today = True
            self.log(f"🧴 喷洒农药成功（田地{idx}）")
        self.refresh_all()

    def harvest_crop(self):
        idx = simpledialog.askinteger("收获作物", "输入田地编号 (1-5)：")
        if not idx or not (1 <= idx <= 5):
            return
        c = self.fields[idx - 1]
        if not c:
            self.log("❌ 没有作物")
            return
        result = c.harvest()
        if result:
            self.storage.add_crop(result)
            self.fields[idx - 1] = None
            self.log(f"🎉 收获 {result['name']} 入库 | 营养: {result['nutrition']} | 新鲜度: {result['freshness']:.1f}%")
        else:
            self.log("❌ 尚未成熟/已死亡/已收获")
        self.refresh_all()

    def sell_crop(self):
        if not self.storage.stock:
            self.log("❌ 仓库为空")
            return
        idx = simpledialog.askinteger("出售作物", "输入作物编号：")
        if not idx or not (1 <= idx <= len(self.storage.stock)):
            return
        crop = self.storage.stock[idx - 1]
        price = self.market.get_price(crop['name'])
        name, value = self.storage.sell_crop(idx - 1, price)
        self.funds += value
        self.log(f"💰 已出售 {name} 获得 ￥{value:.2f}")
        self.refresh_all()

    def next_day(self):
        self.date += timedelta(days=1)
        self.weather = Weather(self.date)
        self.market.update_prices(self.weather)
        self.log(self.weather.summary())
        for i, crop in enumerate(self.fields):
            if crop:
                crop.update_one_day(self.weather)
                crop.update_freshness()
                self.log(f"田地{i + 1}: {crop.status()}")
        fee = self.storage.update_all()
        self.funds -= fee
        self.log(f"📦 仓储费用 ￥{fee:.2f}")
        self.refresh_all()

    def save_game(self):
        data = {
            "date": self.date.strftime("%Y-%m-%d"),
            "funds": self.funds,
            "fields": [
                {
                    "name": c.crop_type.name,
                    "days": getattr(c, "days", 0)
                } if c else None for c in self.fields
            ],
            "storage": self.storage.stock,
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write(self.log_box.get("1.0", "end"))
            self.log("💾 存档已保存")
        except Exception as e:
            self.log(f"❌ 存档失败: {e}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            self.log("⚠ 没有可读取的存档")
            return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.date = datetime.strptime(data["date"], "%Y-%m-%d")
            self.funds = data["funds"]
            self.fields = []
            for item in data["fields"]:
                if item and item["name"] in self.crop_types:
                    self.fields.append(CropInstance(self.crop_types[item["name"]], item.get("days", 0)))
                else:
                    self.fields.append(None)
            self.storage.stock = data["storage"]
            self.market.update_prices(self.weather)
            self.log("📂 存档已加载")
            self.refresh_all()
        except Exception as e:
            self.log(f"❌ 读取存档失败: {e}")
            
    ## 动态模式逻辑
    def toggle_dynamic_mode(self):
        self.dynamic_mode = not self.dynamic_mode
        if self.dynamic_mode:
            self.log("🔄 动态模式已启用")
            self.weather = WeatherDynamic(self.date)
            self.timer_running = True
            self.root.after(1000, self.update_dynamic_minute)
        else:
            self.log("⏸ 返回静态模式")
            self.timer_running = False
            
    def update_dynamic_minute(self):
        if not self.timer_running:
            return
        
        self.weather.update_minute()
        self.log(self.weather.summary())
        
        # 每分钟：向作物输入天气
        for crop in self.fields:
            if crop and not crop.dead and not crop.harvested:
                crop.absorb_weather(self.weather)
                
        # 每天凌晨自动触发生长
        if self.weather.is_new_day():
            self.date += timedelta(days=1)
            self.market.update_prices(self.weather)
            self.log('📈 市场已刷新')
            for crop in self.fields:
                if crop:
                    crop.update_one_day(self.weather)
                    crop.update_freshness()
                    self.log(crop.status())
            fee = self.storage.update_all()
            self.funds -= fee
            self.log(f"📦 仓储费用 ￥{fee:.2f}")
            self.update_info_bar()
        
        self.refresh_all()
        self.root.after(1000, self.update_dynamic_minute)
                

if __name__ == "__main__":
    root = tk.Tk()
    app = FarmerSimGUI(root)
    root.mainloop()