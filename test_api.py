import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("\n--- Testing with ADMIN user ---")
# 1. Login with Admin
resp = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "admin@finance.dev",
    "password": "Admin@123"
})
admin_token = resp.json().get("access")
print(f"1. Admin Login Status: {resp.status_code}")

# 2. Get Dashboard Summary
headers = {"Authorization": f"Bearer {admin_token}"}
resp2 = requests.get(f"{BASE_URL}/dashboard/summary/", headers=headers)
print(f"2. Admin Dashboard Summary ({resp2.status_code}):\n{json.dumps(resp2.json(), indent=2)}")

# 3. Get Income Records
resp3 = requests.get(f"{BASE_URL}/finance/records/?type=INCOME", headers=headers)
print(f"3. Admin Income Records ({resp3.status_code}):\n{json.dumps(resp3.json(), indent=2)[:500]}... (truncated)")

print("\n--- Testing with VIEWER user ---")
# 1. Login with Viewer
resp_v = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "viewer@finance.dev",
    "password": "Viewer@123"
})
viewer_token = resp_v.json().get("access")

v_headers = {"Authorization": f"Bearer {viewer_token}"}

# 2. POST to create record (should be 403)
payload = {
    "amount": "100.00",
    "transaction_type": "INCOME",
    "category": "bonus",
    "date": "2024-01-01"
}
resp_v_post = requests.post(f"{BASE_URL}/finance/records/", headers=v_headers, json=payload)
print(f"1. Viewer POST Record Status: {resp_v_post.status_code}")
print(f"   Viewer POST Record Response: {resp_v_post.json()}")

# 3. GET Dashboard summary (should be 200)
resp_v_get = requests.get(f"{BASE_URL}/dashboard/summary/", headers=v_headers)
print(f"2. Viewer Dashboard Summary Status: {resp_v_get.status_code}")
