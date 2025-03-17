import requests
import json
import time
import logging
import os
import getpass
from datetime import datetime
from colorama import Fore, Style
import sys

logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)

def current_time():
    return datetime.now().strftime('%H:%M:%S')

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

    try:
        response = requests.post(url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat mencoba untuk me-refresh token: {e}")
        return None
    except Exception as e:
        print(f"Terjadi kesalahan tak terduga: {e}")
        return None

    if response.status_code != 200:
        try:
            error_response = response.json()
            print(f"Kesalahan dalam merespon: {error_response['error']}")
        except Exception as e:
            print(f"Error dalam parsing JSON respons: {e}")
        return None

    return response.json()

def print_intro():
    print(Fore.CYAN + Style.BRIGHT + """ █████╗ ██████╗ ███████╗███╗   ███╗██╗██████╗ ███╗   ██╗""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██╔══██╗██╔══██╗██╔════╝████╗ ████║██║██╔══██╗████╗  ██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """███████║██║  ██║█████╗  ██╔████╔██║██║██║  ██║██╔██╗ ██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║  ██║██║╚██╗██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██║  ██║██████╔╝██║     ██║ ╚═╝ ██║██║██████╔╝██║ ╚████║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝  ╚═══╝""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """     Auto Grow for HANA Network x t.me/dpangestuw""" + Style.RESET_ALL)

def print_success(message):
    print(Fore.GREEN + Style.BRIGHT + message + Style.RESET_ALL)

def print_error(message):
    print(Fore.RED + Style.BRIGHT + message + Style.RESET_ALL)

def print_warning(message):
    print(Fore.YELLOW + Style.BRIGHT + message + Style.RESET_ALL)


def load_tokens_from_file():
    try:
        with open("tokens.json", "r") as token_file:
            return json.load(token_file)
    except FileNotFoundError:
        logging.error("File 'tokens.json' not found.")
        print(Fore.RED + Style.BRIGHT + "File 'tokens.json' not found." + Style.RESET_ALL)
        exit()

def restart_program():
    logging.info("Restarting the program due to an error...")
    print_error("Restarting the program due to an error...")
    os.execv(sys.executable, ['python'] + sys.argv)

def main():
    accounts = load_tokens_from_file()
    grow_all = None

    while grow_all is None:
        print(Fore.CYAN + Style.BRIGHT + "Do you want to grow all at once? (y/n): " + Fore.RESET, end="")
        user_choice = 'y'
        if user_choice == 'y':
            grow_all = True
        elif user_choice == 'n':
            grow_all = False
        else:
            print(Fore.YELLOW + Style.BRIGHT + "Invalid input. Please enter 'y' or 'n'." + Fore.RESET)

    while True:
        accounts_with_grow_action = False
        for account in accounts:
            try:
                refresh_token = account['refresh_token']
                token_data = refresh_access_token(refresh_token)
                access_token = token_data["access_token"]
                
                url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }

                response_garden_status = requests.post(
                    url,
                    headers=headers,
                    json={
                        "query": "query GetGardenForCurrentUser {\n  getGardenForCurrentUser {\n    gardenStatus {\n      growActionCount\n    }\n  }\n}",
                        "operationName": "GetGardenForCurrentUser"
                    }
                )
                response_user_name = requests.post(
                    url,
                    headers=headers,
                    json={
                        "query": "query GetCurrentMinimizedUser {\n  currentMinimizedUser {\n    id\n    sub\n    name\n    iconPath\n  }\n}",
                        "operationName": "GetCurrentMinimizedUser"
                    }
                )

                if response_garden_status.status_code == 200:
                    minimized_user_data = response_user_name.json()['data']['currentMinimizedUser']
                    grow_action_count = response_garden_status.json()['data']['getGardenForCurrentUser']['gardenStatus']['growActionCount']

                    if grow_action_count == 0:
                        print(Fore.YELLOW + Style.BRIGHT + f"[{current_time()}] No grow actions for account {minimized_user_data['name']}. Skipping...    " + Style.RESET_ALL, end='\r')
                        time.sleep(30)
                        continue

                    accounts_with_grow_action = True
                    print(Fore.YELLOW + Style.BRIGHT + "--------------------------------------------------------------------" + Style.RESET_ALL)
                    print(Fore.BLUE + Style.BRIGHT + f"[{current_time()}] Processing account {minimized_user_data['name']} with {grow_action_count} grow actions." + Style.RESET_ALL)

                    requests.post(
                        url,
                        headers=headers,
                        json={
                            "query": "mutation ExecuteGrowAction($withAll: Boolean) {\n  executeGrowAction(withAll: $withAll) {\n    baseValue\n    leveragedValue\n  }\n}",
                            "variables": {"withAll": grow_all},
                            "operationName": "ExecuteGrowAction"
                        }
                    )

                    response_current_user = requests.post(
                        url,
                        headers=headers,
                        json={
                            "query": "query CurrentUserStatus {\n  currentUser {\n    totalPoint\n  }\n}",
                            "operationName": "CurrentUserStatus"
                        }
                    )

                    if response_current_user.status_code == 200:
                        current_user_data = response_current_user.json()['data']['currentUser']
                        total_point = current_user_data['totalPoint']
                        print(Fore.GREEN + Style.BRIGHT + f"[{current_time()}] Account {minimized_user_data['name']} | Total Points: {total_point}" + Style.RESET_ALL)
                    else:
                        logging.error(f"Failed to retrieve total points for account {account['name']}.")

            except Exception as e:
                logging.error(f"Error with account {account['name']}: {e}")
                restart_program()

        if not accounts_with_grow_action:
            print(Fore.YELLOW + Style.BRIGHT + f"[{current_time()}] All accounts processed. Waiting for new grow actions..." + Style.RESET_ALL, end='\r')
            time.sleep(1200)

if __name__ == "__main__":
    print_intro()
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        restart_program()
