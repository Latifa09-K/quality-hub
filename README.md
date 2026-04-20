# Quality Hub 

Quality Hub is a web-based QA Training Portal that simulates real-world testing tasks, helping users practice test case design, bug reporting, and QA workflows.

## Features
- User Authentication (Login / Register)
- Role-Based Access (User / Admin)
- Test Cases Management
- Bug Reporting System
- Admin Review System (Approve / Reject submissions)
- Interactive Quiz (ISTQB-based)
- QA Learning Resources

## Interactive Quiz
Includes an interactive quiz based on ISTQB concepts to help users test their understanding of software testing fundamentals.

## Admin Review System
Implements a review workflow where admins can evaluate submitted test cases and bug reports, approving or rejecting them to maintain quality standards.

## Technologies Used
- Flask (Python)
- HTML, CSS, JavaScript
- SQLite

## Project Structure
quality-hub/
│
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
│
├── templates/
│   └── index.html
│
├── static/
│   └── images/
│       └── quality-logo.png

## How to Run
1. Install requirements:
pip install -r requirements.txt

2. Run the project:
python app.py

3. Open browser:
http://127.0.0.1:5000

## Author
Latifa Alanazi
