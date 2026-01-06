from flask import Flask, request, jsonify, render_template_string
import json
import requests
from datetime import datetime

app = Flask(__name__)

# ==========================================
# 設定Access Token (記得輸入自己的access token !)
# ==========================================
ACCESS_TOKEN = ''

# 存放歷史紀錄 (網頁顯示用)
events_history = []


# ==========================================
# 網頁介面 (HTML/JS)
# ==========================================
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>LINE Beacon</title>
    <style>
        body { font-family: "Microsoft JhengHei", sans-serif; padding: 30px; background-color: #f0f2f5; }
        .container { max-width: 1000px; margin: auto; }
        .event-card { 
            border-left: 5px solid #333; 
            padding: 15px; 
            background: white; 
            margin-bottom: 10px; 
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .status-enter { border-left-color: #28a745; background-color: #f8fff9; } 
        .status-exit { border-left-color: #dc3545; background-color: #fff8f8; }
        
        .timestamp { color: #888; font-size: 0.85em; float: right; }
        .status-tag { 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 20px; 
            font-size: 0.9em; 
            font-weight: bold;
            color: white;
            margin-right: 10px;
        }
        .tag-enter { background-color: #28a745; }
        .tag-exit { background-color: #dc3545; }
        
        .user-id-box { 
            background: #e9ecef; 
            padding: 2px 6px; 
            border-radius: 4px; 
            font-family: monospace; 
            word-break: break-all; 
            color: #495057;
            font-size: 0.9em;
        }
        
        .beacon-info { color: #555; font-size: 0.9em; margin-top: 8px; background: #eee; padding: 5px 10px; border-radius: 4px; display: inline-block; }
        pre { background: #f8f9fa; padding: 10px; font-size: 11px; overflow-x: auto; border: 1px solid #ddd; display: none; margin-top: 10px; }
        .toggle-json-btn { 
            color: #007bff; 
            cursor: pointer; 
            font-size: 0.8em; 
            margin-left: 10px; 
            background: #e9f2ff; 
            border: 1px solid #007bff; 
            border-radius: 4px; 
            padding: 4px 8px;
        }
        h1 { color: #1DB446; text-align: center; }
        .coupon-sent-tag { color: #d63384; font-size: 0.8em; font-weight: bold; margin-left: 10px; }
    </style>
    <script>
        const expandedJsonIds = new Set();

        function toggleJson(eventId) {
            const pre = document.getElementById('json-' + eventId);
            const btn = document.getElementById('btn-' + eventId);
            if (expandedJsonIds.has(eventId)) {
                expandedJsonIds.delete(eventId);
                pre.style.display = 'none';
                btn.textContent = '檢視 JSON';
            } else {
                expandedJsonIds.add(eventId);
                pre.style.display = 'block';
                btn.textContent = '隱藏 JSON';
            }
        }

        function updateData() {
            fetch('/data')
                .then(response => response.json())
                .then(events => {
                    const container = document.getElementById('history');
                    container.innerHTML = ''; 
                    events.forEach((event) => {
                        const card = document.createElement('div');
                        const isEnter = event.custom_status === "入店";
                        // 優先用 LINE 的 webhookEventId
                        const eventIdRaw = event.webhookEventId || (event.received_at + '_' + event.source.userId + '_' + event.beacon.hwid);
                        const eventId = eventIdRaw.replace(/[^a-zA-Z0-9_-]/g, '_');
                        const isOpen = expandedJsonIds.has(eventId);

                        card.className = `event-card ${isEnter ? 'status-enter' : 'status-exit'}`;
                        card.innerHTML = `
                            <span class="timestamp">${event.received_at}</span>
                            <div>
                                <span class="status-tag ${isEnter ? 'tag-enter' : 'tag-exit'}">
                                    ${isEnter ? '🟢 入店' : '🔴 出店'}
                                </span>
                                <strong>使用者 ID:</strong> <span class="user-id-box">${event.source.userId}</span>
                                <span style="margin-left:10px;color:#888;font-size:.8em;">事件ID: ${event.webhookEventId || eventId}</span>
                            </div>
                            <div class="beacon-info">
                                📍 設備 HWID: ${event.beacon.hwid} | 店號(DM): ${event.store_id} 
                            </div>
                            <button id="btn-${eventId}" class="toggle-json-btn" onclick="toggleJson('${eventId}')">${isOpen ? '隱藏 JSON' : '檢視 JSON'}</button>
                            <pre id="json-${eventId}" style="display: ${isOpen ? 'block' : 'none'}">${JSON.stringify(event, null, 2)}</pre>
                        `;
                        container.appendChild(card);
                    });
                });
        }
        setInterval(updateData, 2000);
        updateData();
    </script>
</head>
<body>
    <div class="container">
        <h1>LINE Beacon 進出追蹤</h1>
        <div id="history">等待 Beacon 訊號...</div>
    </div>
</body>
</html>
'''

# ==========================================
# 功能函式
# ==========================================
def send_push_message(reply_token, text):
    if not reply_token: 
        print(">>> [Reply API] 缺少 replyToken，無法回覆")
        return
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f">>> [Reply API] 狀態碼: {res.status_code}, 回應: {res.text}")
    except Exception as e:
        print(f">>> [Reply API] 錯誤: {e}")

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/data')
def get_data():
    return jsonify(events_history)

@app.route("/callback", methods=['POST'])
def callback():
    global events_history
    try:
        data = request.get_json()
        if not data or 'events' not in data:
            return 'OK', 200

        for event in data['events']:
            if event.get('type') == 'beacon':
                user_id = event['source']['userId']
                hwid = event['beacon']['hwid']
                dm = event['beacon'].get('dm', '0000000000')
                store_id = dm[4:6] if len(dm) >= 6 else "??"
                event['store_id'] = store_id

                event['custom_status'] = "入店"
                print(f"🟢 [入店通知] 用戶 {user_id[:8]}... 進入了店舖 {store_id}")
                
                # 使用 replyToken 呼叫 Reply API
                reply_token = event.get('replyToken')
                msg = f"歡迎光臨【店舖 {store_id}】！\n恭喜您獲得專屬優惠券 🎁"
                send_push_message(reply_token, msg)

                event['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                events_history.insert(0, event)

                if len(events_history) > 50:
                    events_history.pop()

        return 'OK', 200
    except Exception as e:
        print(f"!!! 伺服器處理錯誤: {e}")
        return 'Internal Server Error', 500

if __name__ == '__main__':
    print("=== LINE Beacon POC 伺服器啟動中 ===")
    app.run(port=5000, debug=True)
