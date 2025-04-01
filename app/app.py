from flask import Flask, render_template, jsonify, request, redirect, flash, session
from flask_session import Session
from werkzeug.security import generate_password_hash

import helpers as h

# App Setting
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Cookies
Session(app)


@app.route("/")
def index():
    return render_template("index.html")

# Questions
@app.route("/add-questions", methods=["GET","POST"])
@h.maintainer_required
def add_questions():
    if request.method == "POST":
        if request.form.get("new-topic") != "":
            new_topic = request.form.get("new-topic")
            h.add_topic(new_topic)
            flash("New topic {} created.".format(new_topic))
            return redirect("add-questions")
        if request.form.get("new-subtopic") != "":
            t_id = int(request.form.get("topic"))
            new_subtopic = request.form.get("new-subtopic")
            h.add_subtopic(t_id, new_subtopic)
            flash("New subtopic {} created.".format(new_subtopic))
            return redirect("/add-questions")
        s_id = request.form.get("subtopic")    
        question = request.form.get("question")
        difficulty = request.form.get("difficulty", None)
        isMultipleChoice = request.form.get("isMultipleChoice",0)
        q_id = h.add_question(s_id, question, difficulty, isMultipleChoice)
        flash("Question successully added. Enter Answers now.")
        return render_template("add-answers.html", q_id = q_id["q_id"], question = question)
    topics = h.get_topics()
    return render_template("add-questions.html", rows_topics=topics)

# Questions

