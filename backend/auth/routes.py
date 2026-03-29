from flask import Blueprint, request, jsonify, redirect
from sqlalchemy.orm import Session
from auth.db import SessionLocal, User
from auth.security import hash_password, verify_password, create_access_token, decode_token
from datetime import datetime
import os, requests as http

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ── Google OAuth config ───────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL         = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "user")

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if role not in ("user", "admin"):
        role = "user"

    db = get_db()
    try:
        if db.query(User).filter(User.email == email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(
            name=name,
            email=email,
            password=hash_password(password),
            role=role,
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "role": user.role})
        return jsonify({
            "token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        }), 201
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password):
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_access_token({"sub": str(user.id), "role": user.role})
        return jsonify({
            "token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        })
    finally:
        db.close()


@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing token"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify({"error": "Invalid or expired token"}), 401

    db = get_db()
    try:
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"id": user.id, "name": user.name, "email": user.email,
                        "role": user.role, "avatar": user.avatar})
    finally:
        db.close()


# ── Google OAuth ──────────────────────────────────────────────────────────────

@auth_bp.route("/google/login", methods=["GET"])
def google_login():
    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google OAuth not configured"}), 503

    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    from urllib.parse import urlencode
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return redirect(url)


@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    code  = request.args.get("code")
    error = request.args.get("error")

    if error or not code:
        return redirect(f"{FRONTEND_URL}/login?error=google_denied")

    # Exchange code for tokens
    token_resp = http.post("https://oauth2.googleapis.com/token", data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    if not token_resp.ok:
        return redirect(f"{FRONTEND_URL}/login?error=token_exchange_failed")

    access_token = token_resp.json().get("access_token")

    # Fetch user info from Google
    info_resp = http.get("https://www.googleapis.com/oauth2/v2/userinfo",
                         headers={"Authorization": f"Bearer {access_token}"})
    if not info_resp.ok:
        return redirect(f"{FRONTEND_URL}/login?error=userinfo_failed")

    info      = info_resp.json()
    google_id = info.get("id")
    email     = info.get("email", "").lower()
    name      = info.get("name", email.split("@")[0])
    avatar    = info.get("picture", "")

    db = get_db()
    try:
        # Find by google_id first, then by email
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()

        if user:
            # Update google_id / avatar if missing
            if not user.google_id:
                user.google_id = google_id
            if avatar and not user.avatar:
                user.avatar = avatar
            db.commit()
        else:
            user = User(
                name=name, email=email, password=None,
                google_id=google_id, avatar=avatar,
                role="user", created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_access_token({"sub": str(user.id), "role": user.role})
        # Redirect to frontend with token in query param
        return redirect(f"{FRONTEND_URL}/auth/callback?token={jwt_token}")
    finally:
        db.close()
