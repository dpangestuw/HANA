import requests
import json
import time
import logging
import os
import getpass
import csv
import random
from datetime import datetime
from colorama import Fore, Style

logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)

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
    try:
        return response.json()
    except json.JSONDecodeError:
        raise Exception("Failed to parse JSON response for access token refresh.")

def print_intro():
    print(Fore.CYAN + Style.BRIGHT + """ █████╗ ██████╗ ███████╗███╗   ███╗██╗██████╗ ███╗   ██╗""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██╔══██╗██╔══██╗██╔════╝████╗ ████║██║██╔══██╗████╗  ██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """███████║██║  ██║█████╗  ██╔████╔██║██║██║  ██║██╔██╗ ██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║██║  ██║██║╚██╗██║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """██║  ██║██████╔╝██║     ██║ ╚═╝ ██║██║██████╔╝██║ ╚████║""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝     ╚═╝╚═╝╚═════╝ ╚═╝  ╚═══╝""" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + """        Auto Draw for HANAFUDA x t.me/dpangestuw""" + Style.RESET_ALL)

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

def main():
    accounts = load_tokens_from_file()

    while True:
        for account in accounts:
            refresh_token = account['refresh_token']
            try:
                num_iterations = random.randint(20, 31)
                print(Fore.BLUE + Style.BRIGHT + f"Random of Hanafuda Draws chosen: {num_iterations}" + Style.RESET_ALL)
                token_data = refresh_access_token(refresh_token)
                access_token = token_data["access_token"]

                url = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                }

                for i in range(num_iterations):
                    query_get_hanafuda_list = {
                        "query": """
                            query getHanafudaList($groups: [YakuGroup!]) {
                              getYakuListForCurrentUser(groups: $groups) {
                                cardId
                                group
                              }
                            }
                        """,
                        "variables": {
                            "groups": ["SPRING", "SUMMER", "AUTUMN", "WINTER", "SECRET"]
                        },
                        "operationName": "getHanafudaList"
                    }
                    requests.post(url, headers=headers, json=query_get_hanafuda_list)
                    
                    mutation_execute_garden_reward = {
                        "query": """
                            mutation executeGardenRewardAction($limit: Int!) {
                              executeGardenRewardAction(limit: $limit) {
                                data {
                                  cardId
                                  group
                                }
                                isNew
                              }
                            }
                        """,
                        "variables": {"limit": 10},
                        "operationName": "executeGardenRewardAction"
                    }
                    response_garden_reward = requests.post(url, headers=headers, json=mutation_execute_garden_reward)

                    if response_garden_reward.status_code == 200:
                        garden_reward_data = response_garden_reward.json()

                        print("-" * 27) 
                        print(Fore.YELLOW + Style.BRIGHT + "Card ID  | Group   | Is New" + Style.RESET_ALL)
                        print("-" * 27) 

                        for item in garden_reward_data['data']['executeGardenRewardAction']:
                            card_id = item['data'].get('cardId')
                            group = item['data'].get('group')
                            is_new = item.get('isNew')
                            print(Fore.GREEN + Style.BRIGHT + f"{card_id:<8} | {group:<7} | {is_new}" + Style.RESET_ALL)

                    query_get_garden = {
                        "query": """
                            query GetGardenForCurrentUser {
                              getGardenForCurrentUser {
                                id
                                inviteCode
                                gardenDepositCount
                                gardenStatus {
                                  id
                                  growActionCount
                                  gardenRewardActionCount
                                }
                                gardenMilestoneRewardInfo {
                                  id
                                  gardenDepositCountWhenLastCalculated
                                  lastAcquiredAt
                                  createdAt
                                }
                                gardenMembers {
                                  id
                                  sub
                                  name
                                  iconPath
                                  depositCount
                                }
                              }
                            }
                        """,
                        "operationName": "GetGardenForCurrentUser"
                    }
                    response_garden = requests.post(url, headers=headers, json=query_get_garden)

                    if response_garden.status_code == 200:
                        garden_data = response_garden.json()

                    sleep_time = random.randint(1, 11)
                    time.sleep(sleep_time)

            except Exception as e:
                logging.error(f"Error refreshing token for account {account['name']}: {e}")
                    
        for remaining in range(600, 0, -1):
            print(Fore.YELLOW + Style.BRIGHT + f"Next in {remaining} seconds" + Style.RESET_ALL, end="\r")
            time.sleep(1)

if __name__ == "__main__":
    print_intro()
    main()
