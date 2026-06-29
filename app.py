from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json, os

app = Flask(__name__)
app.secret_key = 'noteflow_alfido_secret_2024'

REVIEWS_FILE = 'reviews.json'

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

notes = []

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

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        stars   = int(request.form.get('stars', 5))
        message = request.form.get('message', '').strip()
        if name and message:
            reviews = load_reviews()
            reviews.append({
                'id': len(reviews),
                'name': name,
                'email': email,
                'stars': stars,
                'message': message,
                'date': datetime.now().strftime('%d %b %Y'),
                'time': datetime.now().strftime('%I:%M %p'),
                'read': False,
            })
            save_reviews(reviews)
            return redirect(url_for('feedback', submitted=1))
    submitted = request.args.get('submitted')
    reviews   = load_reviews()
    avg = round(sum(r['stars'] for r in reviews) / len(reviews), 1) if reviews else 0
    return render_template('feedback.html',
                           reviews=reviews,
                           avg=avg,
                           submitted=submitted,
                           note_count=len(notes),
                           unread=unread_count())

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