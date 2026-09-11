# Tap Tap

Beginner CTF clicker. The target is **100,000 points**, following the numbered requirements. The home page displays the game in Russian, with registration and login links. Guests can play immediately; registration signs the player in. Accounts persist in SQLite; scores reset on page reload.

## Run

Python 3.10+ with no third-party dependencies:

```sh
cd tap_tap
FLAG='OmFEST{cl1ent_s1de_sc0re_is_y0urs}' python3 app.py
```

Open http://localhost:8001. Configure `HOST`, `PORT`, `FLAG`, or `DATABASE` using environment variables. Port 8001 keeps this separate from the cookie challenge on port 8000.

Run HTTP flow tests from this directory with `python3 -m unittest -v`.

## Contestant text

Нажми 100 000 раз, чтобы получить флаг. Сможешь добраться до цели быстрее?

## Organizer solution

Open browser developer tools, inspect `game.js`, and run in the console:

```js
score = 100000;
```

Alternatively, run `setScore(100000)`. The counter updates and the flag appears immediately after the claim request completes. Clicking 100,000 times follows the same path.

The deliberate vulnerability is writable JavaScript score state, combined with a server that trusts the submitted score without verifying any clicks. A direct POST to `/api/claim` with JSON `{"score":100000}` also works. The flag is not embedded in the HTML or static JavaScript.

There is no anti-cheat, score signing, rate limiting, or security middleware. Passwords are stored in plaintext for this intentionally insecure CTF app; use disposable challenge credentials.
