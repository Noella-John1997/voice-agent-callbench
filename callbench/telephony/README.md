# `telephony/` - real phone calls (experimental)

The main harness tests your agent's **text brain** - fast, free, repeatable. This folder is the
last-mile check: a **real phone call** to your agent.

`twilio_caller.py` dials your agent's number, speaks a persona's script with Twilio's text-to-speech,
pauses after each line so your agent can reply, and records the call.

```bash
pip install -e ".[twilio]"
export TWILIO_ACCOUNT_SID=ACxxxx TWILIO_AUTH_TOKEN=xxxx TWILIO_FROM_NUMBER=+15550001111
python -m callbench.telephony.twilio_caller +15552223333 --persona cooperative
```

Listen to the recording in the Twilio console (Monitor → Calls).

**Note:** real calls cost money. Only call numbers you own or have permission to call.
