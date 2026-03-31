import requests
from bs4 import BeautifulSoup
import re

def debug_post():
    s = requests.Session()
    login_url = "https://scholarshipsguide.xyz/admin/login.php"
    login_data = {"username": "admin", "password": "Beenish@2026"}
    
    print("Logging in...")
    r = s.post(login_url, data=login_data)
    
    add_url = "https://scholarshipsguide.xyz/admin/scholarships.php?action=add"
    print(f"Fetching Add Form: {add_url}")
    r = s.get(add_url)
    
    soup = BeautifulSoup(r.text, 'lxml')
    form = soup.find('form')
    if not form:
        print("Form not found!")
        return

    # Prepare payload with EVERY field
    payload = {
        "id": "",
        "title": "AstraZeneca Internship 2025-26 DEBUG",
        "category_id": "1", # Looking at common category IDs
        "country": "UK",
        "level": "Graduate",
        "funding_type": "Fully Funded",
        "host_university": "AstraZeneca UK",
        "deadline": "2026-12-31",
        "amount": "Full Stipend",
        "official_link": "https://www.astrazeneca.com/",
        "status": "publish",
        "benefits": "Testing benefits",
        "eligibility": "Testing eligibility",
        "how_to_apply": "Testing how to apply",
        "meta_title": "AstraZeneca Internship 2025-26",
        "meta_description": "Join AstraZeneca's prestigious internship program for international students.",
        "meta_keywords": "astrazeneca, internship, uk",
        "submit": "Add Scholarship" # Assuming this is the button text/name
    }
    
    # Also handle checkbox
    payload["featured"] = "on"

    print("\nSubmitting form...")
    r = s.post(add_url, data=payload)
    
    print(f"Response URL: {r.url}")
    print(f"Status Code: {r.status_code}")
    
    if "success" in r.text.lower() or "added" in r.text.lower():
        print("SUCCESS indicator found in response!")
    else:
        print("No success indicator found.")
        # Print first few lines of body to see error
        print("\nResponse Snippet:")
        print(r.text[:1000])

    # Check if it appears in the list
    list_url = "https://scholarshipsguide.xyz/admin/scholarships.php"
    r = s.get(list_url)
    if "AstraZeneca Internship 2025-26 DEBUG" in r.text:
        print("VERIFIED: Post exists in admin list!")
    else:
        print("FAILED: Post not found in admin list.")

if __name__ == "__main__":
    debug_post()
