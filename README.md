T3X Connect | Workforce Management Portal
T3X Connect is a centralized internal management system built with Python and Flask. It was designed to replace manual spreadsheets with a secure, automated hub for employee data, attendance tracking, and grievance management.

🚀 Key Features
Role-Based Access Control (RBAC): Custom Python decorators protect sensitive HR routes while providing a clean dashboard for employees.

Attendance Tracking: Automated clock-in/out logging with an HR-facing attendance report module.

Grievance Redressal System: A formal communication channel for employees to file grievances, featuring real-time status updates (Pending/Resolved).

Password Recovery: Secure password reset functionality using itsdangerous tokens and Flask-Mail (SMTP integration).

Modern UI: Responsive front-end designed with Tailwind CSS and rendered using Jinja2 templates.



🛠️ Technical Stack
Backend: Python 3.x, Flask

Database: MySQL (Production) / SQLite (Development)

ORM: SQLAlchemy

Security: python-dotenv for environment variable management

Styling: Tailwind CSS

📦 Installation & Setup
Clone the repository:
git clone https://github.com/amityadav0099/Workforce-Management-Portal.git
cd Company_Portal


Create a Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install Dependencies:
pip install -r requirements.txt

Environment Variables Create a .env file in the root directory:
SECRET_KEY=your_secret_key
DB_URL=mysql+pymysql://user:password@localhost/db_name
MAIL_USER=your_email@gmail.com
MAIL_PASS=your_app_password

Run the Application:
python app.py