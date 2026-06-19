import core
try:
    script = "In Dari, the national language of Afghanistan, Noor means light. Yet, a profound darkness has fallen over Afghanistan’s girls and women."
    res = core.generate_storyboard("/Users/athakur/Downloads/taliban", script, "moondream")
    print("SUCCESS:")
    print(res)
except Exception as e:
    print("ERROR:", e)
