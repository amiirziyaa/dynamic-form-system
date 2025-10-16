# Dynamic Form Builder System

This project is a system for creating, managing, and monitoring dynamic forms and processes. Users can build custom forms, share them via unique links, and generate reports from the collected results.

---

## ✨ Key Features

* **Dynamic Form Creation**: Build forms with various field types (Text, Select, Checkbox, etc.).
* **Access Control**: Create public forms or private, password-protected forms.
* **Process Management**: Combine forms to create linear or non-linear processes.
* **Categorization**: Organize forms and processes into custom categories for better management.
* **Advanced Reporting**: View aggregated data and real-time results.
* **API Documentation**: Powered by Django REST Framework.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your system:

* **Python 3.10+**
* **PostgreSQL** (Version 12+ recommended)
* **Git**

---

## 🚀 Getting Started (Development Environment)

Follow these steps to set up the project locally:

**1. Clone the Repository:**
```bash
git clone [your-repository-url]
cd dynamic-form-system
```

**2. Create and Activate a Virtual Environment:**
```bash
# Create a virtual environment
python -m venv venv

# Activate it (on Linux/macOS)
source venv/bin/activate

# Or on Windows
.\venv\Scripts\activate
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**4. Set Up the PostgreSQL Database:**
Create a database and a user for the project. For example:
```sql
CREATE USER form_user WITH PASSWORD 'your-password';
CREATE DATABASE dynamic_form_db;
GRANT ALL PRIVILEGES ON DATABASE dynamic_form_db TO form_user;
ALTER DATABASE dynamic_form_db OWNER TO form_user;
```

**5. Configure Environment Variables:**
Rename the `.env.example` file to `.env` and fill it with your credentials:
```ini
# .env
SECRET_KEY='your-django-secret-key'
DEBUG=True

# Database Configuration
DB_NAME=dynamic_form_db
DB_USER=form_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

**6. Run Database Migrations:**
To create the necessary tables in your database, run the following command:
```bash
python manage.py migrate
```

**7. Run the Development Server:**
```bash
python manage.py runserver
```

Your project is now running at `http://127.0.0.1:8000`!