import os
import secrets
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Message, likes

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated:
        unread_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    else:
        unread_count = 0
    return dict(unread_count=unread_count)


# --- Helpers ---

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], picture_fn)
    form_picture.save(picture_path)
    return picture_fn


# --- ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('discover'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio', '')
        gender = request.form.get('gender', '')
        interest = request.form.get('interest', '')
        interests_list = request.form.get('interests_list', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'warning')
            return redirect(url_for('register'))

        picture_file = 'default.png'
        picture = request.files.get('picture')
        if picture and picture.filename:
            picture_file = save_picture(picture)

        hashed_pw = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password=hashed_pw,
            bio=bio,
            gender=gender,
            interest=interest,
            interests_list=interests_list,
            image_file=picture_file,
        )
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('discover'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('discover'))

        flash('Login unsuccessful. Please check email and password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/")
@login_required
def discover():
    # Basic Matching Algorithm
    if current_user.interest == 'Both':
        potential_matches = User.query.filter(User.id != current_user.id).all()
    else:
        potential_matches = User.query.filter(
            User.id != current_user.id, User.gender == current_user.interest
        ).all()

    scored_users = []
    u1_set = set((current_user.interests_list or '').lower().split(','))

    for user in potential_matches:
        u2_set = set((user.interests_list or '').lower().split(','))
        score = len(u1_set.intersection(u2_set))
        scored_users.append((score, user))

    scored_users.sort(key=lambda x: x[0], reverse=True)
    suggestions = [u[1] for u in scored_users]

    return render_template('index.html', suggestions=suggestions)

@app.route('/like/<int:user_id>')
@login_required
def like(user_id):
    target = User.query.get_or_404(user_id)
    if target not in current_user.following:
        current_user.following.append(target)
        db.session.commit()
    return redirect(url_for('discover'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', current_user.bio)
        picture = request.files.get('picture')
        if picture and picture.filename:
            current_user.image_file = save_picture(picture)
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')


@app.route('/messages')
@login_required
def messages():
    # find conversation partners and unread counts
    sent_ids = [m.receiver_id for m in Message.query.filter_by(sender_id=current_user.id).all()]
    received_ids = [m.sender_id for m in Message.query.filter_by(receiver_id=current_user.id).all()]
    partner_ids = set(sent_ids + received_ids)
    partners = User.query.filter(User.id.in_(partner_ids)).all()

    threads = []
    for partner in partners:
        unread = Message.query.filter_by(sender_id=partner.id, receiver_id=current_user.id, is_read=False).count()
        latest = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == partner.id))
            | ((Message.sender_id == partner.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp.desc()).first()
        threads.append({'partner': partner, 'unread': unread, 'latest': latest})

    threads.sort(key=lambda t: t['latest'].timestamp if t['latest'] else datetime.min, reverse=True)
    return render_template('messages.html', threads=threads)


@app.route('/new_message', methods=['GET', 'POST'])
@login_required
def new_message():
    if request.method == 'POST':
        receiver_id = int(request.form.get('receiver_id'))
        content = request.form.get('content', '').strip()
        if not content:
            flash('Message cannot be empty.', 'danger')
            return redirect(url_for('new_message'))
        receiver = User.query.get_or_404(receiver_id)
        msg = Message(sender_id=current_user.id, receiver_id=receiver.id, content=content, is_read=False)
        db.session.add(msg)
        db.session.commit()
        flash(f'Message sent to {receiver.username}.', 'success')
        return redirect(url_for('chat', user_id=receiver.id))

    candidates = User.query.filter(User.id != current_user.id).all()

    # recent contact suggestions by latest message timestamp
    recent_ids = set()
    recent_threads = []
    for msg in Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all():
        partner_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if partner_id not in recent_ids and partner_id != current_user.id:
            recent_ids.add(partner_id)
            partner = User.query.get(partner_id)
            if partner:
                recent_threads.append(partner)
        if len(recent_threads) >= 5:
            break

    return render_template('new_message.html', candidates=candidates, recent_contacts=recent_threads)


@app.route('/chat/<int:user_id>')
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    messages = (
        Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user.id))
            | ((Message.sender_id == other_user.id) & (Message.receiver_id == current_user.id))
        )
        .order_by(Message.timestamp.asc())
        .all()
    )
    Message.query.filter_by(sender_id=other_user.id, receiver_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('chat.html', other_user=other_user, messages=messages)


@socketio.on('join')
def handle_join(data):
    join_room(str(data.get('room')))


@socketio.on('message')
def handle_message(data):
    msg = Message(
        sender_id=current_user.id,
        receiver_id=data['to'],
        content=data['msg'],
        is_read=False,
    )
    db.session.add(msg)
    db.session.commit()
    emit('message', {'msg': data['msg'], 'from': current_user.username}, room=str(data['to']))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)