# Simple in-memory storage
ORDERS_DB = {"orders": {}, "next_id": 1}
DRUG_DB = {
    "aspirin": {"name": "Acetylsalicylic Acid", "price": 5.99,
                "description": "Non-steroidal anti-inflammatory drug for pain relief and fever reduction",
                "quantity": 30},
    "ibuprofen": {"name": "Ibuprofen", "price": 7.99,
                  "description": "Anti-inflammatory medication for pain and inflammation management", "quantity": 20},
    "acetaminophen": {"name": "Acetaminophen", "price": 6.99,
                      "description": "Analgesic and antipyretic medication for pain and fever control", "quantity": 25},
    "metformin": {"name": "Metformin Hydrochloride", "price": 12.50,
                  "description": "Biguanide antidiabetic medication for type 2 diabetes management", "quantity": 60},
    "lisinopril": {"name": "Lisinopril", "price": 8.75,
                   "description": "ACE inhibitor for hypertension and heart failure treatment", "quantity": 30},
    "atorvastatin": {"name": "Atorvastatin Calcium", "price": 15.25,
                     "description": "HMG-CoA reductase inhibitor for cholesterol management", "quantity": 30},
    "omeprazole": {"name": "Omeprazole", "price": 11.99,
                   "description": "Proton pump inhibitor for acid reflux and ulcer treatment", "quantity": 28},
    "amlodipine": {"name": "Amlodipine Besylate", "price": 9.50,
                   "description": "Calcium channel blocker for hypertension and angina", "quantity": 30},
    "metoprolol": {"name": "Metoprolol Tartrate", "price": 7.25,
                   "description": "Beta-blocker for hypertension and heart rhythm disorders", "quantity": 30},
    "sertraline": {"name": "Sertraline Hydrochloride", "price": 13.75,
                   "description": "Selective serotonin reuptake inhibitor for depression and anxiety", "quantity": 30}
}


def get_drug_info(drug_name):
    """Get drug information."""
    drug = DRUG_DB.get(drug_name.lower())
    if drug:
        return {
            "name": drug["name"],
            "description": drug["description"],
            "price": drug["price"],
            "quantity": drug["quantity"]
        }
    return {"error": f"Drug '{drug_name}' not found"}


def place_order(customer_name, drug_name):
    """Place a simple order with predefined quantity."""
    drug = DRUG_DB.get(drug_name.lower())
    if not drug:
        return {"error": f"Drug '{drug_name}' not found"}

    order_id = ORDERS_DB["next_id"]
    ORDERS_DB["next_id"] += 1

    order = {
        "id": order_id,
        "customer": customer_name,
        "drug": drug["name"],
        "quantity": drug["quantity"],
        "total": drug["price"],
        "status": "pending"
    }
    ORDERS_DB["orders"][order_id] = order

    return {
        "order_id": order_id,
        "message": f"Order {order_id} placed: {drug['quantity']} {drug['name']} for ${order['total']:.2f}",
        "total": order['total'],
        "quantity": drug['quantity']
    }


def lookup_order(order_id):
    """Look up an order."""
    order = ORDERS_DB["orders"].get(int(order_id))
    if order:
        return {
            "order_id": order_id,
            "customer": order["customer"],
            "drug": order["drug"],
            "quantity": order["quantity"],
            "total": order["total"],
            "status": order["status"]
        }
    return {"error": f"Order {order_id} not found"}


# Function mapping dictionary       
FUNCTION_MAP = {
    'get_drug_info': get_drug_info,
    'place_order': place_order,
    'lookup_order': lookup_order
}