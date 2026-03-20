import json
from urllib.request import Request, urlopen

TESTS = [
    {
        "name": "Auth aligned",
        "requirement": "Implement JWT token veware for API endpoints and reject expired tokens.",
        "code_diff": "+ async def validate_jwt(token):\n+   payload = jwt.decode(token, SECRET, algorithms=['HS256'])\n+   if payload['exp'] < now():\n+     raise AuthError('expired')\n+   return payload",
    },
    {
        "name": "Auth vs UI mismatch",
        "requirement": "Implement multi-factor authentication login verification for all admin users.",
        "code_diff": "+ .dashboard-title { color: #f59e0b; }\n+ .hero-card { border-radius: 16px; }",
    },
    {
        "name": "Heavy branching",
        "requirement": "Add resilient payment retry flow with fallback and fraud checks.",
        "code_diff": "+ if is_card_valid(card):\n+   for attempt in range(3):\n+     try:\n+       if is_suspected_fraud(card):\n+         raise FraudError()\n+       if gateway_primary_up():\n+         charge_primary(card)\n+       else:\n+         charge_fallback(card)\n+     except TimeoutError:\n+       if attempt == 2:\n+         raise\n+     except Exception:\n+       if should_route_manual_review(card):\n+         route_manual_review(card)",
    },
    {
        "name": "Perf optimization",
        "requirement": "Reduce API latency by adding response caching and avoiding repeated DB queries.",
        "code_diff": "+ cache_key = f'user:{user_id}'\n+ cached = redis.get(cache_key)\n+ if cached:\n+   return cached\n+ data = db.fetch_user(user_id)\n+ redis.set(cache_key, data, ex=120)\n+ return data",
    },
    {
        "name": "Invoice refactor vs ops logging",
        "requirement": "Refactor invoice generation module to improve maintainability and modular design.",
        "code_diff": "+ try:\n+   response = requests.post(url, json=payload)\n+   if response.status_code != 200:\n+     logger.error('bad status')\n+ except Exception as e:\n+   logger.exception(e)",
    },
]

results = []
for t in TESTS:
    payload = json.dumps({"requirement": t["requirement"], "code_diff": t["code_diff"]}).encode("utf-8")
    req = Request(
        "http://localhost:8000/api/v1/analyze",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results.append(
            {
                "test": t["name"],
                "similarity": data.get("similarity"),
                "risk": data.get("impact"),
                "complexity": data.get("complexity"),
                "summary": data.get("summary"),
            }
        )
    except Exception as exc:
        results.append(
            {
                "test": t["name"],
                "similarity": "ERROR",
                "risk": "ERROR",
                "complexity": "ERROR",
                "summary": str(exc),
            }
        )

print(json.dumps(results, indent=2))
