import logging
import sys
import time
import os
import json

# Add parent directory to path so we can import the 'ig' package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ig import IGRestClient, IGStreamingClient, IGConfig

def main():
    logging.basicConfig(level=logging.INFO)
    print("=== IG Python Client Sample ===")
    with open("no_git_push.json", "r") as f:
        kk_config = json.load(f)
    # username = input("Username: ")
    # password = getpass("Password: ")
    # api_key = input("API Key: ")
    # acc_type = input("Account Type (DEMO/LIVE) [DEMO]: ").upper() or "DEMO"

    
    config = IGConfig(
        username=kk_config["username"],
        password=kk_config["password"],
        api_key=kk_config["api_key"],
        acc_type=kk_config["acc_type"]
    )
    
    client = IGRestClient(config)
    
    try:
        # 1. Login
        print("\nLogging in...")
        session = client.login()
        print(f"Logged in! Client ID: {session.client_id}")
        
        # 2. Get Positions
        print("\nFetching positions...")
        positions = client.get_positions()
        if not positions:
            print("No open positions.")
        else:
            for p in positions:
                print(f"Position: {p.direction} {p.size} {p.epic} @ {p.level}")
                
        # 3. Streaming (Demo)
        print("\nConnecting to streaming...")
        try:
            streamer = IGStreamingClient(session)
            streamer.connect()
            
            # Simple subscribe to first position if exists, else generic
            epic = positions[0].epic if positions else "CS.D.EURUSD.TODAY.IP"
            print(f"Subscribing to {epic}...")
            streamer.subscribe([epic])
            
            print("Streaming for 10 seconds (Ctrl+C to stop)...")
            time.sleep(10)
            
            streamer.disconnect()
        except Exception as e:
            print(f"Streaming failed: {e}")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.logout()

if __name__ == "__main__":
    main()
