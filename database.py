import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

pool = MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host='Errorsearching.mysql.pythonanywhere-services.com',
    database='Errorsearching$INDEXER',
    user='Errorsearching',
    password='7408185999@Talib'
)

def get_db_connection():
    return pool.get_connection()

def create_tables():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            contract TEXT,
            name TEXT,
            symbol TEXT,
            decimals INT,
            total_supply BIGINT,
            minter TEXT,
            creator TEXT,
            liquidity_removal_time TIMESTAMP,
            liquidity_removal_amount DOUBLE
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pools (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dexscreener_pair_url TEXT,
            ref_finance_url TEXT,
            pair_address TEXT,
            token_name TEXT,
            token_symbol TEXT,
            token_ca TEXT,
            quote_token_symbol TEXT,
            price_native TEXT,
            price_usd TEXT,
            liquidity DOUBLE,
            shares_total_supply DOUBLE
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            token_id INT,
            token_ca TEXT,
            holder_address TEXT,
            amount DOUBLE,
            percentage FLOAT,
            FOREIGN KEY (token_id) REFERENCES tokens(id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS current_market_analysis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            token_ca TEXT,
            price_usd TEXT,
            total_fee FLOAT,
            tvl FLOAT,
            fdv TEXT,
            rolling_24h_volume TEXT
        );
    ''')

    connection.commit()
    cursor.close()
    connection.close()

# Further functions remain the same with added error handling

def insert_token(token_data, liquidity_removal_info):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('SELECT id FROM tokens WHERE contract = %s;', (token_data['contract'],))
    result = cursor.fetchone()

    if result:
        token_id = result[0]
    else:
        liquidity_removal_time = None
        liquidity_removal_amount = None

        if liquidity_removal_info:
            liquidity_removal_time = liquidity_removal_info.get('block_timestamp')
            liquidity_removal_amount = liquidity_removal_info.get('total_amount_withdrawn')

        cursor.execute('''
            INSERT INTO tokens (contract, name, symbol, decimals, total_supply, minter, creator, liquidity_removal_time, liquidity_removal_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        ''', (token_data['contract'], token_data['name'], token_data['symbol'], token_data['decimals'],
              token_data['total_supply'], token_data['minter'], token_data['creator'],
              liquidity_removal_time, liquidity_removal_amount))

        token_id = cursor.lastrowid

    connection.commit()
    cursor.close()
    connection.close()
    return token_id

def insert_pool(ref_finance_url, matching_info):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO pools (dexscreener_pair_url, ref_finance_url, pair_address, token_name, token_symbol, token_ca, quote_token_symbol, price_native, price_usd, liquidity, shares_total_supply)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    ''', (matching_info['url'], ref_finance_url, matching_info['pair_address'],
          matching_info['base_token']['name'], matching_info['base_token']['symbol'], matching_info['base_token']['address'],
          matching_info['quote_token']['symbol'], matching_info['price_native'], matching_info['price_usd'],
          matching_info['liquidity'], matching_info['shares_total_supply']))

    connection.commit()
    cursor.close()
    connection.close()

def insert_holders(token_id, token_db_id, account, amount, percentage):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO holders (token_ca, token_id, holder_address, amount, percentage)
        VALUES (%s, %s, %s, %s, %s);
    ''', (token_id, token_db_id, account, amount, percentage))

    connection.commit()
    cursor.close()
    connection.close()

def insert_market_analysis(market_analysis_data, token_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO current_market_analysis (token_ca, price_usd, total_fee, tvl, fdv, rolling_24h_volume)
        VALUES (%s, %s, %s, %s, %s, %s);
    ''', (token_id, market_analysis_data['price_usd'],
          market_analysis_data['total_fee'], market_analysis_data['tvl'],
          market_analysis_data['fdv'], market_analysis_data['pool_rolling_vol']))

    connection.commit()
    cursor.close()
    connection.close()

def get_all_tokens():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tokens;')
    tokens = cursor.fetchall()
    cursor.close()
    connection.close()
    return tokens
def get_token_by_contract(contract_address):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tokens WHERE contract = %s;', (contract_address,))
    token = cursor.fetchone()
    cursor.close()
    connection.close()
    return token

def get_all_pools():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pools;')
    pools = cursor.fetchall()
    cursor.close()
    connection.close()
    return pools

def get_pools_by_contract(contract_address):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM pools WHERE token_ca = %s;', (contract_address,))
    pools = cursor.fetchall()
    cursor.close()
    connection.close()
    return pools

def get_holders_by_contract(contract_address):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''
        SELECT * FROM holders 
        WHERE token_ca = %s 
        ORDER BY percentage DESC;
    ''', (contract_address,))
    holders = cursor.fetchall()
    cursor.close()
    connection.close()
    return holders

def get_all_token_contracts():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT contract FROM tokens;')
    token_contracts = [row[0] for row in cursor.fetchall()]
    cursor.close()
    connection.close()
    return token_contracts

def get_market_analysis():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM current_market_analysis;')
    market_analysis = cursor.fetchall()
    cursor.close()
    connection.close()
    return market_analysis

def get_market_analysis_by_contract(contract_address):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM current_market_analysis WHERE token_ca = %s;', (contract_address,))
    market_analysis = cursor.fetchone()
    cursor.close()
    connection.close()
    return market_analysis

def add_new_token(token_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO tokens (contract)
        VALUES (%s) ON DUPLICATE KEY UPDATE contract=contract;
    ''', (token_id,))

    connection.commit()
    cursor.close()
    connection.close()
