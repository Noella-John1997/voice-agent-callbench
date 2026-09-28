from callbench.noise import ASRNoise, LatencyModel


def test_zero_noise_keeps_text():
    assert ASRNoise(0.0).apply("They worked here from March 2019") == "They worked here from March 2019"


def test_noise_is_deterministic_with_seed():
    text = "They worked here from March 2019 to June 2023 as a manager"
    assert ASRNoise(0.9, seed=3).apply(text) == ASRNoise(0.9, seed=3).apply(text)


def test_heavy_noise_changes_text():
    text = "The employee's name is Priya Sharma and they worked from March to June as an engineer"
    assert ASRNoise(1.0, seed=1).apply(text) != text


def test_latency_is_sum_of_parts():
    b = LatencyModel(seed=1).sample(think_ms=300, caller_words=5, accent_noise=0.0)
    assert abs(b.total_ms - (b.endpointing_ms + b.think_ms + b.tts_ttfb_ms + b.network_ms)) < 1e-9
    assert b.think_ms == 300
