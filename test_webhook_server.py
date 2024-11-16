from flask import Flask, request

app = Flask(__name__)

@app.route('/omise/webhook', methods=['POST'])
def omise_webhook():
    """
    Handle incoming Omise webhook events, inspect headers, and print the payload to the console.
    """
    # Retrieve the JSON payload
    payload = request.get_json()
    print("\n--- Received Omise Webhook Payload ---")
    print(payload)
    print("---------------------------------------\n")

    # Retrieve and print all headers
    headers = request.headers
    print("--- Incoming Request Headers ---")
    for header, value in headers.items():
        print(f"{header}: {value}")
    print("---------------------------------\n")

    # Check for the Omise-Signature header
    signature_header = headers.get('Omise-Signature')
    if signature_header:
        print(f"Omise-Signature Header Found: {signature_header}\n")
    else:
        print("Omise-Signature Header Not Found.\n")

    return '', 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)