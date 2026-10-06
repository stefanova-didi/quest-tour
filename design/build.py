#!/usr/bin/env python3
"""Generate one proposal page per look-and-feel direction (and per variant) from a shared screen template.

    python3 build.py

Edit DIRECTIONS (metadata) or the screen builders and re-run. Themes live in themes/*.css; a variant
loads its parent theme first and then its own file. Icons come in four styles (outline, bold, filled,
duotone) and are picked per direction with `icons=`.
"""
from pathlib import Path

HERE = Path(__file__).parent

# ----------------------------------------------------------------------------- icons
# Outline paths (stroke) and filled shapes (fill) for the same 12 glyphs. Styles compose them.
OUTLINE = {
    "clock": '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9 2h6"/>',
    "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3M15 8l2 2"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.6.6 1 1.4 1 2.5h6c0-1.1.4-1.9 1-2.5A6 6 0 0 0 12 3z"/>',
    "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "list": '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
    "team": '<circle cx="9" cy="8" r="3.5"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20a6 6 0 0 1 12 0M14 20a4.5 4.5 0 0 1 7 0"/>',
    "pin": '<path d="M12 21s7-6.5 7-11.5a7 7 0 0 0-14 0C5 14.5 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "trophy": '<path d="M7 4h10v5a5 5 0 0 1-10 0zM7 6H4a3 3 0 0 0 3 4M17 6h3a3 3 0 0 1-3 4M12 14v4M8 21h8"/>',
}
FILLED = {
    "clock": '<path fill-rule="evenodd" d="M12 4a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm-1 4h2v4.6l3 1.7-1 1.7-4-2.3z"/><rect x="9" y="1.5" width="6" height="2" rx="1"/>',
    "key": '<path fill-rule="evenodd" d="M8 10.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9zm0 3a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z"/><path d="M10.6 12.9l-1.5-1.5L19.2 1.3l1.5 1.5-1.4 1.4 1.4 1.4-1.5 1.5-1.4-1.4-1.1 1.1 1.4 1.4-1.5 1.5-1.4-1.4z"/>',
    "lock": '<rect x="4" y="10" width="16" height="11" rx="2.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" stroke-width="2.4"/>',
    "bulb": '<path d="M12 2a7 7 0 0 0-4.6 12.3c.8.7 1.6 1.7 1.6 2.7h6c0-1 .8-2 1.6-2.7A7 7 0 0 0 12 2z"/><rect x="9" y="18.5" width="6" height="2" rx="1"/><rect x="10" y="21" width="4" height="1.8" rx=".9"/>',
    "alert": '<path fill-rule="evenodd" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1 5h2v6h-2zm0 8h2v2h-2z"/>',
    "check": '<path fill-rule="evenodd" d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm-1.6 13.8L6 11.4l1.4-1.4 3 3 6.2-6.2L18 8.2z"/>',
    "list": '<rect x="7" y="5" width="14" height="2.4" rx="1.2"/><rect x="7" y="10.8" width="14" height="2.4" rx="1.2"/><rect x="7" y="16.6" width="14" height="2.4" rx="1.2"/><circle cx="4" cy="6.2" r="1.4"/><circle cx="4" cy="12" r="1.4"/><circle cx="4" cy="17.8" r="1.4"/>',
    "camera": '<path fill-rule="evenodd" d="M9 4l-2 3H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8a1 1 0 0 0-1-1h-3l-2-3zm3 5.5a4 4 0 1 0 0 8 4 4 0 0 0 0-8z"/><circle cx="12" cy="13.5" r="2.2"/>',
    "shield": '<path fill-rule="evenodd" d="M12 2l8 3v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V5zm-1.4 13.4L6.6 11.4 8 10l2.6 2.6 5.4-5.4L17.4 8.6z"/>',
    "team": '<circle cx="9" cy="8" r="3.5"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20a6 6 0 0 1 12 0z"/><path d="M14.5 20a4.5 4.5 0 0 1 7 0z"/>',
    "pin": '<path fill-rule="evenodd" d="M12 22s7-6.5 7-11.5a7 7 0 0 0-14 0C5 15.5 12 22 12 22zm0-9a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>',
    "trophy": '<path fill-rule="evenodd" d="M7 3h10v2h3v2a4 4 0 0 1-4 4h-.3A6 6 0 0 1 13 14.9V18h3v3H8v-3h3v-3.1A6 6 0 0 1 8.3 11H8a4 4 0 0 1-4-4V5h3zM4.9 7a2.1 2.1 0 0 0 2.1 2.1V7zM17 9.1A2.1 2.1 0 0 0 19.1 7H17z"/>',
}

