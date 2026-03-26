from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

# Load customer data from JSON file
def load_customers():
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'customers.json')
    with open(json_path, 'r') as f:
        return json.load(f)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/customers', methods=['GET'])
def get_customers():
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Validate parameters
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:  # Max limit
            limit = 100
            
        customers = load_customers()
        total = len(customers)
        
        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_customers = customers[start_idx:end_idx]
        
        response = {
            "data": paginated_customers,
            "total": total,
            "page": page,
            "limit": limit
        }
        
        return jsonify(response), 200
        
    except ValueError:
        return jsonify({"error": "Invalid page or limit parameter"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/customers/<customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customers = load_customers()
        customer = next((c for c in customers if c['customer_id'] == customer_id), None)
        
        if customer is None:
            return jsonify({"error": "Customer not found"}), 404
            
        return jsonify({"data": customer}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
