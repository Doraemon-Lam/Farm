# main.py（已整合喷洒农药操作）
# 简单终端UI

from weather import Weather
from market import Market
from crops import get_default_crop_types, CropInstance
from storage import Storage
from datetime import datetime, timedelta

def main():
    print("\U0001F468‍\U0001F33E 欢迎进入 FarmerSimPy 农民模拟器")
    current_date = datetime(2025, 3, 1)
    funds = 10000

    market = Market()
    weather = Weather(current_date)
    market.update_prices(weather)
    crop_types = get_default_crop_types()
    storage = Storage()
    fields = [None for _ in range(5)]

    while True:
        print(f"\n\U0001F4C5 当前日期: {current_date.strftime('%Y-%m-%d')} | \U0001F4B0 资金: ￥{funds:.2f}")
        print("\U0001F4CB 可执行操作：")
        print("1. 查看天气")
        print("2. 查看市场价格")
        print("3. 查看田地概况")
        print("4. 播种作物")
        print("5. 浇水操作（每亩￥150）")
        print("6. 施肥操作（每亩￥100）")
        print("7. 喷洒农药（每亩￥120）")
        print("8. 收获作物（入库）")
        print("9. 查看仓库库存")
        print("10. 出售仓库作物")
        print("11. 更新仓库并结算费用")
        print("12. 推进一天")
        print("13. 退出游戏")

        choice = input("请输入编号：")

        if choice == "1":
            print(weather.summary())
        elif choice == "2":
            market.print_market_summary()
        elif choice == "3":
            for idx, crop in enumerate(fields):
                print(f"田地{idx + 1}: " + (crop.status() if crop else "（空地）"))
        elif choice == "4":
            empty_indices = [i for i, f in enumerate(fields) if f is None]
            if not empty_indices:
                print("⚠ 所有田地已种植")
                continue
            field = int(input("选择空田编号（1-5）：")) - 1
            if field not in empty_indices:
                print("❌ 输入错误")
                continue
            print("可选作物：", ", ".join(crop_types.keys()))
            crop_name = input("作物名称：")
            if crop_name not in crop_types:
                print("无此作物")
                continue
            cost = crop_types[crop_name].cost_per_mu
            if funds < cost:
                print("💸 资金不足")
                continue
            fields[field] = CropInstance(crop_types[crop_name], 0)
            funds -= cost
            print(f"✅ 播种完成，支出 ￥{cost}")
        elif choice == "5":
            idx = int(input("输入田地编号（1-5）：")) - 1
            if fields[idx] and not fields[idx].dead:
                if funds >= 150:
                    fields[idx].watered_today = True
                    funds -= 150
                    print("✅ 浇水成功")
                else:
                    print("资金不足")
            else:
                print("田地无作物")
        elif choice == "6":
            idx = int(input("输入田地编号（1-5）：")) - 1
            if fields[idx] and not fields[idx].dead:
                if funds >= 100:
                    fields[idx].fertilized_today = True
                    funds -= 100
                    print("✅ 施肥成功")
                else:
                    print("资金不足")
            else:
                print("田地无作物")
        elif choice == "7":
            idx = int(input("输入田地编号（1-5）：")) - 1
            if fields[idx] and not fields[idx].dead:
                if funds >= 120:
                    fields[idx].pesticide_today = True
                    funds -= 120
                    print("✅ 农药喷洒成功，有效降低未来2日病害概率")
                else:
                    print("资金不足")
            else:
                print("田地无作物")
        elif choice == "8":
            idx = int(input("输入田地编号（1-5）：")) - 1
            if fields[idx]:
                result = fields[idx].harvest()
                if result:
                    storage.add_crop(result)
                    print(f"🎉 收获 {result['name']} 入库 | 营养值: {result['nutrition']} | 新鲜度: {result['freshness']:.1f}%")
                    fields[idx] = None
                else:
                    print("❌ 尚未成熟或已收获/死亡")
            else:
                print("田地为空")
        elif choice == "9":
            storage.list_storage()
        elif choice == "10":
            storage.list_storage()
            idx = int(input("输入要出售的作物编号：")) - 1
            if 0 <= idx < len(storage.stock):
                crop_name, revenue = storage.sell_crop(idx, market.get_price(storage.stock[idx]["name"]))
                funds += revenue
                print(f"💰 已出售 {crop_name} 获得 ￥{revenue:.2f}")
            else:
                print("❌ 输入编号无效")
        elif choice == "11":
            cost = storage.update_all()
            funds -= cost
            print(f"📦 仓库更新完成，共支出仓储费 ￥{cost:.2f}")
        elif choice == "12":
            current_date += timedelta(days=1)
            weather = Weather(current_date)
            market.update_prices(weather)
            print(weather.summary())
            for i, crop in enumerate(fields):
                if crop:
                    crop.grow_one_day(weather)
                    crop.update_freshness()
                    print(f"田地{i+1} 状态: {crop.status()}")
            storage_fee = storage.update_all()
            funds -= storage_fee
            print(f"📦 仓库存储更新 | 支出仓储费 ￥{storage_fee:.2f}")
            print("✅ 已推进一天")
        elif choice == "13":
            print("再见！")
            break
        else:
            print("无效输入")

if __name__ == "__main__":
    main()
