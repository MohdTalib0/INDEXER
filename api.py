from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from data_updater import update_token
from database import (
    get_all_tokens, get_all_pools, get_market_analysis, 
    add_new_token, get_token_by_contract, get_holders_by_contract,
    get_market_analysis_by_contract, get_pools_by_contract
)
from logging_config import logger

app = Flask(__name__)
api = Api(app)

class TokensResource(Resource):
    def get(self):
        logger.info("Fetching all tokens")
        tokens = get_all_tokens()
        return jsonify(tokens)

class PoolsResource(Resource):
    def get(self):
        logger.info("Fetching all pools")
        pools = get_all_pools()
        return jsonify(pools)

class MarketAnalysisResource(Resource):
    def get(self):
        logger.info("Fetching market analysis")
        analysis = get_market_analysis()
        return jsonify(analysis)

class PoolByAddressResource(Resource):
    def get(self, contract_address):
        logger.info(f"Fetching pools by address {contract_address}")
        pools = get_pools_by_contract(contract_address)
        if pools:
            return jsonify(pools)
        else:
            return jsonify({'error': 'No pools found for the specified contract address'}), 404

class HolderByAddressResource(Resource):
    def get(self, contract_address):
        logger.info(f"Fetching holders by address {contract_address}")
        holders = get_holders_by_contract(contract_address)
        if holders:
            return jsonify(holders)
        else:
            return jsonify({'error': 'No holders found for the specified contract address'}), 404

class MarketAnalysisByAddressResource(Resource):
    def get(self, contract_address):
        logger.info(f"Fetching market analysis by address {contract_address}")
        analysis = get_market_analysis_by_contract(contract_address)
        if analysis:
            return jsonify(analysis)
        else:
            return jsonify({'error': 'No market analysis found for the specified contract address'}), 404

class TokenByAddressResource(Resource):
    def get(self, contract_address):
        logger.info(f"Fetching token by address {contract_address}")
        token = get_token_by_contract(contract_address)
        if token:
            return jsonify(token)
        else:
            return jsonify({'error': 'Token not found'}), 404

class AddTokenResource(Resource):
    def post(self):
        data = request.json
        contract_address = data.get('contract_address')
        logger.info(f"Adding new token {contract_address}")
        if contract_address:
            try:
                update_token(contract_address)
                return jsonify({"status": "success", "message": f"Token {contract_address} updated successfully."}), 200
            except Exception as e:
                logger.error(f"Error updating token {contract_address}: {e}")
                return jsonify({"status": "error", "message": "Failed to update token."}), 500
        else:
            logger.warning("Contract address not provided in request")
            return jsonify({"status": "error", "message": "Contract address is required."}), 400

api.add_resource(TokensResource, '/tokens')
api.add_resource(PoolsResource, '/pools')
api.add_resource(MarketAnalysisResource, '/market_analysis')
api.add_resource(PoolByAddressResource, '/pools/<string:contract_address>')
api.add_resource(HolderByAddressResource, '/holders/<string:contract_address>')
api.add_resource(MarketAnalysisByAddressResource, '/market_analysis/<string:contract_address>')
api.add_resource(TokenByAddressResource, '/token/<string:contract_address>')
api.add_resource(AddTokenResource, '/add_token')

if __name__ == '__main__':
    logger.info("Starting API server...")
    app.run(debug=True)
