from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps
import sqlite3
from werkzeug.security import check_password_hash
import datetime as dt
from markdown import markdown

# Variables
db = SQL("sqlite:///database.db.bak")
ROLES = ["admin","maintainer"]

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DAY = dt.timedelta(days=1)


# SQL Functions

# USERS

def get_users():
    users = db.execute("SELECT u_id,name,role FROM users;")
    return users

def get_user(u_id):
    user = db.execute("SELECT COUNT(u_id) AS count FROM users WHERE u_id = ?;", u_id)
    if int(user[0]["count"]) == 1:
        return True
    return False

def add_user(name, hash, role):
    db.execute("INSERT INTO users (name, hash, role) VALUES (?, ?, ?);", name, hash, role)

def delete_user(u_id):
    db.execute("BEGIN TRANSACTION;")
    db.execute("DELETE FROM users WHERE u_id = ?;", u_id)
    db.execute("DELETE FROM user_questions WHERE u_id = ?;", u_id)
    db.execute("COMMIT;")
    

def login_user(username, password):
    user = db.execute("SELECT u_id, name, hash, role FROM users WHERE name = ?", username)
    if user == None or len(user) != 1:
        return None, None, None, "User not found."
    elif check_password_hash(user[0]["hash"], password) == False:
            return None, None, None, "Invalid password."
    else:
        return user[0]["name"], user[0]["u_id"], user[0]["role"], None
    
# TOPICS

def get_topics():
    topics = db.execute("SELECT t_id, topic FROM topics ORDER BY topic;")
    return topics

def add_topic(new_topic):
    db.execute("INSERT INTO topics (topic) values (?);", new_topic)

def get_subtopics(t_id):
    subtopics =  db.execute("SELECT s_id, subtopic FROM subtopics WHERE t_id = ? ORDER BY subtopic", t_id)
    return subtopics
def add_subtopic(t_id, new_subtopic):
    db.execute("INSERT INTO subtopics (t_id, subtopic) VALUES (?, ?);", t_id, new_subtopic)

# QUESTIONS

def get_questions(t_id, s_id):
    if t_id is None or t_id =="":
        return db.execute("SELECT t.topic, s.subtopic,q.question, q.q_id, q.isMultipleChoice FROM questions q INNER JOIN subtopics s USING (s_id) INNER JOIN topics t USING (t_id);")
    elif s_id is None or s_id == "":
        return db.execute("SELECT t.topic, s.subtopic,q.question, q.q_id, q.isMultipleChoice FROM questions q INNER JOIN subtopics s USING (s_id) INNER JOIN topics t USING (t_id) WHERE t.t_id = ?;", t_id)
    else:
        return db.execute("SELECT t.topic, s.subtopic,q.question, q.q_id, q.isMultipleChoice FROM questions q INNER JOIN subtopics s USING (s_id) INNER JOIN topics t USING (t_id) WHERE t.t_id = ? AND s.s_id = ?", t_id, s_id)
   

def add_question(s_id, question, difficulty, isMultipleChoice):
    db.execute("INSERT INTO questions (s_id, question, difficulty, isMultipleChoice) values (?, ?, ?, ?)", s_id, question, difficulty, isMultipleChoice)
    q_id = db.execute("SELECT q_id FROM questions WHERE question = ? AND s_id = ?;", question, s_id)
    return q_id[0]

def update_question(q_id, question):
    print("update", question)
    db.execute("BEGIN TRANSACTION;")
    db.execute("UPDATE questions SET question = ? WHERE q_id = ?;", question, q_id)
    changes = db.execute("SELECT changes();")
    db.execute("COMMIT;")
    return changes[0]

def delete_question(q_id):
    db.execute("BEGIN TRANSACTION;")
    db.execute("DELETE FROM answers WHERE q_id = ?;", q_id)
    answers = db.execute("SELECT changes();")
    db.execute("DELETE FROM questions WHERE q_id = ?;", q_id)
    questions = db.execute("SELECT changes();")
    db.execute("COMMIT;")
    

    return questions[0]["changes()"], answers[0]["changes()"]

# ANSWERS

def get_answers(q_ids):
    answers = db.execute("SELECT row_number() OVER (order by random()) AS random, q_id, a_id, answer, comment, is_true FROM answers WHERE q_id IN (?) ORDER BY q_id, random;", q_ids)
    return answers

def add_answers(answers):
    db.execute("BEGIN TRANSACTION;")
    for answer in answers:
        db.execute("INSERT INTO answers (q_id, answer, comment, is_true) values (?, ?, ?, ?);", int(answer["q_id"]), answer["answer"], answer["comment"], int(answer["true"]))
    db.execute("COMMIT;")





# TESTS

def create_test(t_id, s_id, count):
    print(count, type(count))
    
    if count == "":
        count = None
    else:
        count = int(count)

    questions = get_questions(t_id, s_id)
    questions = questions[0:count]
    q_ids = [q_id["q_id"] for q_id in questions]
    answers = get_answers(q_ids)
    return questions, answers

def get_questions_result(q_ids):
    questions = db.execute("SELECT q_id, question, isMultipleChoice FROM questions WHERE q_id IN (?);", q_ids)
    return questions

def verify_test(u_id,test):
    update_db = None
    # Check user
    if not (u_id is None or u_id == ""):
        update_db = True if get_user(int(u_id)) == True else None
        print("user found",update_db)

    now = dt.datetime.today().strftime("%Y-%m-%d")

    questions = []
    for q in test:
        questions.append(q)

    answers = db.execute("SELECT q_id, (SELECT COUNT(*) FROM answers b WHERE a.q_id = b.q_id) as count,a_id , answer FROM answers a WHERE q_id IN (?) AND is_true = 1;", questions)
    
     
    for q in test:
        right_answers = [a["a_id"] for a in answers if a["q_id"] == int(q)]
        right_answers = set(right_answers)
        right_count = len(right_answers)

        user_answers = set(test[q])
        user_right = user_answers & right_answers
        user_right_count = len(user_right)
        wrong_answers = user_answers - right_answers
        wrong_answers = len(wrong_answers)
        # Using fail for an update counter in db
        passed = 0 if wrong_answers > 0 or user_right_count < right_count else 1
        if update_db is True:
            exists = db.execute("SELECT count(*) AS count FROM user_questions WHERE u_id = ? AND q_id = ?;", u_id, int(q))
            if len(exists) == 1 and exists[0]["count"] == 1:
                db.execute("UPDATE user_questions SET timesDone = timesDone + 1, timesRight = timesRight + ?, lastDate = ? WHERE u_id = ? AND q_id = ?;", passed, now, u_id, int(q))
            else:
                db.execute("INSERT INTO user_questions (u_id, q_id, timesDone, timesRight, lastDate) VALUES (?, ?, ?, ?, ?);", u_id, int(q), 1, passed, now)

# Tools

def add_markdown(data, *args):
    output = []
    for d in data:
        d = dict(d)
        #d["answer"] = markdown(d["answer"])
        for a in args:
            print(d[a])
            d[a] = markdown(d[a]) if d[a] is not None else ''
        output.append(d)
    return output


# Website Functions

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None or session["role"] != ROLES[0]:
            return ("",401)
        return f(*args, **kwargs)

    return decorated_function

def maintainer_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None or session["role"] not in ROLES:
            return ("",401)
        return f(*args, **kwargs)

    return decorated_function





    


