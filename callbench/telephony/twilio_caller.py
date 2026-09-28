"""EXPERIMENTAL: place a real phone call to your voice agent.

The main harness tests your agent's *text brain* quickly and cheaply. This
module is the last-mile check: it dials your agent's real phone number with
Twilio, speaks a persona's lines using Twilio's built-in TTS, pauses between
lines so your agent can answer, and records the whole call. You then listen
to (or transcribe) the recording.

Usage:
    pip install -e ".[twilio]"
    export TWILIO_ACCOUNT_SID=... TWILIO_AUTH_TOKEN=... TWILIO_FROM_NUMBER=+1...
    python -m callbench.telephony.twilio_caller +15551234567 --persona cooperative

Costs real money per minute. Only call numbers you own or have permission to call.
"""
from __future__ import annotations

import argparse
import os
from xml.sax.saxutils import escape

SCRIPTS = {
    "cooperative": ["Hello?", "The employee's name is Priya Sharma.",
                    "They worked here from March 2019 to June 2023.",
                    "Their job title was Senior Data Analyst.", "Yes, that's right.", "Okay, thank you, bye."],
    "asks_human": ["Hello?", "Can I please speak to a real person?"],
    "spanish": ["¿Hola?", "El nombre del empleado es Lucía Garcia.", "Sí, es correcto."],
}


def build_twiml(lines: list[str], pause_s: int = 6, voice: str = "Polly.Joanna") -> str:
    parts = ["<Response>"]
    for line in lines:
        parts.append(f'<Say voice="{voice}">{escape(line)}</Say><Pause length="{pause_s}"/>')
    parts.append("<Hangup/></Response>")
    return "".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("to_number", help="your agent's phone number, E.164 format")
    ap.add_argument("--persona", default="cooperative", choices=sorted(SCRIPTS))
    ap.add_argument("--pause", type=int, default=6, help="seconds to wait for the agent after each line")
    args = ap.parse_args()

    from twilio.rest import Client  # imported lazily so the core package doesn't need twilio

    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    call = client.calls.create(
        to=args.to_number,
        from_=os.environ["TWILIO_FROM_NUMBER"],
        twiml=build_twiml(SCRIPTS[args.persona], args.pause),
        record=True,
    )
    print(f"Call placed: {call.sid}. Find the recording in the Twilio console under Monitor > Calls.")


if __name__ == "__main__":
    main()
