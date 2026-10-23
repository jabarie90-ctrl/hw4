# AI_prompts.md

Log of what I typed to the vibe coder for Homework 4. Runtime prompts the agent reads live are in `backend/prompts/`.

---

## Problem 1: Vibe coder prompts

**Prompt I typed:** Start an AI_prompts.md for HW4 and keep a section for each problem with what I actually ask you.

**Follow-up prompt:** For each section add one follow-up and a short note on what was missing after the first ask.

**What was lacking after the first prompt:** The first version didn’t spell out the follow-up / “what was lacking” lines the rubric wants.

---

## Problem 2: Analyze the database

**Prompt I typed:** Open campus_customs.db and explain the tables — especially catalogue, inventory, and users — in harness.md with why each field matters for the shop.

**Follow-up prompt:** Keep the wording plain; don’t invent columns that aren’t there.

**What was lacking after the first prompt:** Needed clearer “why it matters” lines, not just a field list.

---

## Problem 3: Build the Campus Customs website

**Prompt I typed:** Build a React + Vite TypeScript Campus Customs site with Home, About, Products, a product detail page, and a chat box in the corner.

**Follow-up prompt:** Load real products and images from the database through a small FastAPI backend.

**What was lacking after the first prompt:** Cards were empty until the API and image paths were wired.

---

## Problem 4: Create account and login

**Prompt I typed:** Help me create-account / login behavior, where users are stored, and how passwords should be handled for this custom shop

**Follow-up prompt:** Make sure the seeded test user still logs in with the same hash settings as new signups.

**What was lacking after the first prompt:** Needed the salt reused on login and a constant-time compare so the test account actually worked.

---

## Problem 5: PydanticAI agent backend

**Prompt I typed:** Put a PydanticAI shop chatbot behind FastAPI that the site chat can call — prompt.md, agent.py, tools.py, models.py next to main.py.

**Follow-up prompt:** Write in harness.md how the front end talks to FastAPI and how the agent loads the prompt and model.

**What was lacking after the first prompt:** The chat route and the four agent files needed to be clearly separated from the rest of the API.

---

## Problem 6: Tools for product info and stock

**Prompt I typed:** Add tools so the agent reads real price, description, and size stock from the database and says when a size is out of stock.

**Follow-up prompt:** Update the system prompt so it has to use those tools instead of guessing numbers.

**What was lacking after the first prompt:** Out-of-stock needed to be per size, not a vague “maybe available.”

---

## Problem 7: Chat search that updates the page

**Prompt I typed:** If someone asks what hoodies you have, search the catalogue and show matching product cards on the page that still open the detail view.

**Follow-up prompt:** Send structured product matches back from the chat API so the page can render them.

**What was lacking after the first prompt:** Results were stuck in the chat bubble until the front end had a place to show the cards.

---

## Problem 8: Customer memory

**Prompt I typed:** For logged-in shoppers, save chat history and reload it when they come back. Also tell the agent which product page they’re on so “this” makes sense.

**Follow-up prompt:** Pass the customer’s name and email into the agent context.

**What was lacking after the first prompt:** History alone wasn’t enough — page product id had to travel with the chat request.

---

## Problem 9: Usability improvements

**Prompt I typed:** Add two front-end and two backend/agent usability improvements, and write usability.md with what each is and why it helps.

**Follow-up prompt:** Double-check every item actually shows up in the running app.

**What was lacking after the first prompt:** Needed concrete features (filter, recently viewed, search cap, suggestion chips), not a vague list.

---

## Problem 10: Style the website

**Prompt I typed:** Make the site feel like a real Campus Customs storefront and write design.md on what changed and why it should help people buy.

**Follow-up prompt:** Don’t leave it looking like the default Vite starter.

**What was lacking after the first prompt:** Needed clearer brand hierarchy and a bit of motion called out in the write-up.

---

## Problem 11: Site testing

**Prompt I typed:** Make an app_check.html page with screenshots for inventory chat, the dynamic search cards, and one usability feature.

**Follow-up prompt:** Keep the images in output/app_check_images/ and link them with relative paths.

**What was lacking after the first prompt:** Needed short captions under each shot so graders know what it proves.

---

## Problem 12: Audit trail, safety, finish harness

**Prompt I typed:** Keep an append-only audit_trail.json of agent tool use, add safety rules to the prompt, and finish harness.md.

**Follow-up prompt:** Don’t clear the audit file between runs.

**What was lacking after the first prompt:** Harness still needed loop limits and how to run front + back spelled out.

---

## Problem 13: Push to GitHub

**Prompt I typed:** Get the hw4 folder ready for a public GitHub repo — no .env, no database, no product images in git.

**Follow-up prompt:** README should say how to drop in the data pack and start the front end and back end.

**What was lacking after the first prompt:** Needed .gitignore and .env.example checked so secrets can’t slip in.
