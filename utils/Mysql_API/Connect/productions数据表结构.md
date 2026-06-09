产品数据表，表名：products

| 字段名         | 数据类型      | 允许空 | 默认值            | 说明                                       |
| -------------- | ------------- | ------ | ----------------- | ------------------------------------------ |
| product_id     | CHAR(36)      | 否     | 无                | 唯一产品标识符（UUID格式）                 |
| product_name   | VARCHAR(255)  | 否     | 无                | 产品名称（自动生成含型号后缀）             |
| category       | VARCHAR(50)   | 否     | 无                | 产品分类（从预设分类列表中随机选择）       |
| price          | DECIMAL(10,2) | 否     | 无                | 产品价格（10-1000随机值，保留两位小数）    |
| stock_quantity | INT           | 否     | 无                | 库存数量（0-1000随机整数）                 |
| description    | TEXT          | 是     | NULL              | 产品描述（生成10个单词的随机句子）         |
| created_at     | DATETIME      | 是     | CURRENT_TIMESTAMP | 创建时间（随机分布在过去2年内）            |
| is_available   | BOOLEAN       | 是     | TRUE              | 上架状态（随机True/False）                 |
| weight_kg      | FLOAT         | 是     | NULL              | 产品重量（0.1-20kg随机值，电子产品无重量） |
| supplier       | VARCHAR(100)  | 是     | NULL              | 供应商名称（生成虚构公司名）               |
| rating         | DECIMAL(3,2)  | 是     | NULL              | 用户评分（1.0-5.0随机值，保留两位小数）    |

**特殊逻辑说明**：

1. `weight_kg` 字段对电子产品显示为NULL，其他分类生成实际重量值
2. `created_at` 默认使用当前时间戳，但生成数据时覆盖为随机时间
3. `product_name` 生成规则：随机单词 + 型号后缀（Pro/Max/Lite等）
4. `rating` 允许空值可用于模拟未评分商品

