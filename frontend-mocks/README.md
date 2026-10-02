# Quest City Tour — Player App Mocks

Screen mock-ups of the player app, made from [specs/frontend-design-brief.md](../specs/frontend-design-brief.md) with the Quest City Tour design system.

- **Live canvas (reference):** https://claude.ai/artifact/54hHjRQHZKxepiPzFd6KmK
- **Design system:** https://claude.ai/artifact/EZorDtth41MxdkBwtkt8CP (a copy of its `tokens.json` and `components/bundle.css` is in [ds/questcity/](ds/questcity/))

The canvas is the working copy. This folder is a snapshot of its sources, kept with the specs.

## Viewing

Open any `.dc.html` file in a browser. Each one is a single 390 × 844 phone screen, or 360 × 740 for the `Small*` files. The files are written for the canvas editor, so the `support.js` script they reference is missing here, and the fonts load from Google Fonts. Apart from that, they render as plain HTML.

## Screens

| Brief § | Screen / state | File |
|---|---|---|
| 5.1 | Welcome | [Main.dc.html](Main.dc.html), full scroll: [WelcomeFull.dc.html](WelcomeFull.dc.html) |
| 5.2 | Start confirmation | [StartConfirm.dc.html](StartConfirm.dc.html) |
| 5.3-1 | Task — with picture | [TaskPicture.dc.html](TaskPicture.dc.html) |
| 5.3-2 | Task — without picture (and no penalty yet) | [TaskNoPicture.dc.html](TaskNoPicture.dc.html) |
| 5.3-3 | Task — wrong answer | [TaskWrong.dc.html](TaskWrong.dc.html) |
| 5.3-4 | Task — hint 1 opened | [Hint1Open.dc.html](Hint1Open.dc.html) |
| 5.3-5 | Task — both hints opened | [HintsBoth.dc.html](HintsBoth.dc.html) |
| 5.3-6 | Task — reveal answer unlocked | [RevealUnlocked.dc.html](RevealUnlocked.dc.html) |
| 5.3-7 | Task — time warning | [TaskWarning.dc.html](TaskWarning.dc.html) |
| 5.3-8 | Task — offline banner | [TaskOffline.dc.html](TaskOffline.dc.html) |
| 5.3-9 | Updated by a teammate | [TeammateToast.dc.html](TeammateToast.dc.html) |
| 5.4 | Hint 1 / hint 2 confirmation | [Hint1Confirm.dc.html](Hint1Confirm.dc.html), [Hint2Confirm.dc.html](Hint2Confirm.dc.html) |
| 5.5 | Reveal confirmation, revealed answer | [RevealConfirm.dc.html](RevealConfirm.dc.html), [Revealed.dc.html](Revealed.dc.html) |
| 5.6 | Correct answer | [Correct.dc.html](Correct.dc.html) |
| 5.7-1…4 | Photo — prompt, uploading, saved, failed | [PhotoPrompt.dc.html](PhotoPrompt.dc.html), [PhotoUploading.dc.html](PhotoUploading.dc.html), [PhotoSaved.dc.html](PhotoSaved.dc.html), [PhotoFailed.dc.html](PhotoFailed.dc.html) |
| 5.8 | Landmark info; last task with See results | [Landmark.dc.html](Landmark.dc.html), [LandmarkLast.dc.html](LandmarkLast.dc.html) |
| 5.9 | Finish | [Finish.dc.html](Finish.dc.html), full scroll: [FinishFull.dc.html](FinishFull.dc.html) |
| 5.10 | Time is up | [TimesUp.dc.html](TimesUp.dc.html) |
| 5.11 | Link not valid — expired, not started yet | [LinkExpired.dc.html](LinkExpired.dc.html), [LinkNotYet.dc.html](LinkNotYet.dc.html) |
| 5.12 | 404 Not found | [NotFound.dc.html](NotFound.dc.html) |
| 5.13 | Loading | [Loading.dc.html](Loading.dc.html) |
| §4 | 360 × 740 check | [SmallTask.dc.html](SmallTask.dc.html), [SmallPhoto.dc.html](SmallPhoto.dc.html), [SmallFinish.dc.html](SmallFinish.dc.html) |

## Other files

- [canvas.json](canvas.json): the canvas layout (frame positions, titles, row headings).
- [quest-mocks.css](quest-mocks.css): the design-system tokens as CSS variables, plus screen layout classes (`qs-`). Component classes (`qc-`) come from [ds/questcity/components/bundle.css](ds/questcity/components/bundle.css).
- [img/](img/): placeholder illustrations for the task and landmark pictures. On the canvas they are uploaded assets (`/_blob/…`). Here they are linked locally.

## Design decisions not spelled out in the brief

- The answer input and **Submit** are pinned to the bottom of the Task screen. The picture, riddle, hints and Reveal answer scroll above them.
- Finish and Time is up show no game header, because the clock has stopped. Their totals take its place.
- The Ancient Serdika content on the last landmark, and the extra leaderboard teams in the Finish frames, are sample content.
