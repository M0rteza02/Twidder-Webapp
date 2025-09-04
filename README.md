# Twidder Web Application  

![Project Logo](./static/wimage.png)  

A **full-stack social networking web application** built with **Flask (Python)** on the backend and **HTML, CSS, JavaScript** on the frontend.  
It enables users to **sign up, log in, manage accounts, browse other users, and exchange posts/messages** in a secure environment.  

---

## 🚀 Features  

- **User Authentication**  
  - Secure sign-up and login with password hashing (bcrypt).  
  - Session management using tokens.  
  - WebSocket support to handle multiple sessions.  

- **Profile Management**  
  - View and update user details.  
  - Change password functionality with request signing for enhanced security.  

- **Messaging System**  
  - Post messages to your own wall.  
  - Browse other users and post messages on their wall.  
  - Reload message feeds dynamically.  
  - Drag & Drop messages to repost quickly.  

- **Security**  
  - HMAC-based request signing and timestamp validation.  
  - Prevents replay attacks and unauthorized access.  

- **Responsive UI**  
  - Designed with **Bootstrap 5** and custom CSS for mobile, tablet, and desktop.  

---

## 🛠️ Tech Stack  

**Backend:**  
- [Flask](https://flask.palletsprojects.com/)  
- [Flask-Sock](https://flask-sock.readthedocs.io/) (WebSockets)  
- [Flask-Bcrypt](https://flask-bcrypt.readthedocs.io/) (password hashing)  
- SQLite3 Database  

**Frontend:**  
- HTML5, CSS3, JavaScript (ES6)  
- [Bootstrap 5](https://getbootstrap.com/)  
- [Handlebars.js](https://handlebarsjs.com/) (templating)  
- [CryptoJS](https://cryptojs.gitbook.io/) (signature generation)  

---

## 📂 Project Structure  
├── server.py # Flask server & API routes
├── database_helper.py # Database operations
├── schema.sql # Database schema
├── database.db # SQLite database (created after init)
├── static/
│ ├── client.html # Main frontend page
│ ├── client.css # Styling
│ ├── client.js # Client-side logic
│ └── wimage.png # Logo/branding image
└── README.md

## ⚙️ Setup & Installation  

1. **Clone the repository**  
   ```bash
   git clone https://github.com/m0rteza02/twidder-webapp.git
   cd twidder-webapp

2. **Set up a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Linux/Mac
    venv\Scripts\activate      # On Windows
3. **Install dependencies**
    ```bash
    pip install flask flask-sock flask-bcrypt
4. **Install dependencies**
    ```bash
    pip install flask flask-sock flask-bcrypt
5. **Initialize the database**
    ```bash
    sqlite3 database.db < schema.sql
6. **Run the server**
    ```bash
    python server.py
7. **Open app**
    Visit: http://127.0.0.1:8000