from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from models import User, db

# High-level logic for finding matches
def get_suggestions():
    # Logic: Find users who match the current_user's interest 
    # and haven't been liked/disliked yet.
    return User.query.filter(User.gender == current_user.interest).all()

def like_user(target_id):
    target = User.query.get(target_id)
    current_user.liked.append(target)
    db.session.commit()
    # Check for a mutual match here