from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from auth.db import SessionLocal, User
from auth.security import hash_password, verify_password, create_access_token, decode_token
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


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
        return jsonify({"id": user.id, "name": user.name, "email": user.email, "role": user.role})
    finally:
        db.close()