@app.route("/add-answers", methods=["GET","POST"])
@h.maintainer_required
def add_answers():
    if request.method == "POST":
        form = request.form


        answers = []
        
        
        for i in range (1,len(form)//4+1):
            answer = {}
            answer["q_id"] =  form[f"answer[{i}][q_id]"]
            answer["answer"] = form[f"answer[{i}][answer]"]
            if answer["answer"] == "":
                continue
            answer["comment"] = form[f"answer[{i}][comment]"]
            answer["true"] = form[f"answer[{i}][true]"]
            answers.append(answer)

        changes = h.add_answers(answers)
        flash(f"Added {changes} questions.")
        return redirect("/edit-questions")
        
        

    return render_template("add-answers.html")

@app.route("/edit-questions")
@h.maintainer_required
def edit_questions():
    if request.args.get("delete"):
        q_id = request.args.get("delete")
        questions, answers = h.delete_question(q_id)
        return {"questions": questions, "answers": answers}
    if request.args.get("update"):
        q_id = request.args.get("update")
        question = request.args.get("question", None)
        multiple = request.args.get("multiple", None)
        msg = h.update_question(q_id, question, multiple)
        return jsonify(msg)
        

        
    topics = h.get_topics()
    return render_template("edit-questions.html", rows_topics=topics)

# Tests

@app.route("/make-test", methods=["GET","POST"])
def make_test():
    
    session["q_order"] = ""
    session["a_order"] = ""
    if request.method == "POST":
        t_id = request.form.get("topic")
        s_id = request.form.get("subtopic")
        count = request.form.get("count")
        if not session.get("user_id"):
            u_id = None
        else:
            u_id = session["user_id"]
        questions, answers = h.create_test(u_id,t_id, s_id, count)
        questions = h.add_markdown(questions,"question")
        answers = h.add_markdown(answers,"answer","comment")
        session["q_order"] = [q["q_id"] for q in questions]
        session["a_order"] = [a["a_id"] for a in answers]
        return render_template("test.html", questions=questions, answers=answers)
    topics = h.get_topics()

    if request.args.get("test"):
        t_id = request.args.get("test")
        questions, answers = h.get_user_test(session["user_id"], t_id)
        questions = h.add_markdown(questions,"question")
        answers = h.add_markdown(answers,"answer","comment")
        session["q_order"] = [q["q_id"] for q in questions]
        session["a_order"] = [a["a_id"] for a in answers]
        return render_template("test.html", questions=questions, answers=answers)
        


    return render_template("make-test.html", rows_topics=topics)

@app.route("/get-results", methods=["POST"])
def get_results():
    test = {}
    # extract questions/answers dict
    
    for r in request.form:
        if r.__contains__("."):
            rs = r.split(".")
            if rs[0] == "question":
                test[rs[1]] = []
            else:
                test[rs[0]].append(int(rs[1]))
        else:
            test[r].append(int(request.form.get(r)))



    
    # send answers to users table
    u_id = None if session is None else session.get("user_id")
    h.verify_test(u_id,test)
    questions = h.get_questions_result(session["q_order"])
    questions = h.add_markdown(questions, "question")
    answers = h.get_answers(session["q_order"])
    answers = h.add_markdown(answers, "answer", "comment")
    # Send questions in same random order like make_test
    questions_ordered = []
    for q in session["q_order"]:
        for question in questions:
            if question["q_id"] == int(q):
                questions_ordered.append(question)
    # Send answers in same random order like make_test
    answers_ordered = []
    for a in session["a_order"]:
        for answer in answers:
            if answer["a_id"] == int(a):
                answers_ordered.append(answer)
    return render_template("results.html", questions=questions_ordered, answers=answers_ordered, test=test)
    # return 'hello'

@app.route("/save-test")
def save_test():
    if request.args.get("save") and int(request.args.get("save")) == session["user_id"]:
        
        questions = session["q_order"]
        msg = h.save_test(session["user_id"], str(request.args.get("name")), questions)
        return msg
    
    return redirect("/")

# Inforoutes
@app.route("/get-subtopics")
def get_subtopics():
    t_id = request.args.get("t_id")
    subtopics = h.get_subtopics(t_id)
    return jsonify(subtopics)

@app.route("/get-questions")
def get_questions():
    t_id = request.args.get("t_id")
    s_id = request.args.get("s_id")
    questions = h.get_questions(t_id, s_id)
    questions = h.add_markdown(questions,"question")
    q_ids = [q_id["q_id"] for q_id in questions]
    answers = h.get_answers(q_ids)

    # Markdown
    answers = h.add_markdown(answers,"answer","comment")
    return render_template("questions.html", questions = questions, answers = answers)

# Dev
@app.route("/dev")
def dev():
    tests = h.get_saved_tests(session["user_id"])
    return render_template("dev.html", tests=tests)

# Users

@app.route("/register",methods=["GET","POST"])
def register():
    if session :
        return redirect("/")
    if request.method == "POST":
        if not (request.form.get("username") and request.form.get("password") and request.form.get("confirm")):
            return 'error'
        else:
            msg = h.register_user(request.form.get('username'),request.form.get("password"),request.form.get("confirm"))
        if "error" in msg:
            return msg
        else:
            flash(msg["success"])
            return redirect ("/login")
    
    if request.args.get("username"):
        username = request.args.get("username")
        ok = 'ok' if h.check_username(username) == 0 else 'error'
        return jsonify(ok)
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            error = "Field empty"
            flash('')
            return render_template("login.html", error=error)
        session["user_name"], session["user_id"], session["role"], error_msg = h.login_user(username, password)
        
        if not session["user_id"] or not session["role"]:
            error = error_msg
            flash('')
            return render_template("login.html", error=error)
        flash("User {} successfully logged in as {}".format(username, session["role"]))
        return redirect("/")
    return render_template("login.html")

@app.route("/users", methods=["GET","POST"])
@h.admin_required
def users():
    if request.method == "POST":
        if request.form.get("delete") != None:
            u_id = request.form.get("delete")
            name = request.form.get("name")
            h.delete_user(u_id)
            flash("User {} deleted successfully.".format(name))
            return redirect("/users")
        if request.form.get("change-role") != None:
            msg = h.change_role(request.form.get("change-role"), request.form.get("role"))
        
            if "error" in msg:
                return msg
            else:
                flash(msg["success"])
                return redirect ("/users")
        
        name = request.form.get("name")
        hash = generate_password_hash(request.form.get("password"))
        role = request.form.get("role")
        h.add_user(name, hash, role)
        flash("User {} created successfully as {}.".format(name, role))
        return redirect("/users")

    users = h.get_users()
    return render_template("users.html", users = users, roles=h.ROLES)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("login")