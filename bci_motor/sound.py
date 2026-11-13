def beep(freq=880, ms=250):
    """Pitido para guiar la calibración (con los ojos cerrados no se ve la pantalla)."""
    try:
        import winsound
        winsound.Beep(freq, ms)
    except Exception:
        print("\a", end="", flush=True)
