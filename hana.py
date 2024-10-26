from web3 import Web3
import json
import time
from colorama import init, Fore, Style

init(autoreset=True)

print(Fore.CYAN + Style.BRIGHT + """ █████╗ ██████╗ ███████╗███╗   ███╗██╗██████╗ ███╗   ██╗""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """██╔══██╗██╔══██╗██╔════╝████╗ ████║██║██╔══██╗████╗  ██║""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """███████║██║  ██║█████╗  ██╔████╔██║██║██║  ██║██╔██╗ ██║""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║  ██║██║╚██╗██║""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """██║  ██║██████╔╝██║     ██║ ╚═╝ ██║██║██████╔╝██║ ╚████║""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝  ╚═══╝""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """t.me/dpangestuw31""" + Style.RESET_ALL)
print(Fore.CYAN + Style.BRIGHT + """Auto Deposit ETH for HANA Network""" + Style.RESET_ALL)

RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
AMOUNT_ETH = 0.0000000001  # Amount of ETH to be deposited

web3 = Web3(Web3.HTTPProvider(RPC_URL))

num_transactions = int(input(Fore.YELLOW + "Enter the number of transactions to be executed: " + Style.RESET_ALL))

with open("pvkey.txt", "r") as file:
    private_keys = [line.strip() for line in file if line.strip()]

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

amount_wei = web3.to_wei(AMOUNT_ETH, 'ether')
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(contract_abi))

# Track the nonces for each key
nonces = {key: web3.eth.get_transaction_count(web3.eth.account.from_key(key).address) for key in private_keys}
tx_count = 0  # Counter for transactions sent

for i in range(num_transactions):
    for private_key in private_keys:
        from_address = web3.eth.account.from_key(private_key).address
        short_from_address = from_address[:4] + "..." + from_address[-4:]

        try:
            transaction = contract.functions.depositETH().build_transaction({
                'from': from_address,
                'value': amount_wei,
                'gas': 100000,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonces[private_key],  # Use the tracked nonce
            })

            signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(Fore.GREEN + f"Transaction {i + 1} sent from {short_from_address} with hash: {tx_hash.hex()}")

            # Increment nonce after sending a transaction
            nonces[private_key] += 1
            tx_count += 1  # Increment the transaction counter

            # If 50 transactions have been sent, reset for the next batch
            if tx_count >= 50:
                tx_count = 0  # Reset the counter

            time.sleep(1)  # Adjust the delay as needed

        except Exception as e:
            if 'nonce too low' in str(e):
                print(Fore.RED + f"Nonce too low for {short_from_address}. Fetching the latest nonce...")
                nonces[private_key] = web3.eth.get_transaction_count(from_address)  # Update to the latest nonce
            else:
                print(Fore.RED + f"Error sending transaction from {short_from_address}: {str(e)}")

print(Fore.MAGENTA + "Finished sending transactions.")