def icon(name: str, style: str) -> str:
    o, f = OUTLINE[name], FILLED[name]
    stroke = 'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"'
    if style == "outline":
        inner = f'<g {stroke} stroke-width="2">{o}</g>'
    elif style == "thin":
        inner = f'<g {stroke} stroke-width="1.5">{o}</g>'
    elif style == "bold":
        inner = f'<g {stroke} stroke-width="2.75">{o}</g>'
    elif style == "filled":
        inner = f'<g fill="currentColor">{f}</g>'
    elif style == "duotone":
        inner = f'<g fill="currentColor" opacity=".22">{f}</g><g {stroke} stroke-width="2">{o}</g>'
    else:
        raise ValueError(style)
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'

ICON_STYLES = ["outline", "thin", "bold", "filled", "duotone"]

# ----------------------------------------------------------------------------- illustrations
DOMES = '''<svg viewBox="0 0 320 200" role="img" aria-label="Task picture: three golden domes against the sky">
  <rect width="320" height="200" fill="var(--gold-100)"/>
  <circle cx="58" cy="48" r="22" fill="var(--gold-300)"/>
  <path d="M0 150 L60 120 L120 150 Z" fill="var(--accent-soft)"/>
  <path d="M200 150 L260 120 L320 150 Z" fill="var(--accent-soft)"/>
  <rect x="0" y="150" width="320" height="50" fill="var(--accent)"/>
  <rect x="40" y="112" width="52" height="40" fill="var(--surface)"/><path d="M40 112 A26 26 0 0 1 92 112 Z" fill="var(--gold-500)"/><rect x="64" y="70" width="4" height="18" fill="var(--gold-700)"/>
  <rect x="124" y="92" width="72" height="60" fill="var(--surface)"/><path d="M124 92 A36 36 0 0 1 196 92 Z" fill="var(--gold-500)"/><rect x="158" y="40" width="4" height="22" fill="var(--gold-700)"/>
  <rect x="228" y="112" width="52" height="40" fill="var(--surface)"/><path d="M228 112 A26 26 0 0 1 280 112 Z" fill="var(--gold-500)"/><rect x="252" y="70" width="4" height="18" fill="var(--gold-700)"/>
</svg>'''

NEVSKY = '''<svg viewBox="0 0 320 200" role="img" aria-label="Alexander Nevsky Cathedral">
  <rect width="320" height="200" fill="var(--surface-sunken)"/>
  <rect x="0" y="160" width="320" height="40" fill="var(--accent-soft)"/>
  <rect x="60" y="100" width="200" height="60" fill="var(--surface)"/>
  <path d="M60 100 L160 70 L260 100 Z" fill="var(--accent)"/>
  <rect x="120" y="60" width="80" height="50" fill="var(--surface)"/><path d="M120 60 A40 40 0 0 1 200 60 Z" fill="var(--gold-500)"/><rect x="158" y="10" width="4" height="18" fill="var(--gold-700)"/>
  <rect x="78" y="96" width="30" height="20" fill="var(--surface)"/><path d="M78 96 A15 15 0 0 1 108 96 Z" fill="var(--gold-500)"/>
  <rect x="212" y="96" width="30" height="20" fill="var(--surface)"/><path d="M212 96 A15 15 0 0 1 242 96 Z" fill="var(--gold-500)"/>
  <rect x="150" y="125" width="20" height="35" rx="10" fill="var(--accent-strong)"/>
</svg>'''

