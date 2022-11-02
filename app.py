from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import current_user, login_user, LoginManager, logout_user, login_required
from werkzeug.utils import secure_filename
import random, os


app = Flask(__name__)
app.config.from_object(Config)  # loads the configuration for the database
db = SQLAlchemy(app)            # creates the db object using the configuration
login = LoginManager(app)
login.login_view = 'login'

UPLOAD_FOLDER = './static/images/userPhotos/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from models import Contact, todo, User, Photos
from forms import ContactForm, RegistrationForm, LoginForm, ResetPasswordForm, UserProfileForm, PhotoUploadForm

@app.route('/')
def homepage():  # put application's code here
    return render_template("index.html", title="Ngunnawal Country", user=current_user)

@app.route("/registration", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(email_address=form.email_address.data, name=form.name.data,
                        user_level=1, active=1)  # defaults to regular user
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash("You have registered. Thank you for joining our site!")
        return redirect(url_for("homepage"))
    return render_template("registration.html", title="User Registration", form=form, user=current_user)

@app.route("/contact.html", methods=["POST", "GET"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        new_contact = Contact(name=form.name.data, email=form.email.data, message=form.message.data)
        db.session.add(new_contact)
        db.session.commit()
    flash("Thank you for your feedback! We will get back to you")
    return render_template("contact.html", title ="Contact Us", form=form, user=current_user)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/userPhotos', methods=['GET', 'POST'])
@login_required
def photos():
    form = PhotoUploadForm()
    user_images = Photos.query.filter_by(userid=current_user.id).all()
    if form.validate_on_submit():
        new_image = form.image.data
        filename = secure_filename(new_image.filename)

        if new_image and allowed_file(filename):
            # Get the file extension of the file.
            file_ext = filename.split(".")[1]
            import uuid
            random_filename = str(uuid.uuid4())
            filename = random_filename + "." + file_ext
            new_image.save(os.path.join(UPLOAD_FOLDER, filename))
            photo = Photos(title=form.title.data, filename=filename, userid=current_user.id)
            db.session.add(photo)
            db.session.commit()
            flash("Image Uploaded")
            return redirect(url_for("photos"))
        else:
            flash("The File Upload failed.")
    return render_template("userPhotos.html", title="User Photos", user=current_user, form=form, images=user_images)

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
    return render_template("todo.html", todos=all_todo, user=current_user)
@app.route("/todoedit/<todo_id>", methods=["POST", "GET"])
def edit_note(todo_id):
    if current_user.is_admin():
        if request.method == "POST":
            db.session.query(todo).filter_by(id=todo_id).update({
                "text": request.form['text'],
                "done": True if request.form['done'] == "on" else False
            })
            db.session.commit()
        elif request.method == "GET":
            db.session.query(todo).filter_by(id=todo_id).delete()
            db.session.commit()
        return redirect("/todo", code=302, user=current_user)
    else:
        return render_template("unauthorised.html", user=current_user)

if __name__ == '__main__':
    app.run()

@app.route('/login.html', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email_address=form.email_address.data).first()
        if user is None or not user.check_password(form.password.data) or not user.active:
            return redirect(url_for('login'))
        login_user(user)
        flash("You have logged in")
        return redirect(url_for('homepage'))
    return render_template("login.html", title="Sign In", form=form, user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    flash("You have logged out")
    return redirect(url_for('homepage'))

@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email_address=current_user.email_address).first()
        user.set_password(form.new_password.data)
        db.session.commit()
        flash("Your password is successfully changed")
        return redirect(url_for('homepage'))
    return render_template("passwordreset.html", title='Reset Password', form=form, user=current_user)

@app.route('/history')
def history():  # I don't think it has any code
    return render_template("history.html", title="Ngunnawal History", user=current_user)

@app.route('/gallery')
def gallery():  # I don't think it has any code
    return render_template("gallery.html", title="Gallery", user=current_user)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", user=current_user), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html", user=current_user), 500

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UserProfileForm()
    user = User.query.filter_by(email_address=current_user.email_address).first()
    if request.method == 'GET':
        form.name.data = user.name
        form.email_address.data = user.email_address
    if form.validate_on_submit():
        user.update_details(email_address=form.email_address.data, name=form.name.data)
        db.session.commit()
        flash("Your details have been changed")
        return redirect(url_for("homepage"))
    return render_template("userProfile.html", title="User Profile", user=current_user, form=form)

@app.route('/contact_messages')
@login_required
def view_contact_messages():
    if current_user.is_admin():
        contact_messages = Contact.query.all()
        return render_template("contactMessages.html", title="Contact Messages", user=current_user, messages=contact_messages)
    else:
        return render_template("unauthorised.html", user=current_user)

@app.route('/admin/list_all_users')
@login_required
def list_all_users():
    if current_user.is_admin():
        all_users = User.query.all()
        return render_template("listAllUsers.html", title="All Active Users", user=current_user, users=all_users)
    else:
        flash("You must be an administrator to access this functionality.")
        return redirect(url_for("homepage"))

@app.route('/reset_password/<userid>', methods=['GET', 'POST'])
@login_required
def reset_user_password(userid):
    if current_user.is_admin():
        form = ResetPasswordForm()
        user = User.query.filter_by(id=userid).first()
        if form.validate_on_submit():
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password has been reset for user {}'.format(user.name))
            return redirect(url_for('homepage'))
        return render_template("passwordreset.html", title='Reset Password', form=form, user=user)
    else:
        flash("You must be an administrator to access this functionality.")
        return redirect(url_for("homepage"))

@app.route('/reset_user_password/<userid>', methods=['GET', 'POST'])
@login_required
def reset_user_password(userid):
    if current_user.is_admin():
        form = ResetPasswordForm()
        user = User.query.filter_by(id=userid).first()
        if form.validate_on_submit():
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password has been reset for user {}'.format(user.name))
            return redirect(url_for('homepage'))
        return render_template("passwordreset.html", title='Reset Password', form=form, user=user)
    else:
        flash("You must be an administrator to access this functionality.")
        return redirect(url_for("homepage"))

@app.route('/admin/user_enable/<userid>')
@login_required
def user_enable(userid):
    if current_user.is_admin():
        user = User.query.filter_by(id=userid).first()
        user.active = not user.active
        db.session.commit()
        return redirect(url_for("list_all_users"))
    else:
        flash("You must be an administrator to access this functionality.")
        return redirect(url_for("homepage"))