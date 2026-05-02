# School Attendance Management System

A simple school attendance management system built with Python, Flask, and SQLite. You can open this folder in Visual Studio Code and run the app locally.

## Features

- Login page for admin and teacher accounts
- Add students
- Search, edit, and delete students
- Add classes
- Edit and delete classes
- Enroll students in classes
- Record daily attendance
- Filter attendance reports by class, status, and date range
- Save data in a SQLite database file
- View recent attendance and dashboard summary data

## Project Structure

```text
school attendance management system/
|-- app.py
|-- requirements.txt
|-- attendance_app/
|   |-- __init__.py
|   |-- database.py
|   |-- routes.py
|   |-- static/
|   |   `-- style.css
|   `-- templates/
|       |-- base.html
|       |-- dashboard.html
|       |-- students.html
|       |-- student_form.html
|       |-- classes.html
|       |-- class_form.html
|       |-- attendance.html
|       `-- reports.html
`-- .vscode/
    `-- launch.json
```

## How to Run in VS Code

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
2. Open this project folder in Visual Studio Code.
3. Open the VS Code terminal.
4. Create a virtual environment:

```powershell
python -m venv .venv
```

5. Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

6. Install dependencies:

```powershell
pip install -r requirements.txt
```

7. Run the app:

```powershell
python app.py
```

8. Open this address in your browser:

```text
http://127.0.0.1:5000
```

## Push to GitHub

1. Create a new empty repository on GitHub.
2. In the VS Code terminal, run:

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

3. Replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub repository URL.

## Deploy to Render

1. Sign in to Render.
2. Click `New +` then `Web Service`.
3. Connect your GitHub account.
4. Select this repository.
5. Render should detect the settings from `render.yaml`.
6. Deploy the service.

After the first deploy, every push to your `main` branch will automatically redeploy the app.

## Database

The app automatically creates `attendance.db` in the project folder on first run.

## Default Login

- Admin: `admin` / `admin123`
- Teacher: `teacher` / `teacher123`

Important: Render's filesystem is temporary, so SQLite data will not be reliable for long-term production use there. For a serious deployed version, move from SQLite to PostgreSQL.

## Next Improvements

- Export attendance reports to Excel or PDF
- Add teacher/faculty account management
- Add password change page
- Move production database from SQLite to PostgreSQL
- Deploy online with Render or Railway
