from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is up and running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # إنشاء واستدعاء خيط للحفاظ على التطبيق قيد التشغيل في الخلفية
    t = Thread(target=run)
    t.start()
