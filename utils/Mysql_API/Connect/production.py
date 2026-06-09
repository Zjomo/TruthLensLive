import csv
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

# 初始化Faker库
fake = Faker()

# 生成参数设置
num_products = 100  # 生成100个产品
output_file = 'products_data.csv'

# 产品类别列表
categories = [
    '电子产品', '家居用品', '服装配饰',
    '美妆个护', '运动户外', '图书音像',
    '食品饮料', '母婴玩具', '汽车配件'
]


def generate_product_data(num):
    data = []
    for _ in range(num):
        product_id = str(uuid.uuid4())
        product_name = fake.word().capitalize() + ' ' + random.choice(['Pro', 'Max', 'Lite', 'Plus', '2024 Edition'])
        category = random.choice(categories)
        price = round(random.uniform(10, 1000), 2)
        stock = random.randint(0, 1000)
        description = fake.sentence(nb_words=10)
        created_at = fake.date_time_between(start_date='-2y', end_date='now')
        is_available = random.choice([True, False])
        weight = round(random.uniform(0.1, 20.0), 2) if category != '电子产品' else None
        supplier = fake.company()
        rating = round(random.uniform(1.0, 5.0), 2)

        data.append([
            product_id,
            product_name,
            category,
            price,
            stock,
            description,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            int(is_available),
            weight,
            supplier,
            rating
        ])
    return data


# 生成数据
products = generate_product_data(num_products)

# 写入CSV文件
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'product_id', 'product_name', 'category', 'price',
        'stock_quantity', 'description', 'created_at',
        'is_available', 'weight_kg', 'supplier', 'rating'
    ])
    writer.writerows(products)

print(f'成功生成 {num_products} 条产品数据到 {output_file}')