# ----------------------------------------------------------------------------- screens
def screens(style: str) -> str:
    I = {k: icon(k, style) for k in OUTLINE}
    header = f'''<header class="hdr" aria-label="Game status">
  <div class="hdr-top"><span class="clock">{I["clock"]}01:12:45</span><span class="tag">+25 min</span></div>
  <div class="hdr-prog"><span>Task 3 of 8</span><div class="prog" role="progressbar" aria-valuenow="3" aria-valuemin="0" aria-valuemax="8"><span style="width:37.5%"></span></div></div>
</header>'''
    welcome = f'''<figure class="frame"><figcaption><b>Welcome</b> · hero, rules, privacy notice, Start</figcaption>
<div class="ph">
  <section class="hero">
    <p class="kicker">Quest City Tour</p>
    <h1 class="t-display-l">Sofia Old Town Quest</h1>
    <span class="team">{I["team"]}The Explorers</span>
  </section>
  <main class="main">
    <p>Solve each riddle, walk to the place it describes, take a team photo and learn its story. Eight landmarks, one clock, no pause.</p>
    <ul class="rules">
      <li>{I["list"]}<span>Tasks are played in order. The clock runs from Start.</span></li>
      <li>{I["bulb"]}<span>Hint 1 <span class="tag">+10 min</span><br>Hint 2 <span class="tag">+15 min</span></span></li>
      <li>{I["lock"]}<span>Giving up on a task <span class="tag">+30 min</span></span></li>
      <li>{I["camera"]}<span>A team photo is required at every landmark.</span></li>
    </ul>
    <div class="notice">{I["shield"]}<span>Photos you upload are collected and kept by your host. You will not see them in the app.</span></div>
  </main>
  <div class="actions actions--plain"><button class="btn btn--primary btn--block">Start the quest</button></div>
</div></figure>'''
    task_main = f'''<main class="main">
    <div class="pic">{DOMES}</div>
    <div class="group" style="gap:8px">
      <p class="eyebrow">{I["key"]}Riddle</p>
      <p class="t-riddle">Golden domes shine over the square that bears my name. I was built to honour soldiers who fell for this land's freedom. Who am I?</p>
    </div>
    <div class="group">
      <div class="hint-open"><span class="t-caption">Hint 1 · +10 min</span><p>Look for the largest golden domes in the city centre.</p></div>
      <button class="hint-btn"><span class="ic">{I["bulb"]}Hint 2</span><span class="tag">+15 min</span></button>
      <button class="hint-btn" disabled><span class="ic">{I["lock"]}Reveal answer</span><span class="sub">after 5 tries · +30 min</span></button>
    </div>
  </main>'''
    def task_actions(n: str) -> str:
        return f'''<div class="actions">
    <div class="err">{I["alert"]}<span>Not quite. Try again.</span></div>
    <div class="field"><label for="a{n}">Your answer</label><input class="input input--error" id="a{n}" value="Saint Sofia Church" autocomplete="off"></div>
    <button class="btn btn--primary btn--block">Submit</button>
  </div>'''
    task = f'''<figure class="frame"><figcaption><b>Task</b> · wrong answer, hint 1 open, reveal locked</figcaption>
<div class="ph">
  {header}
  {task_main}
  {task_actions("1")}
</div></figure>'''
    confirm = f'''<figure class="frame"><figcaption><b>Hint confirmation</b> · the cost is shown before it is paid</figcaption>
<div class="ph">
  {header}
  {task_main}
  {task_actions("2")}
  <div class="scrim"><div class="sheet" role="dialog" aria-labelledby="sh">
    <span class="grab"></span>
    <h2 class="t-title" id="sh">Open hint 2?</h2>
    <p>This adds time to your team's total. Every phone on the team will see the hint.</p>
    <span class="cost">+15 min</span>
    <div class="btns"><button class="btn btn--primary btn--block">Open hint</button><button class="btn btn--secondary btn--block">Cancel</button></div>
  </div></div>
</div></figure>'''
    landmark = f'''<figure class="frame"><figcaption><b>Landmark info</b> · after the photo, before the next riddle</figcaption>
<div class="ph">
  {header}
  <main class="main">
    <div class="pic">{NEVSKY}</div>
    <div class="group" style="gap:8px">
      <p class="eyebrow">{I["pin"]}Landmark 3 of 8</p>
      <h1 class="t-display-l">Alexander Nevsky Cathedral</h1>
    </div>
    <p>Built between 1882 and 1912 in memory of the soldiers who died in the Russo-Turkish War of 1877–78, the war that led to Bulgaria's liberation.</p>
    <p>It is one of the largest Eastern Orthodox cathedrals in Europe: the main dome rises 45 m, and the bell tower holds twelve bells cast in Moscow, the heaviest weighing almost twelve tonnes.</p>
    <p class="t-caption">Photo saved ✓ · 2 photos ready for your album</p>
  </main>
  <div class="actions actions--plain"><button class="btn btn--primary btn--block">Next riddle</button></div>
</div></figure>'''
    finish = f'''<figure class="frame"><figcaption><b>Finish</b> · total, breakdown, leaderboard, host message</figcaption>
<div class="ph">
  <section class="curtain">
    <div class="badge" style="justify-self:center">{I["trophy"]}</div>
    <h1 class="t-display-xl">You did it!</h1>
    <p class="t-timer-xl">02:58:30</p>
    <p class="t-caption" style="color:inherit;opacity:.85">The Explorers · 8 of 8 landmarks</p>
  </section>
  <main class="main" style="gap:16px">
    <dl class="sum">
      <div><dt>Walking and solving</dt><dd>02:23:30</dd></div>
      <div><dt>Hints (3)</dt><dd class="pen">+35 min</dd></div>
      <div><dt>Revealed answers (0)</dt><dd class="pen">+0 min</dd></div>
      <div class="total"><dt>Total time</dt><dd>02:58:30</dd></div>
    </dl>
    <table class="lb" aria-label="Leaderboard">
      <thead><tr><th>#</th><th>Team</th><th class="t">Time</th><th class="h">Hints</th></tr></thead>
      <tbody>
        <tr><td class="n">1</td><td>Tram 5</td><td class="t">02:41:10</td><td class="h">1</td></tr>
        <tr><td class="n">2</td><td>Banitsa Club</td><td class="t">02:52:00</td><td class="h">2</td></tr>
        <tr class="me"><td class="n">2</td><td>The Explorers</td><td class="t">02:52:00</td><td class="h">3</td></tr>
        <tr><td class="n">4</td><td>Lost in Lozenets</td><td class="t">03:10:45</td><td class="h">4</td></tr>
      </tbody>
    </table>
    <p class="t-caption">Thank you for playing! Keep an eye on your inbox, your host is preparing a surprise.</p>
  </main>
</div></figure>'''
    return welcome + task + confirm + landmark + finish

