import json
import time
import requests
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# define a function for sending sms (Using V1 for testing, but expecting failure)
def sendsms(to, msg, name):
    api_key = os.getenv("FAST2SMS_API_KEY")
    
    if not api_key:
        print("ERROR: FAST2SMS_API_KEY not set in environment (.env)")
        return False
        
    url = "https://www.fast2sms.com/dev/bulk"
    
    payload = {
        "sender_id": "FSTSMS",     
        "message": msg,
        "language": "english",
        "route": "p",              
        "numbers": to,
    }

    headers = {
        "authorization": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
    }
    
    response = requests.post(url, data=payload, headers=headers)
    
    print(f"SMS attempt sent to {to} for {name}")
    print(f"Fast2SMS Raw Response (Status {response.status_code}):")
    print(response.text)
    
    if response.status_code != 200:
        return False
        
    raw_text = response.text.lower()
    if "true" in raw_text and "fail" not in raw_text:
        return True
    
    try:
        response_json = response.json()
        if response_json.get("return") is True:
            return True
    except requests.exceptions.JSONDecodeError:
        pass 

    print(f"API FAILED for {name}. Raw response does not indicate success.")
    return False


# driver code
if __name__ == "__main__":
    try:
        with open("birthdays.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        print(f"ERROR: Could not load JSON data. {e}")
        exit()

    # Current date
    today = datetime.datetime.now().strftime("%m-%d") 
    year_now = datetime.datetime.now().strftime("%Y")
    
    updated = False
    update_list = [] 
    
    for index, person in enumerate(data):
        
        # --- FIXED: Use capitalized keys from your JSON ---
        name = person.get("Name", "N/A") 
        contact = person.get("Contact")
        
        # Birthday format parsing
        try:
            bday = datetime.datetime.strptime(person.get("Birthday", ""), "%Y-%m-%d").strftime("%m-%d")
        except (ValueError, TypeError):
            print(f"Skipping {name}: Invalid 'Birthday' format.")
            continue
            
        # Get the years SMS was sent (now as a list)
        sent_years_list = person.get("Year", []) # Defaults to empty list
        
        # Condition checking: today is birthday AND yearNow is NOT in sent_years_list
        if bday == today and year_now not in sent_years_list:
            
            msg = f"Wish you a Happy Birthday, {name}! 🎉 Wishing you a fantastic year ahead!"
            
            if sendsms(contact, msg, name): 
                update_list.append(index)
                updated = True
                
    # Update the JSON data and save
    if updated:
        for i in update_list:
            # We know the SMS was successful, so we update the list directly
            data[i]['Year'].append(year_now) 
            data[i]['Year'] = sorted(list(set(data[i]['Year']))) # Clean up and sort years

        try:
            with open("birthdays.json", "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            print("\nSuccessfully updated birthdays.json with current year tracking.")
        except Exception as e:
            print(f"ERROR: Failed to write to birthdays.json. {e}")