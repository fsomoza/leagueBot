# WhatsApp Group Bot

This repository contains a simple example bot that can be used in a WhatsApp group.
It allows members to propose dates and times, vote on proposals, and once five
thumbs-up votes are received the proposed date is confirmed. The bot also sends a
daily reminder at 14:00 for any confirmed dates.

The implementation uses a small Flask application that receives incoming
messages from WhatsApp (e.g. via the Twilio WhatsApp API) and a scheduler to
send reminders. All proposals are persisted in a `proposals.json` file.

## Requirements

- Python 3.8+
- The `schedule`, `flask`, and `twilio` packages (install with `pip install -r requirements.txt`)
- A Twilio account configured for WhatsApp or another WhatsApp API provider

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set the required environment variables:

- `TWILIO_ACCOUNT_SID` – your Twilio Account SID
- `TWILIO_AUTH_TOKEN` – your Twilio Auth Token
- `WHATSAPP_NUMBER` – the Twilio WhatsApp number (e.g. `whatsapp:+14155238886`)
- `GROUP_NUMBER` – the recipient WhatsApp number or group

3. Run the Flask server to receive incoming WhatsApp messages:

```bash
python whatsapp_bot.py runserver
```

Expose the `/whatsapp` endpoint to Twilio (for example via ngrok) and configure
Twilio to send incoming messages to this URL.

4. In a separate process, run the scheduler which sends daily reminders:

```bash
python whatsapp_bot.py
```

The scheduler checks every day at 14:00 and sends a reminder for each confirmed
proposal.

## Interaction

- Propose a date and time by sending a message:

```
propose 2024-05-20 18:00
```

- Vote for a proposal:

```
vote 1 👍
```

Once a proposal receives five thumbs-up votes it is confirmed and an announcement is
sent to the group.
