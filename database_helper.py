import sqlite3
from flask import g
import os
import sys
import random

DATABASE = "database.db"

def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect(DATABASE)
    return g.db

def close_db():
    db = getattr(g, "db", None)
    if db is not None:
        db.close()
        db = None

def add_user(user):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password, firstname, lastname, gender, city, country) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.email, user.password, user.firstname, user.lastname, user.gender, user.city, user.country)
        )
        db.commit()
        
        return True  
    
    except Exception as e:
        
        return False  


def getUserDataByEmail(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT firstname, lastname, gender, city, country, email, password FROM users WHERE email=?", (email,))
    data = cursor.fetchone()
    
    if data is not None:
        return {
           "firstname": data[0],
            "lastname": data[1],
            "gender": data[2],
            "city": data[3],
            "country": data[4],
            "email": data[5],
        }
    else:
        return None 
    

def getPasswordByEmail(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    else: 
        return None
    
def authenticate_user(email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email, password FROM users WHERE email=? AND password=?", (email, password))
    data = cursor.fetchone()
    if data is not None:
        return True
    else:
        return False
    
def add_session(email, token):
    db = get_db()
    cursor = db.cursor()
    
   
    cursor.execute("SELECT email FROM session WHERE email = ?", (email,))
    existing = cursor.fetchone()
    
    if existing:
        
        cursor.execute("UPDATE session SET token = ? WHERE email = ?", (token, email))
    else:
        
        cursor.execute("INSERT INTO session (email, token) VALUES (?, ?)", (email, token))
    
    db.commit()
    return True


def token_exists(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT token FROM session WHERE token=?", (token,))
    data = cursor.fetchone()
    if data is not None:
        return True
    else:
        return False
    
def emailInSession(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email FROM session WHERE email=?", (email,))
    data = cursor.fetchone()
    if data is not None:
        return True
    else:
        return False
    
def check_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email FROM users WHERE email=?", (email,))
    data = cursor.fetchone()
    return data

def delete_session(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM session WHERE token=?", (token,))
    db.commit()
    return True

def getEmailByToken(token):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email FROM session WHERE token=?", (token,))
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    else:
        return None
    
def getTokenByEmail(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT token FROM session WHERE email=?", (email,))
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    else:
        return None
      
def change_password(email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password=? WHERE email=?", (password, email))
    db.commit()
    return True

def getMessagesByEmail(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT SENT_BY, SENT_TO, POST FROM posts WHERE SENT_TO=?", (email,))
    data = cursor.fetchall()
    messages = []
    for row in data:
        messages.append({
            "sent_by": row[0],
            "sent_to": row[1],
            "post": row[2],
        })
    return messages


def add_message(sent_by, sent_to, post):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO posts (SENT_BY, SENT_TO, POST) VALUES (?, ?, ?)", (sent_by, sent_to, post))
    db.commit()
    return True

