import requests
import json
import logging
from web3 import Web3
import time
from colorama import init, Fore, Style

init(autoreset=True)

print(Fore.CYAN + Style.BRIGHT + """t.me/dpangestuw""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """Auto Deposit Multi Network for HANAFUDA""" + Style.RESET_ALL)
print()

def refresh_access_token(refresh_token):
    api_key = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    body = json.dumps({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })

    response = requests.post(url, headers=headers, data=body)

    if response.status_code != 200:
        error_response = response.json()
        raise Exception(f"Failed to refresh access token: {error_response['error']}")

    return response.json()

def validate_tx_hash(tx_hash):
    if not isinstance(tx_hash, str) or not tx_hash.startswith('0x') or len(tx_hash) != 66:
        raise ValueError(f"Invalid transaction hash format: {tx_hash}")
    if any(c not in '0123456789abcdefABCDEF' for c in tx_hash[2:]):
        raise ValueError(f"Transaction hash contains invalid characters: {tx_hash}")

def sync_transaction(tx_hash, chain_id, access_token):
    url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
    query = """
        mutation SyncEthereumTx($chainId: Int!, $txHash: String!) {
          syncEthereumTx(chainId: $chainId, txHash: $txHash)
        }
    """
    variables = {
        "chainId": chain_id,
        "txHash": tx_hash
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {access_token}"
    }
    
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to sync transaction: {response.json()}")
    return response.json()

def load_refresh_token_from_file():
    try:
        with open("tokens2.json", "r") as token_file:
            tokens = json.load(token_file)
            return tokens[0].get("refresh_token")
    except FileNotFoundError:
        logging.error("File 'tokens.json' not found.")
        print(Fore.RED + Style.BRIGHT + "File 'tokens.json' tidak ditemukan." + Style.RESET_ALL)
        exit()
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from 'tokens.json'.")
        exit()

def select_chain():
    print(Fore.YELLOW + Style.BRIGHT + "Select the blockchain network:" + Style.RESET_ALL)
    print(Fore.GREEN + "1. Base Mainnet" + Style.RESET_ALL)
    print(Fore.GREEN + "2. OP Mainnet" + Style.RESET_ALL)
    print(Fore.GREEN + "3. Blast Mainnet" + Style.RESET_ALL)
    print()
    choice = input(Fore.YELLOW + "Enter the number for your choice: " + Style.RESET_ALL)

    if choice == '1':
        rpc_url = "https://base-mainnet.public.blastapi.io"
        contact_address = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c" 
    elif choice == '2':
        rpc_url = "https://mainnet.optimism.io"
        contact_address = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c" 
    elif choice == '3':
        rpc_url = "https://rpc.ankr.com/blast"
        contact_address = "0x56Eff3c3F7bDdb4a58c7241b7695a72762D01baE" 
    else:
        print(Fore.RED + "Invalid choice. Exiting..." + Style.RESET_ALL)
        exit()

    return rpc_url, contact_address

RPC_URL, CONTACT_ADDRESS = select_chain()  

web3 = Web3(Web3.HTTPProvider(RPC_URL))
chain_id = web3.eth.chain_id
amount = 0.000000000000000001
value_in_wei = web3.to_wei(amount, 'ether')

num_transactions = int(input(Fore.YELLOW + "Enter the number of transactions to be executed: " + Style.RESET_ALL))

private_keys = [line.strip() for line in open("pvkey.txt") if line.strip()]

contract_abi = '''
[
    {
        "constant": false,
        "inputs": [],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
'''

contract = web3.eth.contract(address=CONTACT_ADDRESS, abi=json.loads(contract_abi))

nonces = {key: web3.eth.get_transaction_count(web3.eth.account.from_key(key).address) for key in private_keys}
tx_count = 0

refresh_token = load_refresh_token_from_file()

for i in range(num_transactions):
    for private_key in private_keys:
        from_address = web3.eth.account.from_key(private_key).address
        short_from_address = from_address[:4] + "..." + from_address[-4:]

        try:
            access_token_info = refresh_access_token(refresh_token)
            access_token = access_token_info["access_token"]
            refresh_token = access_token_info.get("refresh_token", refresh_token)

            transaction = contract.functions.depositETH().build_transaction({
                'from': from_address,
                'value': value_in_wei,
                'gas': 50000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonces[private_key],
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            tx_hash_hex = tx_receipt['transactionHash'].hex()
            print(Fore.GREEN + f"Transaction {i + 1} sent from {short_from_address} with hash: {tx_hash_hex}")

            if not tx_hash_hex.startswith('0x'):
                tx_hash_hex = '0x' + tx_hash_hex

            validate_tx_hash(tx_hash_hex)

            print(Fore.YELLOW + f"Syncing transaction with hash: {tx_hash_hex}", end='\r')

            sync_response = sync_transaction(tx_hash_hex, chain_id, access_token)

            if sync_response.get('data', {}).get('syncEthereumTx'):
                print(Fore.CYAN + f"Sync {short_from_address} successful with hash: {tx_hash_hex}")
            else:
                print(Fore.RED + "Sync failed!")
            nonces[private_key] += 1
            tx_count += 1

            time.sleep(1)

        except Exception as e:
            if 'nonce too low' in str(e):
                print(Fore.RED + f"Nonce too low for {short_from_address}. Fetching the latest nonce...")
                nonces[private_key] = web3.eth.get_transaction_count(from_address)
            else:
                print(Fore.RED + f"Error sending transaction from {short_from_address}: {str(e)}")

print(Fore.MAGENTA + "Finished sending transactions.")
