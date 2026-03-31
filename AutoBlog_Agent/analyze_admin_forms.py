import requests
from bs4 import BeautifulSoup
import re

def analyze_admin():
    s = requests.Session()
    login_url = "https://scholarshipsguide.xyz/admin/login.php"
    login_data = {"username": "admin", "password": "Beenish@2026"}
    
    # Login
    print("Logging in...")
    r = s.post(login_url, data=login_data)
    if r.status_code != 200:
        print(f"Login failed: {r.status_code}")
        return

    # Check dashboard
    dashboard_url = "https://scholarshipsguide.xyz/admin/index.php"
    r = s.get(dashboard_url)
    soup = BeautifulSoup(r.text, 'lxml')
    
    # Look for "Add Scholarship" or "Add Post"
    links = {a.text.strip(): a['href'] for a in soup.find_all('a', href=True)}
    print("\nFound Dashboard Links:")
    for txt, url in links.items():
        print(f"- {txt}: {url}")

    # Check common post/scholarship add URLs
    potential_urls = [
        "https://scholarshipsguide.xyz/admin/add_scholarship.php",
        "https://scholarshipsguide.xyz/admin/add_post.php",
        "https://scholarshipsguide.xyz/admin/scholarships.php?action=add",
        "https://scholarshipsguide.xyz/admin/posts.php?action=add"
    ]
    
    for url in potential_urls:
        print(f"\nChecking: {url}")
        r = s.get(url)
        if r.status_code == 200 and "<form" in r.text:
            print(f"SUCCESS! Found form at {url}")
            fsoup = BeautifulSoup(r.text, 'lxml')
            form = fsoup.find('form')
            print(f"Action: {form.get('action')}")
            print(f"Method: {form.get('method')}")
            inputs = form.find_all(['input', 'textarea', 'select'])
            for i in inputs:
                print(f"  Field: {i.get('name')} (Type: {i.get('type') or i.name})")
            break
        else:
            print(f"No form or URL not found: {r.status_code}")

if __name__ == "__main__":
    analyze_admin()
