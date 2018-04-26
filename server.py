from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re,md5,os,binascii
salt = binascii.b2a_hex(os.urandom(15)) # generate salt for password hashing+salt
app = Flask(__name__)
app.secret_key = 'KeepItSecretKeepItSafe'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
mysql = MySQLConnector(app,'wall')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration', methods =['POST'])
def registration():
        errors =[] #array for errors
        successlog = [] #array for sucess
        user_fname = request.form['first_name']
        user_lname = request.form['last_name']
        user_email = request.form['email']
        user_password = request.form['password']
        user_pwdConfirm = request.form['pwdConfirm']
        
        if len(user_fname) < 1:
            errors.append("First Name is empty")
        if len(user_lname) < 1:
            errors.append("Last Name is empty")
        if len(user_email) < 1:
            errors.append("Email is empty")
            if len(errors) > 0:
                for error in errors:
                    flash(error,'regError')
                return redirect('/')
        if len(user_fname) < 2:
            errors.append("First Name is too short")
        if not user_fname.isalpha():
            errors.append("First Name should not be a number")
        if len(user_lname) < 2:
            errors.append("Last Name is too short")
        if not user_lname.isalpha():
            errors.append("Last Name should not be a number")
        if not EMAIL_REGEX.match(user_email):
            errors.append("Invalid Email Address!")
        if len(user_password) < 8:
            errors.append("Password should be 8 characters")
        if user_password != user_pwdConfirm:
            errors.append("Passwords do not match")
            if len(errors) > 0:
                for error in errors:
                    flash(error,'regError')
                return redirect('/')
            else:
                return redirect('/')

        # check if records exists in database
        query = "SELECT * FROM users WHERE users.email = :email"
        data = {'email':request.form['email']}
        email_validate = mysql.query_db(query,data)
       
        if len(email_validate) > 0:
            errors.append("This account is already in use. Log-in or use another email.")
            for error in errors:
                flash(error,'regError')
            return redirect('/')
        else:
        # add user to database
            salt =  binascii.b2a_hex(os.urandom(15))
            hashed_pw = md5.new(user_password + salt).hexdigest()
            data = {
                'first_name': user_fname,
                'last_name': user_lname,
                'email': user_email,
                'hashed_pw': hashed_pw, 
                'salt':salt
                }
            query = "INSERT INTO users (first_name, last_name, email, password, salt, created_at, updated_at)"
            query += "VALUES (:first_name, :last_name, :email, :hashed_pw, :salt,  NOW(), NOW())"
            mysql.query_db(query, data)
            successlog.append("You have successfully registered! Please log-in.")
            
            for success in successlog:
                flash(success,'succesNotif')
                return redirect ('/')

@app.route('/login', methods=['POST'])
def login():
        errorlogin = [] #array for errors
        user_email = request.form['email'] 
        user_password = request.form['password']

        #email and password validation
        if len(user_email) < 1 and len(user_password) < 1:
            errorlogin.append("Password or email is empty")
        else:
            query = "SELECT * FROM users WHERE users.email = :email"
            data = {'email':user_email}
            user_validation = mysql.query_db(query, data)
            
            if len(user_validation) != 0:
                encrypted_password = md5.new(user_password + user_validation[0]['salt']).hexdigest()
                if user_validation[0]['password'] == encrypted_password:
                    session['name'] = user_validation[0]['first_name'] 
                    #set session ID to user_id 
                    session['user_id'] = user_validation[0]['user_id']
                    return redirect('/wall')
                else:
                    errorlogin.append("Invalid Password")
                    for error in errorlogin:
                        flash(error,'loginError')
                        return redirect('/')             
            else:
                errorlogin.append("Email not found. Please register")
                for error in errorlogin:
                    flash(error,'loginError')
                    return redirect('/')   

        if len(errorlogin) > 0:
            print len(errorlogin) 
            for error in errorlogin:
                flash(error,'loginError')
            return redirect('/')
        else:
            return redirect('/')
        
@app.route('/logout', methods=['POST'])
def logout():
	session.clear()
	print('session cleared')
	return redirect('/')

@app.route('/wall')
def wall(): 
    # Retrieve the message id from session
    query = "SELECT * FROM messages WHERE messages.user_id= {}".format(session['user_id'])
    getmessageid = mysql.query_db(query)
    session['message_id'] = getmessageid[0]['message_id']

    # Retrieve the user_id from session
    session['user_id']

    # Retrieve the user info by user_id from the database
    query = "SELECT * FROM users WHERE users.user_id = {}".format(session['user_id'])
    user = mysql.query_db(query)

    # Retrieve all messages
    query = "SELECT messages.message_id, CONCAT_WS(' ', users.first_name, users.last_name) AS user_name, DATE_FORMAT(messages.created_at, '%M %D, %Y') AS time, messages.message FROM messages JOIN users ON users.user_id = messages.user_id WHERE users.user_id = {} ORDER BY messages.created_at DESC".format(session['user_id'])
    messages = mysql.query_db(query)
    print messages

    # Retrieve all comments
    query = "SELECT comments.message_id AS message_id, CONCAT_WS(' ', users.first_name, users.last_name) AS user_name, comments.user_id, DATE_FORMAT(comments.created_at, '%M %D, %Y %H:%i:%s') AS time, comments.comment FROM comments  JOIN messages ON messages.message_id = comments.message_id JOIN users ON users.user_id = comments.user_id ORDER BY comments.created_at ASC"
    comments = mysql.query_db(query)
    print comments

    return render_template('wall.html', all_messages = messages, all_comments = comments)

@app.route('/post', methods =['POST'])
def post():
    # If the request is a post, insert in messages
    if (request.form['submit'] == 'post'):
        data = {
            'user_id': session['user_id'],
            'message': request.form['messages']
            }
        query = "INSERT INTO messages (message, created_at, updated_at, user_id) "
        query += "VALUES (:message, NOW(), NOW(), :user_id)"
        mysql.query_db(query, data)

    #insert comments here


    return redirect ('/wall')
app.run(debug=True)