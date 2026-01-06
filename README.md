# LINE Beacon In-Store Tracking System

This project is a POC system built with Flask to track in-store user activity using LINE Beacon.  
It receives Beacon webhook events from the LINE Messaging API, detects user entry events, automatically replies with a promotional message, and displays real-time event history on a web dashboard.

---

##  Features

-  Receive LINE Beacon webhook (enter) events
- Automatically send messages to users via LINE Messaging API
- Real-time web dashboard (auto-refresh every 2 seconds, keep the latest 50 events in memory, show raw webhook JSON return)

---

##  Tech Stack

| Layer | Technology |
|------|-----------|
| Backend | Python / Flask |
| Frontend | HTML / CSS / JS |
| API | LINE Messaging API (Webhook / Reply API) |
| Storage | In-memory |

---

## change needed
- ACCESS_TOKEN = 'CHANGE_TO_YOUR_LINE_CHANNEL_ACCESS_TOKEN'


