# PresencePro — Attendance Operations Platform

PresencePro is a comprehensive, real-time facial recognition attendance system built with Flask, OpenCV, and dlib. It features a modern, responsive, dark-glassmorphism user interface and a robust PostgreSQL database backend.

## ✨ Features

- **Real-Time Facial Recognition**: Mark attendance instantly using a webcam or uploaded images.
- **Student Management**: Register students with multi-image face capture for high accuracy embeddings.
- **Attendance History**: Browse, filter, and manually adjust attendance records with ease.
- **Dashboard & Analytics**: View daily summaries, attendance trends, and department breakdowns via dynamic Chart.js graphs.
- **Advanced Configuration**: Configure recognition thresholds, grace periods, cooldowns, and camera settings directly from the UI.
- **Access Control**: Secure JWT-based authentication with admin-restricted management and configuration endpoints.

## 🛠️ Technology Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-JWT-Extended
- **Machine Learning**: OpenCV, dlib, face_recognition
- **Database**: PostgreSQL
- **Frontend**: Vanilla HTML/JS, Custom CSS (Glassmorphism design system), Chart.js

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.9+**
- **PostgreSQL 14+**
- **CMake** (required for compiling dlib)
- **C++ Build Tools** (e.g., Visual Studio Build Tools on Windows)

## 🚀 Setup & Installation

1. **Clone the repository or navigate to the project folder:**
   ```bash
   cd "PresencePro—Attendance-Operations-Platform"
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   *Note: Building `dlib` can take several minutes.*
   ```bash
   pip install -r requirements.txt
   ```
   *(If `dlib` fails to build on Windows, you can try installing a pre-built wheel: `pip install dlib-bin` before installing `face_recognition`)*

4. **Database Configuration:**
   Ensure your PostgreSQL service is running and create an empty database named `attendance_db`. 
   
   Configure your connection string in the `.env` file located in the root directory:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/attendance_db
   ```

5. **Initialize the Database:**
   This will create all required tables, setup default configurations, and create the default admin user.
   ```bash
   python init_db.py
   ```

## 💻 Running the Application

Start the Flask development server:
```bash
python run.py
```

The system will be available at: **http://127.0.0.1:5000**

### Default Admin Credentials
- **Email:** `admin@admin.com`
- **Password:** `Admin@123`

## 📁 Directory Structure

- `app.py`: Main application factory
- `run.py`: Application entry point
- `init_db.py`: Database initialization script
- `config.py`: Configuration classes
- `src/`: 
  - `api/`: RESTful API blueprints
  - `ml/`: Face detection and recognition logic
  - `models/`: SQLAlchemy database models
  - `services/`: Business logic layer
  - `utils/`: Helpers and decorators
  - `views.py`: Frontend HTML template rendering
- `static/`: CSS styling and frontend JavaScript
- `templates/`: HTML Jinja2 templates
- `data/`: Storage for database files and captured face images

## 📄 License
This project is licensed under the MIT License.

## 🔭 Future Scope

- **Role-Based Access Control**: Admin-only system administration with scoped permissions per role.
- **Teacher Management**: Admin can create teacher accounts and assign subject/class ownership.
- **Class/Subject Attendance**: Teachers manage attendance by subject, class, and timetable.
- **Student Data Ownership**: Teachers can add students directly or request secure transfer from admins/other teachers.
- **Secure Collaboration**: Fine-grained access logs, approvals, and audit trails for data changes.
- **Operational Enhancements**: Automated reports, alerts, and scheduling for improved governance.
