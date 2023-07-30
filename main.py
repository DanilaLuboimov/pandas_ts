import pandas as pd

df_main = pd.read_json("trial_task.json")


# 1. Найти тариф стоимости доставки для каждого склада

df_main["shipping_cost_rate"] = df_main["highway_cost"] / list(
    map(
        lambda x: sum(list(
            map(lambda y: y["quantity"], x))
        ),
        df_main["products"].to_list()
    )
)


# 2. Найти суммарное количество, суммарный доход,
# суммарный расход и суммарную прибыль для каждого товара
# (представить как таблицу со столбцами
# 'product', 'quantity', 'income', 'expenses', 'profit')

products = df_main[["products", "shipping_cost_rate"]].to_dict()

name = [
    i["product"]
    for items in products["products"].values()
    for i in items
]
quantity = [
    (k, i["quantity"])
    for k, v in products["products"].items()
    for i in v
]
price = [
    i["price"]
    for v in products["products"].values()
    for i in v
]
shipping_cost_rate = [
    products["shipping_cost_rate"][i[0]] for i in quantity
]

income = list(map(lambda x, y: x * y[1], price, quantity))
expenses = list(map(lambda x, y: x * y[1], shipping_cost_rate, quantity))
profit = list(map(lambda x, y: x + y, income, expenses))

df_products = pd.DataFrame.from_dict({
    "product": name,
    "quantity": list(i[1] for i in quantity),
    "income": income,
    "expenses": expenses,
    "profit": profit,
})

df_products = df_products.groupby("product").sum().reset_index()


# 3. Составить табличку со столбцами 'order_id' (id заказа)
# и 'order_profit' (прибыль полученная с заказа).
# А также вывести среднюю прибыль заказов

order_income = list(map(
    lambda x, e: sum(list(
        map(lambda y: y["price"] * y["quantity"], x)
    )) + e,
    df_main["products"].to_list(), df_main["highway_cost"].to_list()
))

df_order = pd.DataFrame.from_dict({
    "order_id": df_main["order_id"],
    "order_profit": order_income,
})

df_order.loc["avg_order_profit"] = df_order["order_profit"].mean(
    axis=0,
    numeric_only=True,
)
df_order.loc["avg_order_profit"]["order_id"] = None


# 4. Составить табличку типа 'warehouse_name' , 'product','quantity',
# 'profit', 'percent_profit_product_of_warehouse' (процент прибыли
# продукта заказанного из определенного склада к прибыли этого склада)

def get_percent_profit(product_profit, warehouse_name):
    warehouse_profit = sum(df_product_of_warehouse[
                               df_product_of_warehouse[
                                   "warehouse_name"] == warehouse_name
                               ]["profit"].to_list())

    result = product_profit / warehouse_profit * 100
    return round(result, 6)


products_from_warehouse = df_main[[
    "warehouse_name", "products", "order_id"
]].to_dict()

df_product_of_warehouse = pd.DataFrame.from_dict({
    "warehouse_name": [
        products_from_warehouse["warehouse_name"][k]
        for k, v in products_from_warehouse["products"].items()
        for _ in range(len(v))
    ],
    "product": name,
    "quantity": list(i[1] for i in quantity),
    "profit": profit,
})

df_product_of_warehouse = df_product_of_warehouse.groupby(
    ["warehouse_name", "product"]
).sum().reset_index()

df_product_of_warehouse[
    "percent_profit_product_of_warehouse"
] = df_product_of_warehouse.apply(
    lambda x: get_percent_profit(x["profit"], x["warehouse_name"]),
    axis=1
)


# 5. Взять предыдущую табличку и отсортировать
# 'percent_profit_product_of_warehouse' по убыванию,
# после посчитать накопленный процент. Накопленный
# процент - это новый столбец в этой табличке, который
# должен называться 'accumulated_percent_profit_product_of_warehouse'.
# По своей сути это постоянно растущая сумма отсортированного
# по убыванию столбца 'percent_profit_product_of_warehouse'.

df_accumulated_product_of_warehouse = \
    df_product_of_warehouse.sort_values(by=[
        "warehouse_name", "percent_profit_product_of_warehouse",
    ], ascending=[True, False])

df_accumulated_product_of_warehouse[
    "accumulated_percent_profit_product_of_warehouse"
] = df_accumulated_product_of_warehouse[[
    "percent_profit_product_of_warehouse", "warehouse_name"
]].groupby("warehouse_name").cumsum()


# 6. Присвоить A, B, C - категории на основании значения
# накопленного процента ('accumulated_percent_profit_product_of_warehouse').
# Если значение накопленного процента меньше или равно 70,
# то категория A. Если от 70 до 90 (включая 90), то категория Б.
# Остальное - категория C. Новый столбец обозначить в таблице как 'category'
def get_category(row):
    if row["accumulated_percent_profit_product_of_warehouse"] <= 70:
        category = "A"
    elif row["accumulated_percent_profit_product_of_warehouse"] <= 90:
        category = "B"
    else:
        category = "C"

    return category


df_accumulated_product_of_warehouse["category"] =\
    df_accumulated_product_of_warehouse.apply(get_category, axis=1)
