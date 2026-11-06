import os
import secrets
from datetime import datetime

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# 接続情報は環境変数から読み込む。実際の値はGitHubに含めない。
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "error_kb_app"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "error_knowledge_base_db"),
    "charset": "utf8mb4",
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def validate_error_form(form):
    data = {
        "error_name": form.get("error_name", "").strip(),
        "category": form.get("category", "").strip(),
        "situation": form.get("situation", "").strip(),
        "solution": form.get("solution", "").strip(),
    }
    errors = []
    rules = {
        "error_name": ("エラー名", 100),
        "category": ("カテゴリ", 50),
        "situation": ("発生状況", 1000),
        "solution": ("解決方法", 2000),
    }
    for key, (label, limit) in rules.items():
        if not data[key]:
            errors.append(f"{label}を入力してください。")
        elif len(data[key]) > limit:
            errors.append(f"{label}は{limit}文字以内で入力してください。")
    return data, errors


def get_error_or_404(error_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM errors WHERE id = %s", (error_id,))
        error = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()
    if error is None:
        abort(404)
    return error


@app.route("/")
def index():
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip()
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT DISTINCT category FROM errors ORDER BY category")
        categories = cursor.fetchall()
        sql = "SELECT * FROM errors WHERE 1 = 1"
        params = []
        if keyword:
            sql += " AND (error_name LIKE %s OR category LIKE %s OR situation LIKE %s OR solution LIKE %s)"
            params.extend([f"%{keyword}%"] * 4)
        if category:
            sql += " AND category = %s"
            params.append(category)
        sql += " ORDER BY id DESC"
        cursor.execute(sql, tuple(params))
        errors = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
    return render_template("index.html", errors=errors, categories=categories,
                           keyword=keyword, selected_category=category)


@app.route("/create", methods=["GET", "POST"])
def create():
    form_data = {k: "" for k in ("error_name", "category", "situation", "solution")}
    validation_errors = []
    if request.method == "POST":
        form_data, validation_errors = validate_error_form(request.form)
        if not validation_errors:
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO errors (error_name, category, situation, solution, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (form_data["error_name"], form_data["category"], form_data["situation"], form_data["solution"], datetime.now()),
                )
                connection.commit()
            finally:
                cursor.close()
                connection.close()
            flash("エラー情報を登録しました。", "success")
            return redirect(url_for("index"))
    return render_template("form.html", title="新規登録", heading="エラー情報の新規登録",
                           button="登録する", form_data=form_data,
                           validation_errors=validation_errors, error=None)


@app.route("/detail/<int:i>")
def detail(i):
    return render_template("detail.html", error=get_error_or_404(i))


@app.route("/edit/<int:i>", methods=["GET", "POST"])
def edit(i):
    error = get_error_or_404(i)
    form_data = {k: error[k] for k in ("error_name", "category", "situation", "solution")}
    validation_errors = []
    if request.method == "POST":
        form_data, validation_errors = validate_error_form(request.form)
        if not validation_errors:
            connection = get_db_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "UPDATE errors SET error_name = %s, category = %s, situation = %s, solution = %s WHERE id = %s",
                    (form_data["error_name"], form_data["category"], form_data["situation"], form_data["solution"], i),
                )
                connection.commit()
            finally:
                cursor.close()
                connection.close()
            flash("エラー情報を更新しました。", "success")
            return redirect(url_for("detail", i=i))
    return render_template("form.html", title="編集", heading="エラー情報の編集",
                           button="更新する", form_data=form_data,
                           validation_errors=validation_errors, error=error)


@app.route("/delete/<int:i>", methods=["POST"])
def delete(i):
    get_error_or_404(i)
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM errors WHERE id = %s", (i,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    flash("エラー情報を削除しました。", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
