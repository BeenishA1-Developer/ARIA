import requests
from bs4 import BeautifulSoup

url = "https://scholarshipsguide.xyz/admin/login.php"
payload = {
    "username": "admin",
    "password": "Beenish@2026",
    "login": "" # Often common in PHP forms
}

session = requests.Session()
resp = session.post(url, data=payload)
print(f"Status: {resp.status_code}")
print(f"URL: {resp.url}")

# Find links in dashboard
soup = BeautifulSoup(resp.text, 'lxml')
for a in soup.find_all('a', href=True):
    print(f"Link: {a['href']} - {a.text.strip()}")
