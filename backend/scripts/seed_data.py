import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.assessment import (
    Question,
    QuestionDifficulty,
    QuestionType,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
)
from app.models.course import (
    Course,
    CourseDifficulty,
    Lesson,
    Module,
    Resource,
    ResourceType,
    Topic,
    TopicPrerequisite,
)
from app.models.mastery import (
    LearningEvent,
    LearningEventType,
    MasteryLevel,
    MasteryTrend,
    TopicMastery,
)
from app.models.recommendation import Recommendation, RecommendationPriority, RecommendationType
from app.models.study_plan import PlanType, StudyPlan, StudyPlanItem
from app.models.tutor import ChatMessage, ChatSession, MessageRole
from app.models.user import User, UserRole
from app.services.recommendation_service import RecommendationEngine


def seed_database():
    print("Starting database seeding...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_student = db.query(User).filter(User.email == "student@learnai.dev").first()
        if existing_student:
            print("Database already contains demo student. Re-seeding clean demo dataset...")
            # Optional: We can delete existing rows or let it re-populate
            db.query(QuizAnswer).delete()
            db.query(QuizAttempt).delete()
            db.query(QuizQuestion).delete()
            db.query(Question).delete()
            db.query(Quiz).delete()
            db.query(Resource).delete()
            db.query(Lesson).delete()
            db.query(TopicPrerequisite).delete()
            db.query(TopicMastery).delete()
            db.query(Recommendation).delete()
            db.query(StudyPlanItem).delete()
            db.query(StudyPlan).delete()
            db.query(ChatMessage).delete()
            db.query(ChatSession).delete()
            db.query(LearningEvent).delete()
            db.query(Topic).delete()
            db.query(Module).delete()
            db.query(Course).delete()
            db.query(User).delete()
            db.commit()

        # 1. Users
        print("Creating users...")
        admin = User(
            email="admin@learnai.dev",
            hashed_password=get_password_hash("admin123"),
            full_name="Professor Ada Lovelace (Admin)",
            role=UserRole.ADMIN,
            is_active=True
        )
        teacher = User(
            email="teacher@learnai.dev",
            hashed_password=get_password_hash("teacher123"),
            full_name="Dr. Alan Turing (Instructor)",
            role=UserRole.TEACHER,
            is_active=True
        )
        student = User(
            email="student@learnai.dev",
            hashed_password=get_password_hash("student123"),
            full_name="Alex Chen (Demo Student)",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add_all([admin, teacher, student])
        db.commit()
        db.refresh(student)

        # 2. Courses
        print("Creating courses, modules, topics, lessons, and questions...")

        # Course 1: Python
        c_python = Course(
            title="Python Programming Mastery",
            slug="python-programming-mastery",
            description="From core programming syntax and control structures to data wrangling and object-oriented design.",
            category="Software Engineering",
            difficulty=CourseDifficulty.BEGINNER,
            thumbnail_url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=60",
            is_published=True
        )
        # Course 2: DSA
        c_dsa = Course(
            title="Data Structures & Algorithms in Practice",
            slug="data-structures-and-algorithms",
            description="Master memory models, recursion, linear and tree data structures with algorithmic complexity analysis.",
            category="Computer Science",
            difficulty=CourseDifficulty.INTERMEDIATE,
            thumbnail_url="https://images.unsplash.com/photo-1516259762381-22954d7d3ad2?w=800&auto=format&fit=crop&q=60",
            is_published=True
        )
        # Course 3: Full Stack
        c_web = Course(
            title="Full-Stack Web Development with React & FastAPI",
            slug="full-stack-web-development",
            description="Production architectural patterns combining modern React TypeScript single-page apps with high-throughput FastAPI microservices.",
            category="Web Development",
            difficulty=CourseDifficulty.ADVANCED,
            thumbnail_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&auto=format&fit=crop&q=60",
            is_published=True
        )
        db.add_all([c_python, c_dsa, c_web])
        db.commit()

        # Modules for Python
        m_py_foundations = Module(course_id=c_python.id, title="Python Foundations", description="Syntax, datatypes, and branching logic", order_index=1)
        m_py_control = Module(course_id=c_python.id, title="Control Structures & Iteration", description="Loops, nested iterations, and functional decomposition", order_index=2)
        m_py_oop = Module(course_id=c_python.id, title="Object-Oriented Programming", description="Classes, encapsulation, and inheritance", order_index=3)
        db.add_all([m_py_foundations, m_py_control, m_py_oop])
        db.commit()

        # Topics for Python
        t_vars = Topic(module_id=m_py_foundations.id, title="Variables & Data Types", slug="python-variables", description="Integer, float, string, boolean representations and dynamic typing.", order_index=1, estimated_minutes=25)
        t_cond = Topic(module_id=m_py_foundations.id, title="Conditions & Boolean Logic", slug="python-conditions", description="Logical operators, truth tables, and if-elif-else constructs.", order_index=2, estimated_minutes=30)
        t_loops = Topic(module_id=m_py_control.id, title="Loops & Iteration", slug="python-loops", description="For loops, while loops, break/continue, and nested iterations.", order_index=1, estimated_minutes=45)
        t_funcs = Topic(module_id=m_py_control.id, title="Functions & Scope", slug="python-functions", description="Parameters, return values, default arguments, and local vs global scope.", order_index=2, estimated_minutes=40)
        t_oop = Topic(module_id=m_py_oop.id, title="Object-Oriented Programming", slug="python-oop", description="Classes, instances, attributes, methods, and dunder initialization.", order_index=1, estimated_minutes=50)
        db.add_all([t_vars, t_cond, t_loops, t_funcs, t_oop])
        db.commit()

        # Prerequisites: Loops requires Conditions & Variables
        prereq1 = TopicPrerequisite(topic_id=t_cond.id, prerequisite_topic_id=t_vars.id)
        prereq2 = TopicPrerequisite(topic_id=t_loops.id, prerequisite_topic_id=t_cond.id)
        prereq3 = TopicPrerequisite(topic_id=t_funcs.id, prerequisite_topic_id=t_loops.id)
        prereq4 = TopicPrerequisite(topic_id=t_oop.id, prerequisite_topic_id=t_funcs.id)
        db.add_all([prereq1, prereq2, prereq3, prereq4])
        db.commit()

        # Modules & Topics for DSA
        m_dsa_linear = Module(course_id=c_dsa.id, title="Linear Structures", description="Arrays, Lists, Stacks, Queues", order_index=1)
        m_dsa_trees = Module(course_id=c_dsa.id, title="Hierarchical Structures", description="Binary Trees and Search Trees", order_index=2)
        db.add_all([m_dsa_linear, m_dsa_trees])
        db.commit()

        t_arrays = Topic(module_id=m_dsa_linear.id, title="Arrays & Dynamic Lists", slug="dsa-arrays", description="Contiguous memory allocation and amortized resizing.", order_index=1, estimated_minutes=35)
        t_linked = Topic(module_id=m_dsa_linear.id, title="Linked Lists", slug="dsa-linked-lists", description="Pointer manipulation, node referencing, and cycle detection.", order_index=2, estimated_minutes=40)
        t_trees = Topic(module_id=m_dsa_trees.id, title="Binary Search Trees", slug="dsa-binary-trees", description="Recursive tree traversals and logarithmic search properties.", order_index=1, estimated_minutes=60)
        db.add_all([t_arrays, t_linked, t_trees])
        db.commit()

        # Modules & Topics for Web
        m_web_react = Module(course_id=c_web.id, title="Modern React Frontend", description="Components, state, and client-side lifecycle", order_index=1)
        m_web_fastapi = Module(course_id=c_web.id, title="FastAPI Backend", description="Asynchronous REST endpoints and validation", order_index=2)
        db.add_all([m_web_react, m_web_fastapi])
        db.commit()

        t_react_hooks = Topic(module_id=m_web_react.id, title="React Components & Hooks", slug="react-hooks", description="useState, useEffect, custom hooks, and reconciliation.", order_index=1, estimated_minutes=40)
        t_react_state = Topic(module_id=m_web_react.id, title="State Management & Queries", slug="react-state", description="TanStack Query caching and global state context.", order_index=2, estimated_minutes=45)
        t_fastapi_core = Topic(module_id=m_web_fastapi.id, title="FastAPI & Pydantic Core", slug="fastapi-core", description="Dependency injection, schema serialization, and async route handling.", order_index=1, estimated_minutes=45)
        db.add_all([t_react_hooks, t_react_state, t_fastapi_core])
        db.commit()

        # Lessons for Python Loops (Student's weak area)
        l_loops_1 = Lesson(
            topic_id=t_loops.id,
            title="Introduction to For & While Loops",
            slug="intro-for-while-loops",
            content_markdown="""# Iteration in Python

Loops enable execution of statements repeatedly based on conditionals or sequences.

### 1. The `for` Loop
Used for iterating over an iterable (such as a list, string, or `range`):

```python
for i in range(5):
    print(f"Current count: {i}")
```

### 2. The `while` Loop
Continues executing as long as the test condition evaluates to `True`:

```python
counter = 0
while counter < 3:
    print(counter)
    counter += 1  # Crucial: update state to prevent infinite loops!
```

### Key Differences
- Use `for` when the number of iterations is known or bound to a sequence.
- Use `while` when looping depends on dynamic conditions or external events.
""",
            order_index=1,
            duration_minutes=15,
            is_published=True
        )

        l_loops_2 = Lesson(
            topic_id=t_loops.id,
            title="Nested Loops and Complexity Patterns",
            slug="nested-loops-and-complexity",
            content_markdown="""# Nested Loops & 2D Iteration

A nested loop is a loop inside the body of an outer loop.

### Mechanics
For **every single step** of the outer loop, the inner loop runs completely through all its iterations:

```python
# Multiplying grid coordinates
for x in range(1, 4):
    for y in range(1, 4):
        print(f"({x}, {y})", end=" ")
    print()  # Newline after inner loop completes
```

### Common Pitfalls
1. **Accidental Infinite Loops**: Altering the wrong loop index variable.
2. **Time Complexity Explosion**: A nested loop over $N$ items results in $O(N^2)$ quadratic operations.
3. **Premature Break**: Using `break` inside the inner loop **only** terminates the inner loop, leaving the outer loop running!
""",
            order_index=2,
            duration_minutes=20,
            is_published=True
        )
        db.add_all([l_loops_1, l_loops_2])

        # Lessons for other topics
        l_vars = Lesson(
            topic_id=t_vars.id,
            title="Variables, Types, and Dynamic Assignment",
            slug="variables-and-types",
            content_markdown="""# Python Variables & Data Types

Python uses dynamic typing. A variable is simply a pointer or reference to an object in heap memory.

```python
user_name = "Alex"  # str
user_age = 22       # int
account_balance = 104.50 # float
is_active = True    # bool
```
""",
            order_index=1,
            duration_minutes=15,
            is_published=True
        )

        l_cond = Lesson(
            topic_id=t_cond.id,
            title="Branching Logic and Short-Circuit Evaluation",
            slug="conditions-and-branching",
            content_markdown="""# Branching Logic

Python uses `if`, `elif`, and `else` statements alongside indentation blocks.

### Short-Circuiting
Python evaluates boolean expressions left to right and stops as soon as the outcome is determined:
- In `A and B`: if `A` is `False`, `B` is never evaluated.
- In `A or B`: if `A` is `True`, `B` is never evaluated.
""",
            order_index=1,
            duration_minutes=15,
            is_published=True
        )

        l_funcs = Lesson(
            topic_id=t_funcs.id,
            title="Function Signatures, Parameters & Variable Scope",
            slug="functions-and-scope",
            content_markdown="""# Functions & Variable Scope

Define functions in Python using `def`.

### The LEGB Rule for Variable Scope
1. **L**ocal: Inside the current function.
2. **E**nclosing: Any enclosing function closures.
3. **G**lobal: Module level variables.
4. **B**uilt-in: Python default symbols like `len`, `range`.

```python
total = 100 # Global

def calculate_discount(price):
    total = price * 0.9 # Local, shadows global 'total'
    return total
```
""",
            order_index=1,
            duration_minutes=20,
            is_published=True
        )
        db.add_all([l_vars, l_cond, l_funcs])
        db.commit()

        # Questions Bank
        print("Creating Question Bank...")
        questions = [
            # Topic: Loops (Student's weak area)
            Question(
                topic_id=t_loops.id,
                question_text="What is the output of the following nested loop?\n\nfor i in range(2):\n    for j in range(3):\n        print(f'{i}{j}', end=' ')",
                explanation="The outer loop runs for i=0 and i=1. For each value of i, the inner loop runs j=0, 1, 2. Output is: 00 01 02 10 11 12.",
                difficulty=QuestionDifficulty.MEDIUM,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "00 01 02 10 11 12"},
                    {"id": "B", "text": "00 11 22"},
                    {"id": "C", "text": "00 01 10 11 20 21"},
                    {"id": "D", "text": "01 02 03 11 12 13"},
                ],
                correct_answer="A",
                concept_tag="nested_loops",
                points=2,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_loops.id,
                question_text="If a 'break' statement is executed inside an inner nested loop, what happens?",
                explanation="The 'break' statement terminates ONLY the innermost enclosing loop. Execution resumes immediately at the outer loop's next statement.",
                difficulty=QuestionDifficulty.MEDIUM,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "It terminates all nested loops and halts the entire program"},
                    {"id": "B", "text": "It terminates ONLY the innermost enclosing loop"},
                    {"id": "C", "text": "It skips to the next iteration of the inner loop like 'continue'"},
                    {"id": "D", "text": "It causes a syntax error if not wrapped in try-except"},
                ],
                correct_answer="B",
                concept_tag="nested_loops",
                points=2,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_loops.id,
                question_text="What causes a while loop to become an infinite loop in Python?",
                explanation="An infinite loop occurs when the loop condition never evaluates to False (e.g. state variables are never incremented/modified).",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "The loop condition never evaluates to False"},
                    {"id": "B", "text": "The while loop contains more than 10 iterations"},
                    {"id": "C", "text": "Using a float inside the boolean condition"},
                    {"id": "D", "text": "Forgetting to specify an 'else' block on the while loop"},
                ],
                correct_answer="A",
                concept_tag="while_loop_termination",
                points=1,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_loops.id,
                question_text="What will be printed?\n\nx = 1\nwhile x < 5:\n    x *= 2\nprint(x)",
                explanation="Initial x=1 (<5) -> x becomes 2. Next x=2 (<5) -> x becomes 4. Next x=4 (<5) -> x becomes 8. Loop terminates because 8 is not < 5. Printed value is 8.",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "4"},
                    {"id": "B", "text": "8"},
                    {"id": "C", "text": "16"},
                    {"id": "D", "text": "5"},
                ],
                correct_answer="B",
                concept_tag="while_loop_termination",
                points=1,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_loops.id,
                question_text="What is the time complexity of the following code snippet?\n\nfor i in range(n):\n    for j in range(n):\n        pass",
                explanation="Both loops run n times, producing n * n iterations = O(n^2) quadratic time complexity.",
                difficulty=QuestionDifficulty.HARD,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "O(n)"},
                    {"id": "B", "text": "O(n log n)"},
                    {"id": "C", "text": "O(n^2)"},
                    {"id": "D", "text": "O(2^n)"},
                ],
                correct_answer="C",
                concept_tag="nested_loops",
                points=3,
                is_ai_generated=False
            ),
            # Topic: Variables
            Question(
                topic_id=t_vars.id,
                question_text="Which of the following variable names is INVALID in Python?",
                explanation="Variable names in Python cannot start with a digit. '2nd_user' is invalid.",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "_user_name"},
                    {"id": "B", "text": "user_2"},
                    {"id": "C", "text": "2nd_user"},
                    {"id": "D", "text": "UserRole"},
                ],
                correct_answer="C",
                concept_tag="variable_naming",
                points=1,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_vars.id,
                question_text="What is the result of type(3 / 2) in Python 3?",
                explanation="The true division operator '/' always returns a float in Python 3. Therefore type(3 / 2) is float.",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "int"},
                    {"id": "B", "text": "float"},
                    {"id": "C", "text": "decimal"},
                    {"id": "D", "text": "double"},
                ],
                correct_answer="B",
                concept_tag="type_casting",
                points=1,
                is_ai_generated=False
            ),
            # Topic: Conditions
            Question(
                topic_id=t_cond.id,
                question_text="What does bool([]) evaluate to in Python?",
                explanation="An empty container (list, dict, set, string) evaluates to False in a boolean context (falsy value).",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "True"},
                    {"id": "B", "text": "False"},
                    {"id": "C", "text": "None"},
                    {"id": "D", "text": "Raises ValueError"},
                ],
                correct_answer="B",
                concept_tag="boolean_truthiness",
                points=1,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_cond.id,
                question_text="What is the value of result?\n\nresult = True or (10 / 0 == 1)",
                explanation="Python uses short-circuit evaluation. Because the left side is True in an 'or' expression, the right side (division by zero) is never evaluated.",
                difficulty=QuestionDifficulty.MEDIUM,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "True"},
                    {"id": "B", "text": "ZeroDivisionError is raised"},
                    {"id": "C", "text": "False"},
                    {"id": "D", "text": "None"},
                ],
                correct_answer="A",
                concept_tag="short_circuit_evaluation",
                points=2,
                is_ai_generated=False
            ),
            # Topic: Functions
            Question(
                topic_id=t_funcs.id,
                question_text="What happens when a Python function has no explicit 'return' statement?",
                explanation="Functions without a return statement (or reaching the end of the block) implicitly return None.",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "It returns 0"},
                    {"id": "B", "text": "It returns False"},
                    {"id": "C", "text": "It returns None"},
                    {"id": "D", "text": "It raises a RuntimeError"},
                ],
                correct_answer="C",
                concept_tag="return_values",
                points=1,
                is_ai_generated=False
            ),
            Question(
                topic_id=t_funcs.id,
                question_text="What is the default behavior when mutable objects (like lists) are used as default argument values in Python functions?",
                explanation="Default argument values are evaluated once when the function is defined, meaning all function calls share the exact same mutable instance.",
                difficulty=QuestionDifficulty.HARD,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "A fresh empty list is created for each function call"},
                    {"id": "B", "text": "The list is shared across subsequent calls if mutated"},
                    {"id": "C", "text": "Python raises a SyntaxError at compile time"},
                    {"id": "D", "text": "The list becomes an immutable tuple"},
                ],
                correct_answer="B",
                concept_tag="default_arguments",
                points=3,
                is_ai_generated=False
            ),
            # Topic: OOP
            Question(
                topic_id=t_oop.id,
                question_text="In Python class definitions, what does the 'self' parameter represent?",
                explanation="'self' is an explicit reference to the current instance of the class.",
                difficulty=QuestionDifficulty.EASY,
                question_type=QuestionType.MULTIPLE_CHOICE,
                options_json=[
                    {"id": "A", "text": "A reference to the parent class"},
                    {"id": "B", "text": "A reference to the current class instance"},
                    {"id": "C", "text": "A global singleton pointer"},
                    {"id": "D", "text": "The memory address of the module"},
                ],
                correct_answer="B",
                concept_tag="instance_reference",
                points=1,
                is_ai_generated=False
            ),
        ]
        db.add_all(questions)
        db.commit()

        # Quizzes
        quiz_loops_adaptive = Quiz(
            course_id=c_python.id,
            topic_id=t_loops.id,
            title="Adaptive Quiz: Python Loops & Iteration",
            description="Dynamic assessment measuring control flow, nested loops, and iteration patterns with real-time difficulty adaptation.",
            time_limit_minutes=15,
            passing_score=70.0,
            is_adaptive=True
        )
        quiz_python_foundations = Quiz(
            course_id=c_python.id,
            topic_id=t_vars.id,
            title="Python Foundations Standard Quiz",
            description="Tests variable types, mutability, and expressions.",
            time_limit_minutes=10,
            passing_score=60.0,
            is_adaptive=False
        )
        db.add_all([quiz_loops_adaptive, quiz_python_foundations])
        db.commit()

        # Associate questions to standard quiz
        qq1 = QuizQuestion(quiz_id=quiz_python_foundations.id, question_id=questions[5].id, order_index=1)
        qq2 = QuizQuestion(quiz_id=quiz_python_foundations.id, question_id=questions[6].id, order_index=2)
        db.add_all([qq1, qq2])
        db.commit()

        # 3. Topic Mastery Profiles (Realistic Mixed Mastery)
        # Alex Chen: Variables=88, Conditions=74, Loops=42 (Weak!), Functions=55, OOP=31, Arrays=65, Linked=48, Trees=20, React=72, State=58, FastAPI=82
        print("Configuring realistic student mastery telemetry...")
        mastery_data = [
            (t_vars.id, 88.0, 0.92, 6, 12, 1, MasteryTrend.IMPROVING, QuestionDifficulty.HARD, [], ["variable_naming", "type_casting"]),
            (t_cond.id, 74.0, 0.78, 4, 8, 3, MasteryTrend.STABLE, QuestionDifficulty.MEDIUM, ["short_circuit_evaluation"], ["boolean_truthiness"]),
            (t_loops.id, 42.0, 0.65, 5, 6, 8, MasteryTrend.DECLINING, QuestionDifficulty.EASY, ["nested_loops", "while_loop_termination"], ["for_range"]),
            (t_funcs.id, 55.0, 0.60, 3, 5, 4, MasteryTrend.STABLE, QuestionDifficulty.MEDIUM, ["default_arguments", "variable_scope"], ["return_values"]),
            (t_oop.id, 31.0, 0.35, 1, 1, 3, MasteryTrend.STABLE, QuestionDifficulty.EASY, ["dunder_methods", "inheritance"], []),
            (t_arrays.id, 65.0, 0.70, 3, 6, 3, MasteryTrend.IMPROVING, QuestionDifficulty.MEDIUM, [], ["dynamic_resizing"]),
            (t_linked.id, 48.0, 0.55, 2, 4, 4, MasteryTrend.DECLINING, QuestionDifficulty.EASY, ["pointer_reversal"], []),
            (t_trees.id, 20.0, 0.20, 1, 1, 4, MasteryTrend.STABLE, QuestionDifficulty.EASY, ["tree_traversals"], []),
            (t_react_hooks.id, 72.0, 0.80, 4, 8, 3, MasteryTrend.IMPROVING, QuestionDifficulty.MEDIUM, [], ["use_effect_deps"]),
            (t_react_state.id, 58.0, 0.62, 3, 5, 4, MasteryTrend.STABLE, QuestionDifficulty.MEDIUM, ["query_invalidation"], []),
            (t_fastapi_core.id, 82.0, 0.88, 5, 10, 2, MasteryTrend.IMPROVING, QuestionDifficulty.HARD, [], ["pydantic_validation", "dependency_injection"]),
        ]

        for topic_id, score, conf, att_cnt, corr, incorr, trnd, diff, weak, strong in mastery_data:
            tm = TopicMastery(
                user_id=student.id,
                topic_id=topic_id,
                mastery_score=score,
                confidence=conf,
                attempts_count=att_cnt,
                correct_answers=corr,
                incorrect_answers=incorr,
                last_practiced_at=datetime.utcnow() - timedelta(days=2 if score > 50 else 0),
                trend=trnd,
                current_difficulty=diff,
                weak_concepts=weak,
                strong_concepts=strong,
                updated_at=datetime.utcnow()
            )
            db.add(tm)
        db.commit()

        # 4. Realistic Historical Quiz Attempts & Mistake Records for Alex
        print("Creating historical quiz attempts with mistake logging...")
        # Attempt 1 on Loops (Failed, 40%)
        attempt_loops_1 = QuizAttempt(
            quiz_id=quiz_loops_adaptive.id,
            user_id=student.id,
            score=2.0,
            max_score=5.0,
            percentage=40.0,
            passed=False,
            is_completed=True,
            current_difficulty=QuestionDifficulty.EASY,
            started_at=datetime.utcnow() - timedelta(days=3, hours=2),
            completed_at=datetime.utcnow() - timedelta(days=3, hours=1, minutes=45)
        )
        db.add(attempt_loops_1)
        db.flush()

        ans1 = QuizAnswer(attempt_id=attempt_loops_1.id, question_id=questions[0].id, selected_answer="B", is_correct=False, points_awarded=0.0, time_spent_seconds=45, created_at=datetime.utcnow() - timedelta(days=3))
        ans2 = QuizAnswer(attempt_id=attempt_loops_1.id, question_id=questions[1].id, selected_answer="A", is_correct=False, points_awarded=0.0, time_spent_seconds=50, created_at=datetime.utcnow() - timedelta(days=3))
        ans3 = QuizAnswer(attempt_id=attempt_loops_1.id, question_id=questions[2].id, selected_answer="A", is_correct=True, points_awarded=1.0, time_spent_seconds=20, created_at=datetime.utcnow() - timedelta(days=3))
        ans4 = QuizAnswer(attempt_id=attempt_loops_1.id, question_id=questions[3].id, selected_answer="B", is_correct=True, points_awarded=1.0, time_spent_seconds=30, created_at=datetime.utcnow() - timedelta(days=3))
        db.add_all([ans1, ans2, ans3, ans4])

        # Attempt 2 on Foundations (Passed, 100%)
        attempt_foundations = QuizAttempt(
            quiz_id=quiz_python_foundations.id,
            user_id=student.id,
            score=2.0,
            max_score=2.0,
            percentage=100.0,
            passed=True,
            is_completed=True,
            current_difficulty=QuestionDifficulty.MEDIUM,
            started_at=datetime.utcnow() - timedelta(days=5),
            completed_at=datetime.utcnow() - timedelta(days=5, minutes=-10)
        )
        db.add(attempt_foundations)
        db.flush()

        ans_f1 = QuizAnswer(attempt_id=attempt_foundations.id, question_id=questions[5].id, selected_answer="C", is_correct=True, points_awarded=1.0, time_spent_seconds=15, created_at=datetime.utcnow() - timedelta(days=5))
        ans_f2 = QuizAnswer(attempt_id=attempt_foundations.id, question_id=questions[6].id, selected_answer="B", is_correct=True, points_awarded=1.0, time_spent_seconds=18, created_at=datetime.utcnow() - timedelta(days=5))
        db.add_all([ans_f1, ans_f2])
        db.commit()

        # 5. Learning Events (for telemetry, streaks, charts)
        print("Populating learning events over past 7 days...")
        for i in range(6, -1, -1):
            day_time = datetime.utcnow() - timedelta(days=i, hours=4)
            db.add(LearningEvent(
                user_id=student.id,
                event_type=LearningEventType.LESSON_STARTED,
                entity_type="lesson",
                entity_id=l_loops_1.id,
                event_data={"lesson_title": "Introduction to For & While Loops"},
                created_at=day_time
            ))
            db.add(LearningEvent(
                user_id=student.id,
                event_type=LearningEventType.QUESTION_ANSWERED,
                entity_type="question",
                entity_id=questions[0].id,
                event_data={"is_correct": i % 2 == 0},
                created_at=day_time + timedelta(minutes=15)
            ))

        db.commit()

        # 6. Generate Explainable Recommendations using RecommendationEngine
        print("Generating explainable recommendations...")
        RecommendationEngine.generate_recommendations_for_user(db, student.id)

        # 7. Generate Personalized Study Plan
        print("Generating weekly study plan...")
        plan = StudyPlan(
            user_id=student.id,
            title="Alex's Adaptive Mastery Acceleration Plan",
            plan_type=PlanType.WEEKLY,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=7),
            target_hours=5.5,
            is_active=True
        )
        db.add(plan)
        db.flush()

        plan_items = [
            StudyPlanItem(study_plan_id=plan.id, topic_id=t_loops.id, lesson_id=l_loops_2.id, day_of_week=0, title="Monday: Remediate Nested Loops", description="Review 2D iteration rules and solve 3 nested loop exercises.", estimated_minutes=30, is_completed=True, completed_at=datetime.utcnow() - timedelta(days=1)),
            StudyPlanItem(study_plan_id=plan.id, topic_id=t_loops.id, lesson_id=None, day_of_week=1, title="Tuesday: Adaptive Loop Practice Quiz", description="Complete an adaptive quiz aiming for >= 75% on loop termination.", estimated_minutes=20, is_completed=False),
            StudyPlanItem(study_plan_id=plan.id, topic_id=t_funcs.id, lesson_id=l_funcs.id, day_of_week=2, title="Wednesday: Functions & Mutable Defaults", description="Study python variable scope and immutable default parameters.", estimated_minutes=35, is_completed=False),
            StudyPlanItem(study_plan_id=plan.id, topic_id=t_funcs.id, lesson_id=None, day_of_week=3, title="Thursday: AI Tutor Socratic Session", description="Discuss function scope challenges with your AI Tutor.", estimated_minutes=25, is_completed=False),
            StudyPlanItem(study_plan_id=plan.id, topic_id=t_oop.id, lesson_id=None, day_of_week=4, title="Friday: OOP Foundations Preview", description="Learn class syntax and constructor initializers.", estimated_minutes=30, is_completed=False),
        ]
        db.add_all(plan_items)
        db.commit()

        # 8. AI Tutor Chat Session with history
        print("Initializing AI Tutor conversation history...")
        chat_sess = ChatSession(
            user_id=student.id,
            topic_id=t_loops.id,
            course_id=c_python.id,
            title="Tutoring: Python Loops & Iteration",
            is_active=True
        )
        db.add(chat_sess)
        db.flush()

        msg1 = ChatMessage(
            session_id=chat_sess.id,
            role=MessageRole.USER,
            content="Can you explain why my nested loop produced 6 prints instead of 5?",
            metadata_json={},
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
        msg2 = ChatMessage(
            session_id=chat_sess.id,
            role=MessageRole.ASSISTANT,
            content="""Great question! In a nested loop, the total number of iterations is the **product** of the outer loop count and inner loop count ($N \times M$), not the sum.

For example:
```python
for i in range(2):      # Outer runs 2 times (i=0, i=1)
    for j in range(3):  # Inner runs 3 times for each i
        print("Tick")
```

Here, $2 \times 3 = 6$ total ticks! Notice how the inner loop must complete all 3 iterations before `i` advances to the next count.""",
            metadata_json={
                "hints": ["Remember: inner loops run completely for each step of the outer loop.", "Use len(outer) * len(inner) to verify expected prints."],
                "follow_up_questions": ["What happens if you place a break statement inside the inner loop?"]
            },
            created_at=datetime.utcnow() - timedelta(hours=3, minutes=-1)
        )
        db.add_all([msg1, msg2])
        db.commit()

        print("\nSUCCESS! Database seeding completed successfully.")
        print(f"Demo Student: student@learnai.dev | password: student123")
        print(f"Demo Teacher: teacher@learnai.dev | password: teacher123")
        print(f"Demo Admin:   admin@learnai.dev   | password: admin123")
        print(f"Total Courses: 3 | Total Topics: 11 | Questions Bank: {len(questions)}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
