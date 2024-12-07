import json
import random
import os
class QuestionBank:
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.files = {
            f"section{i}": os.path.join(file_path, f"questions_section{i}.json")
            for i in range(1, 5)
        }
        self.questions = self.load_questions()

    def load_questions(self):
        """
        Load questions from the JSON file.

        :return: Dictionary with sections as keys and their respective questions as values.
        """
        questions = {}
        for section, file_path in self.files.items():
            try:
                with open(file_path, 'r') as file:
                    questions[section] = json.load(file)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                questions[section] = []
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {file_path}")
                questions[section] = []
        return questions

    def add_question(self, section, question):
        """
        Add a new question to a specific section.

        :param section: The section to which the question belongs.
        :param question: The question to add (a dictionary with keys like "question_text", "options", "correct_answer").
        """
        if section not in self.questions:
            self.questions[section] = []
        self.questions[section].append(question)
        print(f"Question added to section '{section}'.")
        self.save_questions()


    def update_question(self, section, index, updated_question):
        if section in self.questions and 0 <= index < len(self.questions[section]):
            self.questions[section][index] = updated_question
            print(f"Question at index {index} in section '{section}' updated.")
            self.save_questions()
        else:
            print(f"Invalid section or index: section '{section}', index {index}.")

    def delete_question(self, section, index):
        if section in self.questions and 0 <= index < len(self.questions[section]):
            self.questions[section].pop(index)
            print(f"Question at index {index} in section '{section}' deleted.")
            self.save_questions()
        else:
            print(f"Invalid section or index: section '{section}', index {index}.")

    def save_questions(self, section):
        """
        Save the updated questions back to the JSON file.
        """
        if section in self.files:
            try:
                with open(self.files[section], 'w') as file:
                    json.dump(self.questions[section], file, indent=4)
            except Exception as e:
                print(f"Error saving questions for {section}: {e}")


    def question_menu(self):

        print("\nAvailable Sections: section1, section2, section3, section4")
        section = input("Select a section to manage (e.g., 'section1'): ").strip()

        if section not in self.questions:
            print("Invalid section. Please try again.")
            return
        
        while True:
            print("\n=== Question Menu ===")
            print("1. Add a question")
            print("2. Update a question")
            print("3. Delete a question")
            print("4. Back to Teacher Menu")
            
            choice = input("Choose an option (1-4): ").strip()

            if choice == "1":
                # section = input("Enter the section name: ").strip()
                question_text = input("Enter the question text: ").strip()
                options = input("Enter options (comma-separated): ").strip().split(',')
                correct_answer = input("Enter the correct answer: ").strip()
                question = {
                    "question_text": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "true_count": 0,
                    "false_count": 0
                }
                self.questions[section].append(question)
                self.save_questions(section)
                print("Question added successfully.")

            elif choice == "2":
                # section = input("Enter the section name: ").strip()
                try:
                    index = int(input("Enter the index of the question to update: ").strip())
                    question_text = input("Enter the updated question text: ").strip()
                    options = input("Enter updated options (comma-separated): ").strip().split(',')
                    correct_answer = input("Enter the updated correct answer: ").strip()
                    updated_question = {
                        "question_text": question_text,
                        "options": options,
                        "correct_answer": correct_answer
                    }
                    self.questions[section][index] = updated_question
                    self.save_questions(section)
                    print("Question updated successfully.")
                except (ValueError, IndexError):
                    print("Invalid index. Please try again.")

            elif choice == "3":
                try:
                    index = int(input("Enter the index of the question to delete: ").strip())
                    self.questions[section].pop(index)
                    self.save_questions(section)
                    print("Question deleted successfully.")
                except (ValueError, IndexError):
                    print("Invalid index. Please try again.")

            elif choice == "4":
                print("Logging out...")
                break

            else:
                print("Invalid choice. Please try again.")