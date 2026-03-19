from app.services.ai_engine import AIEngine

req = "Harden JWT authentication by validating issuer, audience, expiry, refresh token rotation, and lock account after repeated failures"
code = """+ async def validate_jwt(token, refresh_token, user_id):
+     payload = jwt.decode(token, SECRET, algorithms=[\"HS256\"], audience=\"web\", issuer=\"devpulse\")
+     if payload[\"exp\"] < now_ts: raise AuthError(\"expired\")
+     if payload.get(\"sub\") != user_id: raise AuthError(\"subject mismatch\")
+     if not await verify_refresh(refresh_token, user_id): raise AuthError(\"refresh invalid\")
+     for attempt in range(3):
+         if await is_account_locked(user_id): break
+         else:
+             if await detect_bruteforce(user_id): await lock_account(user_id)
+     try:
+         await rotate_refresh_token(user_id)
+     except Exception:
+         await revoke_session(user_id)
+     return payload"""

print(AIEngine().get_similarity(req, code))
