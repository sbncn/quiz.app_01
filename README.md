Exam Application 1.0.1
This project is a simple exam application where users can log in, take a timed exam, answer questions in multiple sections, and view their results.

Features
User login with name, surname, and student number.
Timed exam (30 minutes total).
4 sections, each containing 5 questions.
Feedback on correct answers and score after each section.
Final success score and result notification at the end of the exam.
Requirements
Python 3.7 or later
Required libraries:
tkinter (for the GUI)
simpledialog, messagebox (for user input and notifications)
Installation
Clone or download this repository:
git clone https://github.com/Dusty-data/exam-application.git

The project directory:
cd exam-application

pip install -r requirements.txt

python main.py

run Docker
docker-compose run --rm exam_app

run test
python test/main_test.py

create network
docker-compose up --build