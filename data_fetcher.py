import requests
from functools import lru_cache
from datetime import datetime
import time

def fetch_token_price(token_id):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_id}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Failed to parse JSON from token price response.")
            return None
    else:
        print(f"Failed to fetch token price: {response.status_code}")
        return None

@lru_cache(maxsize=1)
def get_token_overview(token_address):
    deployment_url = f"https://api3.nearblocks.io/v1/account/{token_address}/contract/deployments"
    deployment_response = requests.get(deployment_url)
    if deployment_response.status_code == 200:
        deployments = deployment_response.json().get("deployments", [])
        if deployments:
            minter_info = deployments[0]
            minter_address = minter_info.get("receipt_predecessor_account_id")
            transaction_hash = minter_info.get("transaction_hash")

            txn_url = f"https://api3.nearblocks.io/v1/txns/{transaction_hash}"
            txn_response = requests.get(txn_url)
            if txn_response.status_code == 200:
                txn_data = txn_response.json().get("txns", [])[0]
                creator_address = txn_data.get("signer_account_id")

                for receipt in txn_data.get("receipts", []):
                    for ft in receipt.get("fts", []):
                        delta_amount = int(ft.get("delta_amount", 0))
                        ft_meta = ft.get("ft_meta")

                        if ft_meta is None:
                            contract = "N/A"
                            name = "N/A"
                            symbol = "N/A"
                            decimals = 0
                        else:
                            contract = ft_meta.get("contract", "N/A")
                            name = ft_meta.get("name", "N/A")
                            symbol = ft_meta.get("symbol", "N/A")
                            decimals = int(ft_meta.get("decimals", 0))

                        total_supply = delta_amount / (10 ** decimals) if decimals else delta_amount
                        token_data = {
                            "contract": contract,
                            "name": name,
                            "symbol": symbol,
                            "decimals": decimals,
                            "total_supply": round(total_supply),
                            "minter": minter_address,
                            "creator": creator_address
                        }

                        return token_data
            else:
                print("Failed to fetch transaction data")
        else:
            print("No deployment information found.")
    else:
        print("Failed to fetch deployment data")

    return None

def extract_pool_info(token_price):
    extracted_info = []
    pool_ids = []

    if not token_price or 'pairs' not in token_price or not token_price['pairs']:
        print("No pairs information found in token price data.")
        return extracted_info, pool_ids
    
    for index, pair in enumerate(token_price['pairs']):
        pair_info = {
            'url': pair['url'],
            'pair_address': pair['pairAddress'].split('-')[1],
            'base_token': pair['baseToken'],
            'quote_token': pair['quoteToken'],
            'price_native': pair.get('priceNative', 'N/A'),
            'price_usd': pair.get('priceUsd', 'N/A'),
            'liquidity': pair['liquidity']['usd'],
            'fdv': pair.get('fdv', 'N/A'),
            'shares_total_supply': pair['liquidity']['base']
        }
        extracted_info.append(pair_info)
        pool_ids.append(pair['pairAddress'].split('-')[1])

    return extracted_info, pool_ids

def check_liquidity_removal(creator_address, retries=3, wait_time=2):
    url = f"https://api3.nearblocks.io/v1/account/{creator_address}/txns?action=FUNCTION_CALL&method=remove_liquidity&page=1&per_page=25&order=desc"
    
    for attempt in range(retries):
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            transactions = data.get("txns", [])
            
            if transactions:
                latest_transaction = transactions[0]
                transaction_hash = latest_transaction.get("transaction_hash")
                
                txn_url = f"https://api3.nearblocks.io/v1/txns/{transaction_hash}"
                txn_response = requests.get(txn_url)
                
                if txn_response.status_code == 200:
                    txn_data = txn_response.json().get("txns", [])[0]
                    
                    for receipt in txn_data.get("receipts", []):
                        for ft in receipt.get("fts", []):
                            if ft.get("cause") == "TRANSFER":
                                delta_amount = ft.get("delta_amount")
                                decimals = ft.get("ft_meta", {}).get("decimals", 0)
                                block_timestamp = int(ft.get("block_timestamp")) // 10**9
                                readable_time = datetime.utcfromtimestamp(block_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                
                                total_amount = delta_amount / (10 ** decimals) if decimals else delta_amount
                                return {
                                    "block_timestamp": readable_time,
                                    "total_amount_withdrawn": total_amount
                                }
                    print("No TRANSFER cause found in transaction receipts.")
                else:
                    print(f"Failed to fetch transaction details: {txn_response.status_code}")
            else:
                print("No remove_liquidity transactions found for the creator.")
        elif response.status_code == 500:
            print(f"Attempt {attempt + 1} failed with status code 500. Retrying...")
            time.sleep(wait_time)
        else:
            print(f"Failed to fetch remove_liquidity transactions: {response.status_code}")
            break

    print("Exceeded maximum retry attempts or no data found.")
    return None

@lru_cache(maxsize=32)
def fetch_pool_info(pool_id):
    url = f"https://api.ref.finance/get-pool?pool_id={pool_id}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Failed to parse JSON from pool info response.")
            return None
    else:
        print(f"Failed to fetch pool info: {response.status_code}")
        return None

@lru_cache(maxsize=32)
def fetch_pool_rolling_volume(pool_id):
    url = f"https://api.stats.ref.finance/api/pool/{pool_id}/rolling24hvolume/sum"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Failed to parse JSON from rolling volume response.")
            return None
    else:
        print(f"Failed to fetch pool rolling volume: {response.status_code}")
        return None

@lru_cache(maxsize=32)
def fetch_token_holders(token_address):
    token_url = f"https://api3.nearblocks.io/v1/fts/{token_address}/holders"
    response = requests.get(token_url)
    if response.status_code == 200:
        try:
            data = response.json()
            holders = data.get("holders", [])
            # If there are fewer than 50 holders, return all of them
            if len(holders) < 50:
                return holders
            else:
                return holders[:50]  # Return only the first 50 holder
        except ValueError:
            print("Failed to parse JSON from token holders response.")
            return None
    else:
        print(f"Failed to fetch token holders: {response.status_code}")
        return None
