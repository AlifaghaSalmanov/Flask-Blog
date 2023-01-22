from flask import (
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    session,
    logging,
    request,
)
from functools import wraps

from flask_mysqldb import MySQL
from wtforms import (
    Form,
    StringField,
    SelectField,
    TextAreaField,
    PasswordField,
    validators,
)
from passlib.hash import sha256_crypt

app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:

            return f(*args, **kwargs)
        else:
            flash("You must be logged in first.", "danger")

            return redirect(url_for("login"))

    return decorated_function


class RegisterForm(Form):
    """docstring for RegisterForm."""

    name = StringField(
        "Name: ",
        validators=[
            validators.Length(min=3, max=10, message="name must be range 3 and 10")
        ],
    )
    username = StringField(
        "Username: ",
        validators=[
            validators.Length(min=3, max=10, message="name must be range 3 and 10"),
            validators.DataRequired(),
        ],
    )
    email = StringField(
        "email: ",
        validators=[
            # validators.Email(),
            validators.DataRequired(),
        ],
    )
    password = PasswordField(
        "Password: ",
        validators=[
            validators.Length(min=1, message="password must be at least 8 characthers"),
            validators.DataRequired(),
            validators.EqualTo(
                fieldname="confirm", message="Fill this field with your password"
            ),
        ],
    )
    confirm = PasswordField()


class LoginForm(Form):
    username = StringField(
        "Username: ",
        validators=[
            validators.Length(min=3, max=10, message="name must be range 3 and 10"),
            validators.DataRequired(),
        ],
    )

    password = PasswordField(
        "Password: ",
        validators=[
            validators.Length(min=1, message="password must be at least 8 characthers"),
            validators.DataRequired(),
            validators.EqualTo(
                fieldname="confirm", message="Fill this field with your password"
            ),
        ],
    )


class ArticaleForm(Form):
    """docstring for ArticaleForm."""

    title = StringField("Article Title")
    content = TextAreaField("Article content")


@app.route("/")
def main():
    return render_template("index.html", answer=5)


mysql = MySQL(app)
app.secret_key = "ybblog"


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("main"))
    else:
        cursor = mysql.connection.cursor()
        keyword = request.form.get("keyword")
        query = "SELECT * FROM articles  WHERE title LIKE '%" + keyword + "%'"
        result = cursor.execute(query)
        if result == 0:
            flash("There is not such article", "danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html", articles=articles)


@app.route("/edit/<string:id>", methods=["GET", "POST"])
def edit(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s and id=%s"
    if request.method == "GET":
        result = cursor.execute(query, (session["username"], id))
        print(f"{result=}")
        if result > 0:
            article = cursor.fetchone()
            form = ArticaleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("edit.html", form=form)
        else:
            flash("There was an error", "danger")
            return redirect(url_for("main"))
    elif request.method == "POST":
        form = ArticaleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        query = "UPDATE articles SET title=%s, content=%s WHERE id = %s"
        cursor.execute(query, (newTitle, newContent, id))
        mysql.connection.commit()
        flash("Updated articles")
        return redirect(url_for("dashboard"))


@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "DELETE FROM articles WHERE author = %s and id = %s"
    result = cursor.execute(query, (session["username"], id))

    if result > 0:
        mysql.connection.commit()
        flash("Successfully deleted articles", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Failed to delete articles", "danger")
        return redirect(url_for("main"))


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles"
    result = cursor.execute(query)

    if result > 0:
        articles = cursor.fetchall()

        return render_template("articles.html", articles=articles)
    else:
        return render_template("articles.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(query, (session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        query = (
            "INSERT INTO users(NAME, USERNAME, EMAIL, PASSWORD) VALUES(%s, %s, %s, %s)"
        )

        cursor.execute(query, (name, username, email, password))
        mysql.connection.commit()

        cursor.close()

        flash("Sign up succesfully", category="success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users WHERE username = %s"

        result = cursor.execute(query, (username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password, real_password):
                flash("Login successfuly", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("main"))
            else:
                flash("Password wrong", "danger")
                return redirect(url_for("login"))
        else:
            flash("Username is wrong", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/addarticale", methods=["GET", "POST"])
@login_required
def addarticle():
    form = ArticaleForm(request.form)

    if request.method == "POST":
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        query = "INSERT INTO articles(title, author, content) VALUES(%s,%s,%s)"
        cursor.execute(query, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Articales successfully added", "success")
        return redirect(url_for("dashboard"))

    return render_template("addarticale.html", form=form)
    pass


@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(query, (id,))
    if result > 0:
        article = cursor.fetchone()

        return render_template("article.html", article=article)
    else:
        return render_template("article.html", id=id)


if __name__ == "__main__":
    app.run(debug=True)
