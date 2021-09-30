import sqlite3
import logging

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.config.update(
        CONNECTION_COUNT=app.config['CONNECTION_COUNT'] + 1,
    )

    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Function to count the number of posts
def get_posts_number():
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return len(post)


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.config['CONNECTION_COUNT'] = 0


# Healthcheck endpoint
@app.route('/healthz')
def healthz():
    try:
        get_posts_number()
        return app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    except sqlite3.OperationalError:
        return app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )


# Metrics endpoint
@app.route('/metrics')
def metrics():
    response = app.response_class(
        response=json.dumps(
            {
                "db_connection_count": app.config['CONNECTION_COUNT'],
                "post_count": get_posts_number(),
            }
        ),
        status=200,
        mimetype='application/json'
    )

    return response


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        # logging if the article does not exist
        # i used the f-strings but it has a version problem with the docker image
        # log.info(f"The article with the id: {post_id} does not exist!")
        log.info("The article with the id: {} does not exist!".format(post_id))
        return render_template('404.html'), 404
    else:
        # logging the title of the requested article
        # log.info(f"Article {post['title']} retrieved!")
        log.info("Article {} retrieved!".format(post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    # logging if the about us page is retrieved
    log.info("Page About us retrieved!")
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()
            # logging if a new article is created
            # log.info(f"The article with the title: {title} was created!")
            log.info("The article with the title: {} was created!".format(title))

            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    # define the logger, its name and the level
    log = logging.getLogger('techtrends')
    log.setLevel(logging.DEBUG)

    # create file handler, the level and the name of the file
    fh = logging.FileHandler('app.log')
    fh.setLevel(logging.DEBUG)

    # create the stream handler and the level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create the message and date formatter
    formatter = logging.Formatter('%(levelname)s: %(name)s: %(asctime)s, %(message)s', "%d-%m-%Y %H:%M:%S")

    # add the formatter to the handlers
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    log.addHandler(fh)
    log.addHandler(ch)

    # app.run(debug=True)
    app.run(host='0.0.0.0', port='3111')
