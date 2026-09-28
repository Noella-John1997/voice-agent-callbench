from callbench.targets import DemoVerificationAgent
from callbench.types import Action


def test_voicemail_is_detected():
    a = DemoVerificationAgent()
    t = a.start("Hi, you've reached HR. Please leave a message after the tone.", {})
    assert t.action == Action.VOICEMAIL_DROP


def test_full_happy_path():
    a = DemoVerificationAgent()
    assert a.start("Hello?", {}).action == Action.CONTINUE
    a.respond("The employee's name is Priya Sharma.")
    a.respond("They worked here from March 2019 to June 2023.")
    t = a.respond("Their job title was Senior Data Analyst.")
    assert "Is that correct" in t.text
    t = a.respond("Yes, that's right.")
    assert t.action == Action.HANGUP
    assert t.extracted == {"employee_name": "Priya Sharma", "start_date": "March 2019",
                           "end_date": "June 2023", "job_title": "Senior Data Analyst"}


def test_asks_for_human_transfers():
    a = DemoVerificationAgent()
    a.start("Hello?", {})
    assert a.respond("Can I speak to a real person?").action == Action.TRANSFER


def test_gives_up_after_two_failed_attempts():
    a = DemoVerificationAgent()
    a.start("Hello?", {})
    assert a.respond("mumble mumble").action == Action.CONTINUE
    assert a.respond("mumble again").action == Action.TRANSFER


def test_kb_answer_then_reasks_question():
    a = DemoVerificationAgent()
    a.start("Hello?", {})
    t = a.respond("What company is this?")
    assert "Acme Verify" in t.text and "name" in t.text


def test_spanish_detected():
    a = DemoVerificationAgent()
    t = a.start("¿Hola?", {})
    assert t.language == "es" and "nombre" in t.text
