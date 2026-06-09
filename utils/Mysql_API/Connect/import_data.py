import pandas as pd
import mysql.connector
from sqlalchemy import create_engine

# MySQL数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3309,
    'user': 'root',
    'password': 'root',
    'database': 'excel_data'
}

# 创建数据表的SQL语句
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fund_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    security_code VARCHAR(20),
    security_name VARCHAR(100),
    risk_level VARCHAR(20),
    investment_type VARCHAR(50),
    association_investment_type VARCHAR(50),
    ytd_return DECIMAL(10,2),
    total_return DECIMAL(10,2),
    one_year_return DECIMAL(10,2),
    three_year_return DECIMAL(10,2),
    five_year_return DECIMAL(10,2),
    fund_size DECIMAL(20,2),
    nav DECIMAL(10,4),
    adjusted_nav DECIMAL(10,4),
    fund_manager VARCHAR(100),
    fund_custodian VARCHAR(100),
    management_fee DECIMAL(5,2),
    size_ranking INT,
    current_investment_manager TEXT,
    years_since_establishment DECIMAL(5,2)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"""

def create_database_table():
    try:
        # 连接到MySQL数据库
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建数据表
        cursor.execute(CREATE_TABLE_SQL)
        print("数据表创建成功！")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"创建数据表时出错：{str(e)}")

def import_excel_to_mysql(excel_file_path):
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file_path)
        
        # 重命名列名为英文（与数据库表结构对应）
        column_mapping = {
            '证券代码': 'security_code',
            '证券名称': 'security_name',
            '风险等级': 'risk_level',
            '投资类型': 'investment_type',
            '协会投资类型': 'association_investment_type',
            '今年以来收益率': 'ytd_return',
            '成立以来收益率': 'total_return',
            '近1年收益率': 'one_year_return',
            '近3年收益率': 'three_year_return',
            '近5年收益率': 'five_year_return',
            '产品规模(百万元)': 'fund_size',
            '单位净值(元)': 'nav',
            '复权单位净值(元)': 'adjusted_nav',
            '基金管理人': 'fund_manager',
            '基金托管人': 'fund_custodian',
            '管理费率%': 'management_fee',
            '规模同类排名': 'size_ranking',
            '投资经理(现任)': 'current_investment_manager',
            '成立年限(年)': 'years_since_establishment'
        }
        df = df.rename(columns=column_mapping)
        
        # 处理数值列中的'--'，将其转换为None（NULL）
        numeric_columns = [
            'ytd_return', 'total_return', 'one_year_return', 
            'three_year_return', 'five_year_return', 'fund_size',
            'nav', 'adjusted_nav', 'management_fee', 'years_since_establishment'
        ]
        
        for col in numeric_columns:
            df[col] = df[col].replace('--', None)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 处理size_ranking列，移除非数值部分
        df['size_ranking'] = df['size_ranking'].replace('--', None)
        df['size_ranking'] = df['size_ranking'].apply(lambda x: int(x.split('/')[0]) if pd.notnull(x) and '/' in str(x) else None)
        
        # 创建数据库连接
        engine = create_engine(
            f'mysql+mysqlconnector://{DB_CONFIG["user"]}:{DB_CONFIG["password"]}@{DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}',
            echo=False
        )
        
        # 将数据写入MySQL
        df.to_sql('fund_info', engine, if_exists='append', index=False)
        print("数据导入成功！")
        
    except Exception as e:
        print(f"导入数据时出错：{str(e)}")

"""
CREATE TABLE IF NOT EXISTS fund_info (
    id INT AUTO_INCREMENT PRIMARY KEY,                    -- 自增主键ID
    security_code VARCHAR(20),                           -- 证券代码
    security_name VARCHAR(100),                          -- 证券名称
    risk_level VARCHAR(20),                             -- 风险等级（如：中高风险、中低风险等）
    investment_type VARCHAR(50),                        -- 投资类型（如：股债平衡型基金、中长期纯债券型基金等）
    association_investment_type VARCHAR(50),            -- 协会投资类型（如：混合类、固定收益类等）
    ytd_return DECIMAL(10,2),                          -- 今年以来收益率（年初至今）
    total_return DECIMAL(10,2),                        -- 成立以来总收益率
    one_year_return DECIMAL(10,2),                     -- 近1年收益率
    three_year_return DECIMAL(10,2),                   -- 近3年收益率
    five_year_return DECIMAL(10,2),                    -- 近5年收益率
    fund_size DECIMAL(20,2),                           -- 产品规模（单位：百万元）
    nav DECIMAL(10,4),                                 -- 单位净值（单位：元）
    adjusted_nav DECIMAL(10,4),                        -- 复权单位净值（单位：元）
    fund_manager VARCHAR(100),                         -- 基金管理人（管理公司名称）
    fund_custodian VARCHAR(100),                       -- 基金托管人（托管银行名称）
    management_fee DECIMAL(5,2),                       -- 管理费率（百分比）
    size_ranking INT,                                  -- 规模同类排名（仅保存排名数字）
    current_investment_manager TEXT,                   -- 现任投资经理（可能包含多个名字）
    years_since_establishment DECIMAL(5,2)             -- 成立年限（单位：年）
)
"""

if __name__ == "__main__":
    # 首先创建数据表
    create_database_table()
    
    # 然后导入Excel数据
    excel_file_path = "test_2-20250217.xlsx"  # 请替换为实际的Excel文件路径
    import_excel_to_mysql(excel_file_path)
