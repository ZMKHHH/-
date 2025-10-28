from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
import pymysql
import os

# 创建 Flask 应用，显式设置名称
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 设置一个密钥用于 session


# ===========================
# 数据库配置
# ===========================
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="14753785988",
        database="sys",
        port=3306,
        charset='utf8mb4'
    )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS `前端账号密码`
                   (
                       id
                       INT
                       AUTO_INCREMENT
                       PRIMARY
                       KEY,
                       username
                       VARCHAR
                   (
                       50
                   ) NOT NULL UNIQUE,
                       password VARCHAR
                   (
                       100
                   ) NOT NULL
                       )
                   """)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 数据库表已准备就绪")


# ===========================
# 辅助函数：检查用户是否登录
# ===========================
def check_login():
    """检查用户是否已登录"""
    return 'user_id' in session


# ===========================
# 路由定义
# ===========================

# 静态文件服务 - 服务所有文件
@app.route('/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory('.', filename)
    except:
        return f"文件 {filename} 未找到", 404


# 专门为智慧工地文件夹提供静态文件服务
@app.route('/03.智慧工地/<path:filename>')
def serve_gongdi_static(filename):
    # 检查是否是 CSS、JS、图片等静态资源，这些允许直接访问
    if filename.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico')):
        try:
            return send_from_directory('03.智慧工地', filename)
        except:
            return f"文件 {filename} 未找到", 404
    else:
        # 如果是 HTML 文件，需要登录验证
        if not check_login():
            return redirect('/')  # 未登录跳转到登录页
        try:
            return send_from_directory('03.智慧工地', filename)
        except:
            return f"文件 {filename} 未找到", 404


# 主页面 - 使用模板
@app.route('/')
def index():
    # 如果已登录，直接跳转到智慧工地页面
    if check_login():
        return redirect('/03.智慧工地/ZhiHuigongdi.html')
    return render_template('login.html')


# 智慧工地主页面 - 需要登录验证
@app.route('/03.智慧工地/ZhiHuigongdi.html')
def zhihui_gongdi():
    if not check_login():
        return redirect('/')  # 未登录跳转到登录页

    try:
        return send_from_directory('03.智慧工地', 'ZhiHuigongdi.html')
    except:
        return "智慧工地页面未找到", 404


# 测试路由1 - 直接HTML
@app.route('/test')
def test():
    return "<h1>测试页面 - 直接HTML</h1><p>如果看到这个，说明路由正常</p>"


# 测试路由2 - 另一个测试
@app.route('/hello')
def hello():
    return "<h1>Hello World!</h1><p>Flask 工作正常</p>"


# 登录API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "用户名和密码不能为空！"})

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM `前端账号密码` WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            # 登录成功，设置 session
            session['user_id'] = user[0]  # 用户ID
            session['username'] = user[1]  # 用户名

            return jsonify({
                "status": "success",
                "message": "登录成功！",
                "redirect": "/03.智慧工地/ZhiHuigongdi.html"
            })
        else:
            return jsonify({"status": "error", "message": "用户名或密码错误！"})
    except Exception as e:
        print("❌ 登录错误：", e)
        return jsonify({"status": "error", "message": "服务器错误，请稍后重试。"})


# 注册API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "用户名和密码不能为空！"})

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM `前端账号密码` WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "用户名已存在，请更换用户名。"})

        cursor.execute("INSERT INTO `前端账号密码` (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "注册成功！请返回登录界面登录。"})
    except Exception as e:
        print("❌ 注册错误：", e)
        return jsonify({"status": "error", "message": "服务器错误，请稍后重试。"})


# 退出登录
@app.route('/logout')
def logout():
    session.clear()  # 清除所有 session
    return redirect('/')  # 跳转到登录页


# ===========================
# 启动应用
# ===========================
if __name__ == '__main__':
    # 检查模板文件
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'login.html')
    print(f"🔍 模板文件路径: {template_path}")
    print(f"📄 模板文件存在: {os.path.exists(template_path)}")

    # 检查智慧工地文件是否存在
    gongdi_path = '03.智慧工地/ZhiHuigongdi.html'
    print(f"🔍 智慧工地文件路径: {gongdi_path}")
    print(f"📄 智慧工地文件存在: {os.path.exists(gongdi_path)}")

    init_db()
    print("🚀 启动 Flask 应用...")
    print("🌐 请访问: http://localhost:5000")
    print("🏗️ 智慧工地链接: http://localhost:5000/03.智慧工地/ZhiHuigongdi.html")

    # 使用不同的端口避免冲突
    app.run(host='0.0.0.0', port=5000, debug=True)
    #爱哦聚餐次奶茶哦i阿我怕紧凑i下