from timer import Timer
from user import User
from questions import Question



class Exam:
    def __init__(self, user, questions):
        self.user = user
        self.questions = questions
        self.user_answers = []
        self.exam_active = False

    def start_exam(self):
        print(f"\nWelcome {self.user.username}! Your exam is starting.")
        self.exam_active = True

        correct_answers = 0

        for index, question in enumerate(self.questions):
            print(f"\nQuestion {index + 1}:")
            score = question.ask_question()  # Ask the question and calculate score
            self.user_answers.append(score)
            correct_answers += (score / question.question_score)  # Add correct answers

        print("\nExam Completed!")
        total_score = sum(self.user_answers)
        print(f"Total Score: {total_score:.2f}")
        self.user.update_score("section1", correct_answers, len(self.questions))