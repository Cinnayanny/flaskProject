from flask import Flask, render_template
from config import Config
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object(Config)  # loads the configuration for the database
db = SQLAlchemy(app)            # creates the db object using the configuration
from models import Contact, todo
from forms import ContactForm

@app.route('/')
def homepage():  # put application's code here
    return render_template("index.html", title="Ngunnawal Country")

@app.route("/contact.html", methods=["POST", "GET"])
def contact():
    form = ContactForm()
    return render_template("contact.html", title ="Contact Us", form=form)

@app.route('/todo', methods=["POST", "GET"])
def view_todo():
    all_todo = db.session.query(todo).all()
    if request.method == "POST":
        new_todo = todo(text=request.form['text'])
        new_todo.done = False
        db.session.add(new_todo)
        db.session.commit()
        db.session.refresh(new_todo)
				return redirect("/todo")
    return render_template("todo.html", todos=all_todo)

if __name__ == '__main__':
    app.run()