# ----------------------------------------------------------------------------- directions
DIRECTIONS = [
    dict(
        num="00", slug="baseline", title="Limestone & Patina", icons="outline",
        ref="The current system: Nevsky cathedral limestone, copper-patina roofs, gilded domes, theatre red.",
        thesis="Reference point. The tokens exactly as they are in the app today, so every other direction is judged against it.",
        type=("Fraunces", "Atkinson Hyperlegible Next", "Atkinson Hyperlegible Mono"),
        notes={
            "Why it works": ["Warm, calm, already built and tested.", "Palette is tied to real Sofia materials.", "Contrast numbers documented in tokens.json."],
            "Where it is weak": ["Cream + serif + green reads as generic 'heritage app'.", "No Cyrillic story: Fraunces has no Cyrillic, Atkinson Next has limited coverage.", "Header and hero are the same green, so screens look alike."],
            "Change needed in app": ["None. This is the shipped look."],
        },
    ),
    dict(
        num="00b", slug="patina-guidebook", title="Limestone & Patina · Guidebook", parent="00-baseline", icons="thin",
        ref="Same palette as 00, set like a printed city guide: hairline frames, small caps, a serif with full Cyrillic, tick-marked progress.",
        thesis="Quiet and bookish. One-pixel borders replace shadows, labels are small caps, the progress bar is ticked per task, and Literata takes over display duty from Fraunces.",
        type=("Literata", "Atkinson Hyperlegible Next", "Atkinson Hyperlegible Mono"),
        diff={"Components": "1px hairline borders, 8px corners, outlined secondaries, no shadows, progress bar ticked into 8 tasks.", "Fonts": "Literata (serif, Cyrillic) display and italic team name; Atkinson body unchanged.", "Highlights": "Gold-100 panels with a gold-300 hairline and small-caps gold-700 labels; outlined gold tag in the header.", "Icons": "Thin outline, 1.5px stroke."},
        notes={
            "Why it works": ["Closest to today's app, so the lowest migration cost of the variants.", "Literata adds Cyrillic and reads better than Fraunces at small sizes."],
            "Where it is weak": ["Hairlines and thin icons lose a little in glare; keep body at 17px.", "Least differentiated from the baseline at thumbnail size."],
            "Change needed in app": ["Display font swap; border variants of card, tag, hint and button; one progress rule."],
        },
    ),
    dict(
        num="00c", slug="patina-pills", title="Limestone & Patina · Pills", parent="00-baseline", icons="filled",
        recommended="Recommended · lowest cost", why_rec="Keeps the shipped palette; only radius and type tokens change, and Sofia Sans adds Bulgarian Cyrillic for free.",
        ref="Same palette as 00, rounded off: pill controls, patina-tint panels, a floating header, Sofia Sans with Bulgarian Cyrillic forms.",
        thesis="Soft and friendly. Every control is a pill, hints and eyebrows sit on a patina tint, penalties on gold pills, header and hero have rounded bottoms. Sofia Sans throughout, slightly larger body.",
        type=("Sofia Sans", "Sofia Sans", "Atkinson Hyperlegible Mono"),
        diff={"Components": "Pill buttons and inputs, 22px cards, rounded header and hero bottoms, soft shadows, tinted panels instead of borders.", "Fonts": "Sofia Sans 800 display and 400 body at 18px (Bulgarian Cyrillic); mono clock unchanged.", "Highlights": "Patina-50 tint for opened hints, hint buttons and the eyebrow chip; gold-300 pills for every penalty.", "Icons": "Filled glyphs."},
        notes={
            "Why it works": ["Reads as a modern consumer app while keeping the exact brand colours.", "Sofia Sans makes a Bulgarian UI possible with no font change."],
            "Where it is weak": ["Pill inputs waste horizontal room at 360px.", "Softest hierarchy of the three; relies on tint and size rather than lines."],
            "Change needed in app": ["Radius tokens to 10/999/22; eyebrow becomes a chip; header gains rounded bottom."],
        },
    ),
    dict(
        num="00d", slug="patina-signage", title="Limestone & Patina · Signage", parent="00-baseline", icons="bold",
        ref="Same palette as 00, with the clarity of street signage: squared frames, condensed uppercase, solid gold chips, segmented progress.",
        thesis="Bold and legible. Four-pixel corners, two-pixel ink frames, condensed uppercase display, a gold rule under the header, eight progress segments. Sofia Sans Condensed over Onest.",
        type=("Sofia Sans Condensed", "Onest", "Atkinson Hyperlegible Mono"),
        diff={"Components": "Squared 4px corners, 2px ink borders, segmented 8-step progress, gold rules under header and hero, no shadows.", "Fonts": "Sofia Sans Condensed 800 uppercase display and clock; Onest body (Cyrillic).", "Highlights": "Solid gold-500 chips with ink text; opened hints get an 8px gold left bar; ink eyebrow rule.", "Icons": "Bold outline, 2.75px stroke."},
        notes={
            "Why it works": ["Highest legibility of the three in direct sun; the timer and task counter dominate.", "Uppercase condensed display gives short, punchy landmark names."],
            "Where it is weak": ["Sternest tone; less suited to family or birthday audiences.", "Uppercase labels slow reading slightly for second-language players."],
            "Change needed in app": ["Radius tokens to 3/4/6; label transform; segmented progress rule; display font swap."],
        },
    ),
    dict(
        num="01", slug="borisova", title="Borisova Gradina", icons="outline",
        ref="Borisova gradina, the city's oldest park (1884): leaf green, fresh lime in spring, cream gravel paths, the lily pond that opens the quest.",
        thesis="Park green. A deep leaf green for actions, a fresh lime for progress and the team tag, cream-sage ground, round shapes. Friendly, modern and still clearly Sofia.",
        type=("Manrope", "Atkinson Hyperlegible Next", "Atkinson Hyperlegible Mono"),
        notes={
            "Why it works": ["Green is the brand colour the team already likes, pushed toward a fresher, younger register.", "Lime on deep green is a loud, legible progress signal in daylight.", "Pill shapes and Manrope read as a modern consumer app, which lowers the bar for first-time players."],
            "Where it is weak": ["Lime is decorative only; it never carries text, so it adds no contrast risk but also cannot be the primary action.", "Leaf motif must stay in hero and finish bands, never behind the riddle.", "Manrope is widely used; the palette and leaf shape carry the identity."],
            "Change needed in app": ["Colour tokens plus one new token <code>--lime</code> for progress, tags and the badge.", "Radius tokens to 8/14/22 and pill buttons.", "Display face Manrope (has Cyrillic)."],
        },
    ),
    dict(
        num="02", slug="patina-noir", title="Evening Domes", icons="outline",
        ref="The cathedral domes after sunset: near-black patina green, gold catching the last light, a gold rule where roof meets wall.",
        thesis="Deep patina and gold. The darkest green of the set on header, hero and finish band, a light sage reading surface in between, and a thin gold rule as the signature detail. Premium and calm, made for corporate team events.",
        type=("Commissioner", "Atkinson Hyperlegible Next", "Atkinson Hyperlegible Mono"),
        notes={
            "Why it works": ["Keeps every reading surface light, as the brief requires, while the dark bands give it a premium frame.", "Gold on deep green is the highest-contrast pairing in today's token set (6.7:1 and up).", "Commissioner is a humanist sans with full Cyrillic and a quiet, professional voice."],
            "Where it is weak": ["Dark bands can read as 'night mode' in a thumbnail; the light content area is what players see most.", "Gold must never be used as text on the light surface (fails contrast), only on green.", "The most conservative direction; least playful for a family audience."],
            "Change needed in app": ["Colour tokens only; header and curtain grounds move to <code>--accent-strong</code> at a darker value.", "A 2px gold rule under hero and curtain (<code>border-bottom</code>).", "Display face Commissioner."],
        },
    ),
    dict(
        num="02b", slug="evening-serif", title="Evening Domes · Luxe", parent="02-patina-noir", icons="thin",
        ref="Same palette as 02, with hotel-lobby restraint: hairline gold outlines, a Didone display face, small-caps labels.",
        thesis="Hairlines and serifs. One-pixel gold outlines on tags, cards and the team chip, ghost secondary buttons, a gold-outlined primary. Prata for display, Commissioner for text.",
        type=("Prata", "Commissioner", "Atkinson Hyperlegible Mono"),
        diff={"Components": "1px gold outlines, 4px corners, ghost secondaries, 3px progress hairline, underlined input base.", "Fonts": "Prata (Didone serif, Cyrillic) for display; Commissioner body; 12px spaced small-caps labels.", "Highlights": "Gold hairline tags, gold rules under eyebrows and table heads, no filled chips.", "Icons": "Thin outline, 1.5px stroke."},
        notes={
            "Why it works": ["The most premium reading; suits corporate and incentive events.", "Hairlines keep the light surface calm and the riddle dominant."],
            "Where it is weak": ["Thin strokes and 12px labels are the weakest in glare; keep body text at 17px.", "Prata has one weight, so hierarchy relies on size alone."],
            "Change needed in app": ["Tokens plus 1px border variants of tag, card and button components."],
        },
    ),
    dict(
        num="02c", slug="evening-cards", title="Evening Domes · Cards", parent="02-patina-noir", icons="filled",
        recommended="Recommended", why_rec="Best match for the brief: clearest states while walking, highest-contrast timer, per-task progress, full Cyrillic, keeps the green-and-gold brand.",
        ref="Same palette as 02, organised like a dashboard: every block is a raised card on a sage ground, controls are flat and sunken.",
        thesis="Card system. Riddle, hints, rules and leaderboard each sit on their own white card, inputs and secondary buttons are sunken, progress is eight segments, icons sit in tinted circles. Onest throughout with JetBrains Mono numerals.",
        type=("Onest", "Onest", "JetBrains Mono"),
        diff={"Components": "Raised white cards on sage, flat sunken inputs and secondaries, shadowed action bar, segmented progress.", "Fonts": "Onest 800 display and 400 body (Cyrillic); JetBrains Mono for the clock and times.", "Highlights": "Solid gold chips for penalties, patina tint for opened hints, patina chip eyebrows.", "Icons": "Filled glyphs inside tinted circles in lists."},
        notes={
            "Why it works": ["Clear chunking helps players scan while walking.", "Cards give each state (hint open, wrong answer) an obvious home."],
            "Where it is weak": ["Most visual weight of the set; the riddle competes with its container.", "Cards add 28px of padding per block, so long tourist texts scroll sooner."],
            "Change needed in app": ["Layout classes for cards on Welcome, Task and Finish; segmented progress rule."],
        },
    ),
    dict(
        num="02d", slug="evening-soft", title="Evening Domes · Soft", parent="02-patina-noir", icons="duotone",
        ref="Same palette as 02, rounded off: pill controls, a header with rounded bottom corners, soft shadows, a gold dot as the eyebrow marker.",
        thesis="Round and gentle. Pills for every control, 24px cards, a floating header, soft green shadows under primary buttons, pale gold pills for penalties. Nunito throughout.",
        type=("Nunito", "Nunito", "Atkinson Hyperlegible Mono"),
        diff={"Components": "Pill buttons and inputs, header and hero with rounded bottoms, soft shadows, 32px sheet radius.", "Fonts": "Nunito 900 display and 400 body (rounded terminals, Cyrillic).", "Highlights": "Pale gold-100 pills with gold-700 text; gold dot before eyebrows; gold ring on the badge.", "Icons": "Duotone: 22% fill under a 2px outline."},
        notes={
            "Why it works": ["Warmest take on the dark-green palette; works for families as well as companies.", "Floating header reads as a native app pattern."],
            "Where it is weak": ["Rounded terminals plus pale pills can look soft in harsh sun; keep the header tag solid gold.", "Nunito's wide counters make long riddles slightly longer."],
            "Change needed in app": ["Radius tokens to 12/999/24; header and hero gain rounded bottoms."],
        },
    ),
    dict(
        num="03", slug="vitosha", title="Vitosha Trail", icons="outline",
        ref="Vitosha mountain above the city: spruce green, granite, snow, and the red-white-red paint blazes that mark Bulgarian hiking trails.",
        thesis="Outdoor wayfinding. Snow-white ground, spruce header, a trail-blaze orange action, and contour lines in the hero. Built for glare and gloves.",
        type=("Sofia Sans Semi Condensed", "Sofia Sans", "IBM Plex Mono"),
        notes={
            "Why it works": ["The quest is a walk; hiking-sign language (blazes, contours, distance) matches the task.", "Orange primary is the most visible colour in direct sun.", "Spruce green header keeps continuity with today's patina brand."],
            "Where it is weak": ["Orange + green can look like a sports brand; the granite greys keep it calm.", "Blaze stripes are a strong motif; use once per screen at most.", "Less 'old town' than the other directions."],
            "Change needed in app": ["Colour tokens; display face Sofia Sans Semi Condensed.", "Progress bar restyled as a trail blaze.", "Radius tokens 4/8/12."],
        },
    ),
]

