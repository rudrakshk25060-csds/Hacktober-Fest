---
title: "JobiFC: A Finishing Coach Built for My Friend"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, hacktoberfest
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01).* 

## What I Built

I built JobiFC for my friend, Jobi Anand. He told me finishing is the area he especially wants to improve, so I made it the app’s default coaching focus. After trying the finishing drill, Jobi said it fits him.

JobiFC lets him record match stats, review a small performance snapshot, and ask for a practical training suggestion. It is a practice aid, not a player rating or a replacement for his coach.

## Demo

[Watch the JobiFC walkthrough](https://github.com/rudrakshk25060-csds/Hacktober-Fest/blob/main/demo/jobifc-demo.mov)

The walkthrough shows JobiFC’s finishing focus, a match-stat entry, and a finishing drill from the coach.

## Code

[JobiFC source on GitHub](https://github.com/rudrakshk25060-csds/Hacktober-Fest)

## How I Built It

The interface uses HTML, CSS, and JavaScript, with a Python FastAPI backend. The backend validates match entries, imports CSV files, calculates the visible stats, and stores match history in a local JSON file.

For coaching, JobiFC sends the question and recent match data to **Gemma 3 4B (`gemma3:4b`) running locally through Ollama**. The app checks whether Gemma’s answer follows Jobi’s chosen focus. If it switches to another skill area, JobiFC shows a clearly labeled finishing drill instead.

## Why Does Open Innovation Matter?

Running Gemma locally let me build around Jobi’s specific goal without sending his match history to a hosted chatbot API. I can inspect and change the model call, choose where inference happens, and keep the data on the same computer during this demo. Open model tooling made that control practical for a small, personal project.

## Prize Categories

- **Best Use of Gemma** — JobiFC uses Gemma 3 4B through Ollama for its coaching flow.
