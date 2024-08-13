# data_updater.py

from data_fetcher import fetch_token_price, get_token_overview, extract_pool_info, check_liquidity_removal, fetch_pool_info, fetch_pool_rolling_volume, fetch_token_holders
from database import insert_token, insert_pool, insert_holders, create_tables, insert_market_analysis
from logging_config import logger

def update_data():
    token_ids = get_all_tokens()
    for token in token_ids:
        update_token(token['contract'])

def update_token(contract_address):
    logger.info(f"Processing token {contract_address}")
    try:
        token_price = fetch_token_price(contract_address)
        token_overview = get_token_overview(contract_address)

        if token_overview:
            liquidity_removal_info = check_liquidity_removal(token_overview['creator'])
            token_db_id = insert_token(token_overview, liquidity_removal_info)
            extracted_info, pool_ids = extract_pool_info(token_price)
            if pool_ids:
                pool_rolling_vol = fetch_pool_rolling_volume(pool_ids[0])

            for pool_id in pool_ids:
                pool_data = fetch_pool_info(pool_id)
                ref_finance_url = f"https://app.ref.finance/pool/{pool_id}"

                matching_info = next((info for info in extracted_info if info['pair_address'] == pool_id), None)
                if matching_info:
                    insert_pool(ref_finance_url, matching_info)

            if extracted_info:
                price_usd = extracted_info[0]['price_native'] if extracted_info[0]['price_native'] != 'NaN' else "NaN"
                total_fee = pool_data['total_fee'] / 10000 * 100
                tvl = float(pool_data['tvl'])
                fdv = extracted_info[0]['fdv'] if extracted_info else "NaN"
                market_analysis_data = {
                    "price_usd": price_usd,
                    "total_fee": total_fee,
                    "tvl": tvl,
                    "fdv": fdv,
                    "pool_rolling_vol": pool_rolling_vol
                }
                insert_market_analysis(market_analysis_data, token_db_id)

            holders = fetch_token_holders(contract_address)
            if holders:
                for holder in holders:
                    account = holder['account']
                    amount = int(holder['amount']) / (10 ** token_overview["decimals"])
                    percentage = (amount / token_overview['total_supply']) * 100
                    insert_holders(contract_address, token_db_id, account, amount, percentage)
        else:
            logger.warning(f"Failed to fetch token overview for {contract_address}")
    except Exception as e:
        logger.error(f"Error processing token {contract_address}: {e}")
