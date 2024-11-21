from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 定義資料庫模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 初始化資料庫
with app.app_context():
    db.create_all()

# 加載使用者
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 註冊功能 - 存儲密碼的時候加密
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 檢查密碼與確認密碼是否相同
        if password != request.form['confirm_password']:
            flash('密碼與確認密碼不一致，請再試一次。', 'error')
            return redirect(url_for('register'))


        # 檢查使用者名稱是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('使用者名稱已存在，請選擇其他名稱。', 'error')
            return redirect(url_for('register'))

        # 如果使用者名稱不存在，則創建新使用者
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()

        flash('註冊成功，請登入！', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# 登入功能 - 檢查帳號和密碼
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('帳號不存在或密碼錯誤! 請再試一次', 'error')  # 錯誤訊息，類型為 'error'
            return redirect(url_for('login'))

    return render_template('login.html')

# 登出功能
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# 主頁，顯示使用者的待辦事項
@app.route('/')
@login_required
def index():
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.date.asc()).all()

    # 過濾重複的日期，只保留唯一日期
    unique_dates = []
    for todo in todos:
        if todo.date not in unique_dates:
            unique_dates.append(todo.date)

    return render_template('index.html', todos=todos, unique_dates = unique_dates)

# 新增待辦事項
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_todo():
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        content = request.form['content']
        
        new_todo = Todo(title=title, date=date, content=content, user_id=current_user.id)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add_todo.html')

# 顯示單一待辦事項頁面
@app.route('/todo/<int:id>')
@login_required
def view_todo(id):
    todo = Todo.query.get_or_404(id)  # 使用 get_or_404 確保找不到時返回 404
    if todo.user_id != current_user.id:  # 確保只有擁有者可以查看
        flash('你沒有權限查看此事項')
        return redirect(url_for('index'))
    return render_template('view_todo.html', todo=todo)

# 編輯和刪除路由保持不變，確保只有擁有者可以修改和刪除
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_todo(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        flash('你沒有權限編輯這個待辦事項')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        todo.title = request.form['title']
        todo.date = request.form['date']
        todo.content = request.form['content']
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('update_todo.html', todo=todo)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_todo(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        flash('你沒有權限刪除這個待辦事項')
        return redirect(url_for('index'))
    
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
