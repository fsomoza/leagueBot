import os
import json
import schedule
import time
from flask import Flask, request, abort
from filelock import FileLock

try:
    from twilio.rest import Client
except ImportError:  # Twilio not installed in environment
    Client = None

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")  # 'whatsapp:+14155238886'
GROUP_NUMBER = os.getenv("GROUP_NUMBER")        # recipient group or user number

PROPOSALS_FILE = "proposals.json"
PROPOSALS_LOCK = PROPOSALS_FILE + ".lock"

# Emoji used for voting
THUMBS_UP = "\U0001F44D"
THUMBS_DOWN = "\U0001F44E"

app = Flask(__name__)

def load_proposals():
    """Load proposals from disk with a file lock."""
    lock = FileLock(PROPOSALS_LOCK)
    with lock:
        if os.path.exists(PROPOSALS_FILE):
            with open(PROPOSALS_FILE, "r") as f:
                return json.load(f)
        return []


def save_proposals(proposals):
    """Save proposals to disk with a file lock."""
    lock = FileLock(PROPOSALS_LOCK)
    with lock:
        with open(PROPOSALS_FILE, "w") as f:
            json.dump(proposals, f)


def send_whatsapp_message(body: str):
    """Send a message via Twilio WhatsApp API."""
    if Client is None:
        print(f"Would send: {body}")
        return
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(body=body, from_=WHATSAPP_NUMBER, to=GROUP_NUMBER)


def propose(date_str: str, time_str: str, proposer: str):
    proposals = load_proposals()
    proposal_id = len(proposals) + 1
    proposals.append({
        "id": proposal_id,
        "date": date_str,
        "time": time_str,
        "yes_votes": [],
        "no_votes": [],
        "confirmed": False,
        "proposer": proposer,
    })
    save_proposals(proposals)
    send_whatsapp_message(
        f"Proposal {proposal_id}: {date_str} {time_str} by {proposer}\n"
        f"Reply 'vote {proposal_id} {THUMBS_UP}' to approve or 'vote {proposal_id} {THUMBS_DOWN}' to reject."
    )


def vote(proposal_id: int, user: str, is_yes: bool):
    proposals = load_proposals()
    for p in proposals:
        if p["id"] == proposal_id:
            yes_votes = p.setdefault("yes_votes", [])
            no_votes = p.setdefault("no_votes", [])

            if is_yes:
                if user not in yes_votes:
                    yes_votes.append(user)
                if user in no_votes:
                    no_votes.remove(user)
            else:
                if user not in no_votes:
                    no_votes.append(user)
                if user in yes_votes:
                    yes_votes.remove(user)

            save_proposals(proposals)

            if len(yes_votes) >= 5 and not p.get("confirmed"):
                p["confirmed"] = True
                save_proposals(proposals)
                send_whatsapp_message(
                    f"Date confirmed: {p['date']} {p['time']}"
                )
            return

    send_whatsapp_message(f"Proposal {proposal_id} not found.")


def daily_reminder():
    proposals = load_proposals()
    for p in proposals:
        if p.get("confirmed"):
            send_whatsapp_message(
                f"Reminder: {p['date']} {p['time']} (proposal {p['id']})"
            )


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    body = request.values.get("Body", "").strip()
    user = request.values.get("From", "")
    tokens = body.split()
    if not tokens:
        abort(400)

    command = tokens[0].lower()
    if command == "propose" and len(tokens) >= 3:
        date_str = tokens[1]
        time_str = tokens[2]
        propose(date_str, time_str, user)
    elif command == "vote" and len(tokens) >= 3:
        try:
            proposal_id = int(tokens[1])
        except ValueError:
            send_whatsapp_message("Invalid proposal id")
            return "", 200

        vote_token = tokens[2]
        if vote_token.lower() == "yes" or vote_token.startswith(THUMBS_UP):
            vote(proposal_id, user, True)
        elif vote_token.lower() == "no" or vote_token.startswith(THUMBS_DOWN):
            vote(proposal_id, user, False)
    return "", 200


def run_scheduler():
    schedule.every().day.at("14:00").do(daily_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # Example usage: python whatsapp_bot.py runserver
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        app.run(host="0.0.0.0", port=5000)
    else:
        run_scheduler()
