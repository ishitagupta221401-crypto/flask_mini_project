from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json, os, re, hashlib, random, string

app = Flask(__name__)
app.secret_key = 'noteflow_alfido_secret_2024'

REVIEWS_FILE = 'reviews.json'

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# ── helpers ──────────────────────────────────────────────
def load_reviews():
    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_reviews(reviews):
    with open(REVIEWS_FILE, 'w') as f:
        json.dump(reviews, f, indent=2)

def unread_count():
    reviews = load_reviews()
    return sum(1 for r in reviews if not r.get('read', False))

def is_valid_email(email):
    if not email:
        return True  # email is optional
    return re.match(EMAIL_REGEX, email) is not None

def generate_reviewer_id(name, email):
    """
    Creates a unique, deterministic Reviewer ID.
    Same person (same name+email) always gets the same ID.
    Format: NF-XXXXXX  (NoteFlow + 6 char hash)
    """
    seed = f"{name.strip().lower()}|{email.strip().lower()}"
    hash_digest = hashlib.sha256(seed.encode()).hexdigest()
    short_code = hash_digest[:6].upper()
    return f"NF-{short_code}"

def get_avatar_color(reviewer_id):
    """Generate a consistent color for each unique reviewer based on their ID."""
    colors = [
        '#7c3aed', '#2563eb', '#059669', '#d97706',
        '#db2777', '#0891b2', '#65a30d', '#dc2626'
    ]
    index = sum(ord(c) for c in reviewer_id) % len(colors)
    return colors[index]

# ── in-memory notes ───────────────────────────────────────
notes = []

# ── routes ───────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title    = request.form.get('title', '').strip()
        content  = request.form.get('content', '').strip()
        category = request.form.get('category', 'General')
        if title and content:
            notes.append({
                'id': len(notes),
                'title': title,
                'content': content,
                'category': category,
                'date': datetime.now().strftime('%d %b %Y'),
                'time': datetime.now().strftime('%I:%M %p'),
            })
        return redirect(url_for('view_notes'))
    return render_template('index.html',
                           note_count=len(notes),
                           unread=unread_count())

@app.route('/notes')
def view_notes():
    return render_template('notes.html',
                           notes=notes,
                           note_count=len(notes),
                           unread=unread_count())

@app.route('/delete/<int:index>')
def delete_note(index):
    if 0 <= index < len(notes):
        notes.pop(index)
        for i, n in enumerate(notes):
            n['id'] = i
    return redirect(url_for('view_notes'))

# ── feedback ──────────────────────────────────────────────
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    error = None
    old_name = old_email = old_message = ''
    old_stars = 5

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        stars   = int(request.form.get('stars', 5))
        message = request.form.get('message', '').strip()

        old_name, old_email, old_message, old_stars = name, email, message, stars

        if not name or not message:
            error = "Name and feedback message are required."
        elif not is_valid_email(email):
            error = "That email address doesn't look valid. Please check the format (e.g. name@example.com)."
        else:
            reviewer_id = generate_reviewer_id(name, email)
            reviews = load_reviews()

            # Count how many reviews this same reviewer ID has left before
            previous_count = sum(1 for r in reviews if r.get('reviewer_id') == reviewer_id)

            reviews.append({
                'id': len(reviews),
                'reviewer_id': reviewer_id,
                'avatar_color': get_avatar_color(reviewer_id),
                'name': name,
                'email': email,
                'stars': stars,
                'message': message,
                'date': datetime.now().strftime('%d %b %Y'),
                'time': datetime.now().strftime('%I:%M %p'),
                'read': False,
                'visit_number': previous_count + 1,
            })
            save_reviews(reviews)
            return redirect(url_for('feedback', submitted=1))

    submitted = request.args.get('submitted')
    reviews   = load_reviews()
    avg = round(sum(r['stars'] for r in reviews) / len(reviews), 1) if reviews else 0
    unique_reviewers = len(set(r['reviewer_id'] for r in reviews)) if reviews else 0

    return render_template('feedback.html',
                           reviews=reviews,
                           avg=avg,
                           submitted=submitted,
                           note_count=len(notes),
                           unread=unread_count(),
                           error=error,
                           old_name=old_name,
                           old_email=old_email,
                           old_message=old_message,
                           old_stars=old_stars,
                           unique_reviewers=unique_reviewers)

# ── notifications ─────────────────────────────────────────
@app.route('/notifications')
def notifications():
    reviews = load_reviews()
    for r in reviews:
        r['read'] = True
    save_reviews(reviews)
    return render_template('notifications.html',
                           reviews=reviews,
                           note_count=len(notes),
                           unread=0)

@app.route('/delete-review/<int:index>')
def delete_review(index):
    reviews = load_reviews()
    if 0 <= index < len(reviews):
        reviews.pop(index)
        for i, r in enumerate(reviews):
            r['id'] = i
        save_reviews(reviews)
    return redirect(url_for('notifications'))

if __name__ == '__main__':
    app.run(debug=True)