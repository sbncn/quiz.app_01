import random
import json
import os
#from tools.questions import Question



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Bulunduğu dosyanın dizini
BASE_DIR = os.path.dirname(BASE_DIR)  # tools klasöründen çıkıp kök dizine git

def get_data_path(file_name):
    """Helper function to construct full file paths."""
    return os.path.join(BASE_DIR, file_name)


# Question sınıfı
class Question:
    
    def __init__(self, section, question_score=5 ):
        self.section = section
        self.question_score = question_score
        self.questions = self.load_questions()
        self.answers = self.load_answers()
        self.randomized_questions = self.randomize_questions()
        self.current_question_index = 0
       


    def load_questions(self):
        """Load questions for the section from a JSON file."""
        questions_file_path = get_data_path(f'questions/section{self.section}.json')
        #print(f"Attempting to load questions from: {questions_file_path}") #deneme
        if not os.path.exists(questions_file_path):
            print(f"Error: Questions file not found: {questions_file_path}")
            return []
        
        try:
            with open(questions_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return [q for q in data if self.validate_question_format(q)]
                else:
                    print("Error: Invalid questions format. Expected a list.")
                    return []
        except Exception as e:
            print(f"Error loading questions: {str(e)}")
            return [] 


    def validate_question_format(self, question):
        """Validate the structure of a question."""
        required_keys = {"id", "question_text", "type", "score"}
        if not required_keys.issubset(question.keys()):
            return False

        if question["type"] == "True-False":
            return "options" in question and "True" in question["options"] and "False" in question["options"]
        elif question["type"] in {"Multiple-Choice", "Multiple-Answer"}:
            return "options" in question and isinstance(question["options"], list)
        elif question["type"] == "Ordering":
            return "words" in question and isinstance(question["words"], list)
        return False

    def load_answers(self):
        """Load answers from the global answers JSON file."""
        answers_file_path = get_data_path('answers/answers.json')
        
        if not os.path.exists(answers_file_path):
            print(f"Error: Answers file not found: {answers_file_path}")
            return {}
        
        try:
            with open(answers_file_path, 'r', encoding='utf-8') as file:
                answers_data = json.load(file)

            # Veriyi yeni anahtarlarla yeniden düzenleyin
            self.answers = {
                "section1": answers_data.get("answers_section1", []),
                "section2": answers_data.get("answers_section2", []),
                "section3": answers_data.get("answers_section3", []),
                "section4": answers_data.get("answers_section4", [])
            }
            return self.answers

        except Exception as e:
            print(f"Error loading answers: {str(e)}")
            return {}   
        

    def randomize_questions(self):
        """Randomize and select up to 5 questions."""
        return random.sample(self.questions, min(len(self.questions), 5))
        
    def get_correct_answer(self, question_id):
        """Retrieve the correct answer for a specific question."""
        section_key = f"section{self.section}"  # Hangi bölümün cevaplarına bakıldığını gösterir.
        section_answers = self.answers.get(section_key, [])
        
        if not section_answers:
            print(f"Warning: No answers found for section {section_key}. Check the 'answers' structure.")
        
        for answer_entry in section_answers:
            if answer_entry["id"] == question_id:
                return answer_entry.get("answer")
        return None
    
    def handle_question(self, question):
        """Handle user interaction for answering a question."""
        question_type = question.get("type", "Unknown")
        print(f"Question: {question.get('question_text', 'No question text provided')}")
        print(f"Question Type: {question_type}")
        
        try:
            if question_type == "True-False":
                return self.handle_true_false(question)

            elif question_type == "Multiple-Choice":
                return self.handle_multiple_choice(question)

            elif question_type == "Multiple-Answer":
                return self.handle_multiple_answer(question)

            elif question_type == "Ordering":
                return self.handle_ordering(question)

            else:
                print(f"Unknown question type: {question_type}")
                return None

        except Exception as e:
            print(f"Error handling question: {e}")
            return None
        

    def handle_true_false(self, question):
        """Handle True/False question."""
        print("Options: 1. True / 2. False")
        while True:
            user_answer = input("Your answer (1 or 2): ").strip()
            if user_answer in ["1", "2"]:
                return user_answer
            print("Invalid input. Please enter 1 for True or 2 for False.") 


            
    def handle_multiple_choice(self, question):
        """Handle Multiple-Choice question."""
        for idx, option in enumerate(question.get("options", []), start=1):
            print(f"{idx}. {option}")
        while True:
            user_answer = input("Please select only one option (e.g., 1, 2, 3): ").strip()
            if user_answer.isdigit() and 1 <= int(user_answer) <= len(question["options"]):
                return user_answer
            print("Invalid input. Please enter a valid option number (e.g., 1, 2, or 3).")  

    def handle_multiple_answer(self, question):
        """Handle Multiple-Answer question."""
        for idx, option in enumerate(question.get("options", []), start=1):
            print(f"{idx}. {option}")
        while True:
            user_answer = input("Please select all that apply (e.g., 1, 3 for multiple answers): ").strip()
            user_answers = user_answer.split(',')
            if all(opt.strip().isdigit() and 1 <= int(opt.strip()) <= len(question["options"]) for opt in user_answers):
                return user_answer
            print("Invalid input. Please enter valid option numbers separated by commas (e.g., 1, 2, 3).") 
    
    def handle_ordering(self, question):
        """Handle Ordering question."""
        print(f"Words to order: {', '.join(question.get('words', []))}")
        while True:
            user_answer = input("Enter the correct order (e.g., 2, 1, 4, 3): ").strip()
            if all(opt.strip().isdigit() for opt in user_answer.split(",")) and len(user_answer.split(",")) == len(question.get('words', [])):
                return user_answer
            print("Invalid input. Please enter the order of numbers correctly (e.g., 1, 2, 3, 4).")                      
    
    def ask_question(self):
        """Display the current question and handle user input."""
        if self.current_question_index >= len(self.randomized_questions):
            print("All questions in this section have been asked.")
            return 0

        question = self.randomized_questions[self.current_question_index]
        self.current_question_index += 1

        # Ask the question
        user_answer = self.handle_question(question)

        # Get the correct answer for evaluation
        correct_answer = self.get_correct_answer(question["id"])

        if correct_answer is None:
            print(f"Warning: Correct answer for question {question['id']} not found!")
        
        # Evaluate the answer
        return self.evaluate_answer(question, user_answer)
    
    def evaluate_answer(self, question, user_answer):
        """Evaluate the user's answer against the correct answer."""
        try:
            correct_answer = self.get_correct_answer(question["id"])

            if correct_answer is None:
                print("Error: Correct answer not defined!")
                return 0

            question_type = question.get("type", "Unknown")

            # True-False soruları
            if question_type == "True-False":
                correct_option = "1" if str(correct_answer).lower() == "true" else "2"
                result = question.get("score", 0) if user_answer == correct_option else 0
                return result

            # Multiple-Choice soruları
            elif question_type == "Multiple-Choice":
                try:
                    user_option_index = int(user_answer) - 1
                    correct_option_index = question["options"].index(correct_answer)
                    result = question.get("score", 0) if user_option_index == correct_option_index else 0
                    return result
                except ValueError:
                    return 0

            # Multiple-Answer soruları
            elif question_type == "Multiple-Answer":
                if isinstance(correct_answer, list):
                    user_answers = set(int(opt.strip()) for opt in user_answer.split(','))
                    correct_answers = set(int(opt.strip()) for opt in correct_answer)
                    result = question.get("score", 0) if user_answers == correct_answers else 0
                    return result
                return 0

            # Ordering soruları
            elif question_type == "Ordering":
                correct_order = [str(num) for num in correct_answer]
                user_order = [opt.strip() for opt in user_answer.split(',')]
                result = question.get("score", 0) if user_order == correct_order else 0
                return result

            return 0

        except Exception as e:
            print(f"Error evaluating answer: {e}")
            return 0
    '''   
    def start_quiz(self):
        """Start the quiz and continue until all questions are answered."""
        total_possible_score = len(self.randomized_questions) * self.question_score
        total_score = 0
        while self.current_question_index < len(self.randomized_questions):
            total_score += self.ask_question()

        percentage_score = (total_score / total_possible_score) * 100 if total_possible_score > 0 else 0
        return total_score, total_possible_score, percentage_score
    
    if __name__ == "__main__":
        sections = [1, 2, 3, 4]  # Tüm bölümleri burada belirtiyoruz
        for section in sections:
            quiz = question(section=section)
            total_score, total_possible_score, percentage_score = quiz.start_quiz()
            print(f"Your total score for Section {section}: {total_score}/{total_possible_score} ({percentage_score:.2f}%)")

        ''' 
   