SWATCH_TOKENS = ["surface", "surface-sunken", "ink", "accent", "accent-strong", "gold-500", "gold-700", "theatre-500", "header-bg", "hero-bg", "curtain-bg"]

PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_prefix}{title} · Quest City Tour L&amp;F</title>
<link rel="stylesheet" href="fonts/fonts.css">
<link rel="stylesheet" href="base.css">
{theme_links}
</head>
<body>
<div class="pg">
  <nav class="pg-nav" aria-label="Proposals">{nav}</nav>
  <div class="pg-top">
    <div>
      <h1><small>{kind} {num}</small>{title}{badge}</h1>{rec_note}
      <p>{thesis}</p>
      <p><b>Sofia reference.</b> {ref}</p>
    </div>
  </div>
  {diff}
  <div class="meta">
    <div class="swatches" aria-label="Palette">{swatches}</div>
    <div class="specimen" aria-label="Typography">{specimen}</div>
  </div>
  <div class="frames">{screens}</div>
  <div class="notes">{notes}</div>
</div>
</body>
</html>
'''


def page_name(d: dict) -> str:
    return f'{d["num"]}-{d["slug"]}.html'


def nav_html(current: str) -> str:
    items = ['<a href="index.html">Overview</a>']
    for d in DIRECTIONS:
        cur = ' aria-current="page"' if d["slug"] == current else ""
        cls = ' class="sub"' if "parent" in d else ""
        label = d["title"].split(" · ")[-1] if "parent" in d else d["title"]
        star = " ★" if d.get("recommended") else ""
        items.append(f'<a href="{page_name(d)}"{cur}{cls}>{d["num"]} {label}{star}</a>')
    return "".join(items)


def specimen_html(d: dict) -> str:
    disp, body, mono = d["type"]
    return (
        f'<div class="sp sp-display"><span class="sp-name">Display · {disp}</span><span class="t-display-l">Sofia Old Town Quest · Стар град</span></div>'
        f'<div class="sp sp-body"><span class="sp-name">Text · {body}</span><span class="t-riddle">Golden domes shine over the square that bears my name. Aa Бб 0123</span></div>'
        f'<div class="sp sp-mono"><span class="sp-name">Numerals · {mono}</span><span class="t-timer-xl">01:12:45</span></div>'
    )


def diff_html(d: dict) -> str:
    if "diff" not in d:
        return ""
    cells = "".join(f'<div class="diff-cell"><h3>{k}</h3><p>{v}</p></div>' for k, v in d["diff"].items())
    return f'<div class="diff" aria-label="What differs from the parent direction">{cells}</div>'


def notes_html(notes: dict) -> str:
    out = []
    for head, items in notes.items():
        lis = "".join(f"<li>{i}</li>" for i in items)
        out.append(f'<section class="note"><h3>{head}</h3><ul>{lis}</ul></section>')
    return "".join(out)


def main() -> None:
    for d in DIRECTIONS:
        swatches = "".join(f'<span class="sw" data-n="{t}" style="background:var(--{t})"></span>' for t in SWATCH_TOKENS)
        links = []
        if "parent" in d:
            links.append(f'<link rel="stylesheet" href="themes/{d["parent"]}.css">')
        links.append(f'<link rel="stylesheet" href="themes/{d["num"]}-{d["slug"]}.css">')
        html = PAGE.format(
            title=d["title"], num=d["num"], ref=d["ref"], thesis=d["thesis"],
            kind="Variant" if "parent" in d else "Direction",
            title_prefix=(d["recommended"].upper() + " · ") if d.get("recommended") else "",
            badge=f'<span class="rec">★ {d["recommended"]}</span>' if d.get("recommended") else "",
            rec_note=f'<p class="rec-note"><b>Why recommended.</b> {d["why_rec"]}</p>' if d.get("recommended") else "",
            theme_links="\n".join(links), nav=nav_html(d["slug"]), swatches=swatches,
            specimen=specimen_html(d), diff=diff_html(d), screens=screens(d["icons"]), notes=notes_html(d["notes"]),
        )
        path = HERE / page_name(d)
        path.write_text(html, encoding="utf-8")
        print("wrote", path.name, len(html), "bytes")


if __name__ == "__main__":
    main()
