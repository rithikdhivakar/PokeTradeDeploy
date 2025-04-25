# seed_quiz_questions.py

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poketrade.settings')
django.setup()

from core.models import QuizQuestion

quiz_questions = [
    {
        "question_text": "What is the primary element type of ________?",
        "question_type": "element_type",
        "correct_property": "types"
    },
    {
        "question_text": "What is the base HP stat of ________?",
        "question_type": "base_hp",
        "correct_property": "stats.hp"
    },
    {
        "question_text": "Which ability is commonly associated with ________?",
        "question_type": "ability",
        "correct_property": "abilities"
    },
    {
        "question_text": "Which generation did ________ first appear in?",
        "question_type": "generation",
        "correct_property": "generation"
    },
    {
        "question_text": "From which region does ________ originate?",
        "question_type": "region",
        "correct_property": "region"
    },
    {
        "question_text": "What is the evolution stage of ________?",
        "question_type": "evolution_stage",
        "correct_property": "evolution_stage"
    }
]

for q in quiz_questions:
    QuizQuestion.objects.create(
        question_text=q["question_text"],
        question_type=q["question_type"],
        correct_property=q["correct_property"]
    )

print("✅ 6 dynamic quiz questions inserted successfully!")

