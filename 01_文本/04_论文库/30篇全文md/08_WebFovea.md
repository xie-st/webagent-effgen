---
title: "WebFovea: When the Model Is Right but the Click Is Wrong Reliable Round Trips for Vision-Based Web Agents on Live Websites"
arxiv_html: https://arxiv.org/html/2610.03036v2
downloaded: 2026-10-29
converted: arxiv LaTeXML HTML -> Markdown（本地图片 + alttext 公式还原）
---

# WebFovea: When the Model Is Right but the Click Is Wrong Reliable Round Trips for Vision-Based Web Agents on Live Websites

- **Jiangang Han** · Independent Researcher · jiangangh@gmail.com

###### Abstract

We present WebFovea, a vision-based web agent that placed 2nd in the WebRetriever Challenge 2026 [[1](#bib.bib1), [2](#bib.bib3)] with a final score of 57.0 out of 100. The challenge evaluates agents end to end on Protocol III of the WebRetriever benchmark [[1](#bib.bib1)]: starting from an entry URL on a live website, the agent must operate the site’s own interface and return a verifiable answer. A capable multimodal large language model (LLM) is necessary for this, but not sufficient. The model’s decisions reach the browser through the *harness*, the code between the model and the page. At every step, four things must go right: the model’s reply must be parsed into the intended action, the action must take effect on the page, the result must be reported back accurately, and the model must be shown the information it needs. On real websites, many of the failures we observed occurred at one of these four stages rather than in the model’s reasoning. A coordinate-space mismatch placed every click at 3/4 of its intended coordinates; actions on native dropdowns, inside iframes, and in text boxes failed silently; and self-generated chat-template tokens contaminated 4.9% of task episodes. WebFovea hardens each stage and surrounds the loop with guardrails that keep the agent within the rules and its budget. The four-stage view does not depend on the model, although some individual fixes do. Because we used the same model in all four submissions, the rise of our official hidden-set score from 31.0 to 57.0 reflects changes to the harness, up to run-to-run variance on live sites. We describe the design, the evidence for each component (including negative results), a failure analysis, the limitations, and a roadmap that includes routing different steps to different models.

Code: <https://github.com/jianganghan/WebFovea>

## Introduction

Much of the information people and organizations need lives on public websites: statistical portals, regulatory filings, rankings, and dashboards. Retrieving it usually means navigating menus, setting filters, reading tables and charts, and only then reading off a value. Web agents that automate this are useful only if their answers can be trusted. The WebRetriever benchmark [[1](#bib.bib1)] evaluates such agents on 1,550 tasks on 800 real, live websites. Its Protocol III, the challenge track, asks for end-to-end retrieval: navigate from an entry URL, operate the page, and return a single answer that can be checked exactly. Success requires *both* a correct answer and a trajectory that actually reaches the evidence. The benchmark’s own results show why both are needed: navigation success alone is an insufficient predictor of task completion [[1](#bib.bib1)].

This calls for grounding at two levels:

- •

  Answer-level grounding. The answer must come from the authoritative page, reached through its interface during this session, not from parametric memory, a search engine, or a hand-crafted API call. Our logs show why this matters. After hitting a CAPTCHA, an early version of our agent answered from memory; in another task, the model wrote an entire fictitious multi-step trajectory in a single reply and submitted an answer at step 1 (§[4.2](#S4.SS2)). Web data also drifts: by the time we evaluated, some of the 100 public reference answers no longer matched the live sites (§[5.5](#S5.SS5)). In such cases, only the trajectory and the final on-screen evidence can show whether the agent’s answer was right.
- •

  Action-level grounding. Every action must land on the intended pixel or element, and its effect must be perceived correctly. For a vision-based agent, this is where many of our failures turned out to lie.

Both levels depend on the *harness*: everything between the model and the browser. We find it useful to view each step as a round trip that passes through four stages (Figure [1](#S2.F1), §[4.1](#S4.SS1)). The model’s reply is turned into an action (*parsing*), the action is carried out on the page (*execution*), the page’s reaction is reported back (*feedback*), and the next view shows the model what it needs (*observation*). When one stage breaks, even a strong model fails in ways that look like reasoning errors: it clicks empty space, retypes text that never arrived, or abandons an action that actually worked. The model is right, but the click is wrong.

The challenge restricted teams to a list of approved models, and we used the same one throughout, so the changes in our score reflect changes to the harness rather than to the model. This is not an argument for keeping the model fixed: stronger and more specialized models help, and an agent may route different steps to different models, rules, or classical vision tools (§[6.3](#S6.SS3)). But whichever model decides, its decisions still pass through the same four stages.

#### Contributions.

(1) A simple way to analyze vision-based web agents: each step is a round trip through four stages (parsing, execution, feedback, and observation), with guardrails around the loop. The view doubles as a diagnostic checklist: for any failure, ask at which stage it broke. (2) WebFovea11
1
Named after the fovea, the small central part of the retina that gives sharp vision. Just as the eye shifts its gaze to bring each detail onto the fovea, the agent examines a page one view at a time until the evidence is clear., an agent built on this view, which placed 2nd in the WebRetriever Challenge 2026 with a score of 57.0 out of 100. Across four submissions, harness changes raised its score from 31.0 to 57.0, and it lost no points in the organizers’ manual review. (3) Evidence for each stage: paired evaluations, case studies, and negative results. (4) Design principles, an explicit account of the limitations, and a prioritized roadmap, including routing steps to different models and adding classical computer-vision tools.

## Related Work

#### Web agent benchmarks.

Early benchmarks used self-hosted sites (WebArena [[3](#bib.bib4)]) or offline snapshots (Mind2Web [[4](#bib.bib5)]); OSWorld [[5](#bib.bib17)] extends evaluation to full desktop environments. WebVoyager [[6](#bib.bib6)] moved to live websites with multimodal agents. WebRetriever [[1](#bib.bib1)] scales live-site evaluation to 1,550 tasks on 800 websites spanning many industries and languages. It defines three protocols: basic navigation, navigation with operational documentation, and end-to-end retrieval. It also introduces NavEval, which judges navigation from network requests, URL trajectories, actions, and the final screenshot, and agrees with human experts 91.2% of the time. Its central finding, that navigation success alone is an insufficient predictor of task completion, motivates the challenge’s focus on Protocol III. Table [1](#S2.T1) lists the Protocol III baselines on the benchmark leaderboard. They were evaluated on a different task set with human verification, so they are not directly comparable to challenge scores.

#### Agent paradigms.

Web agents follow two broad paradigms. *Vision-based* agents take screenshots of the page and act through pixel coordinates. Examples include Claude computer use [[7](#bib.bib12)], Gemini computer use [[8](#bib.bib11)], and UI-TARS [[9](#bib.bib10)], a GUI agent model trained end to end; SeeClick [[10](#bib.bib15)] showed that better GUI grounding improves such agents. *DOM-based* agents serialize the page into indexed elements. Examples include Browser Use [[11](#bib.bib9)], Agent-E with DOM distillation and change observation [[12](#bib.bib8)], and SeeAct, which grounds GPT-4V’s action descriptions in HTML candidates [[13](#bib.bib7)]. Set-of-Mark prompting [[14](#bib.bib16)] sits between the two by overlaying element labels on the screenshot.

#### The interface between model and environment.

Most of this work improves the model or the way the page is represented to it. Closest in spirit to ours is SWE-agent [[15](#bib.bib14)], which showed that the design of the agent–computer interface strongly affects how well a language model solves software-engineering tasks. We study the analogous question for vision-based web agents: the path a given model’s decisions take to the page and back.

Table 1: Protocol III baselines on the WebRetriever leaderboard [[16](#bib.bib2)] (success rate, human-verified). †Model not on the challenge’s approved list.

| Agent | Model | SR (%) |
| --- | --- | --- |
| Claude Computer Use | claude-4-8-opus † | 47 |
| Kimi Agent | Kimi K3 † | 28 |
| Google Computer Use | gemini-2.5-pro | 21 |
| Claude Computer Use | claude-4-5-sonnet | 16 |
| Browser Use | gpt-4o | 11 |
| Agent-E | gpt-4o | 9 |
| UI-TARS-1.5 | 7B | 8 |
| SeeAct | gpt-4o | 6 |


Guardrails: closed action set $\cdot$ hard constraints $\cdot$ budgets enforced by the executor $\cdot$ no task retries $\cdot$ model-call retries


Multimodal LLM
(decides the next action)
here: claude-opus-4-6
could be: per-step routing to large or small models, rules, classical CV

Live website
Chrome over CDP
iframes, native widgets, canvas charts, obfuscated fonts

Parsing
keep the first action only; strip self-generated tokens

Execution
coordinate-space alignment; element-level select/fill; iframe DOM fallback

Feedback
DOM + child-frame fingerprints; read-back; text hash for tooltips

Observation
screenshot size cap; hover; find\_text; read\_text (de-obfuscated)
replyactioneffectchangereportview


Figure 1: Each step is a round trip through four stages. The model’s reply is parsed into an action and executed on the page; the page’s reaction comes back as feedback and as the next view. Guardrails bound the whole loop.


Table 2: The four stages and the guardrails: failures observed in our runs and the components that address them.

| Stage | What goes wrong (example from our runs) | Components |
| --- | --- | --- |
| Parsing (§ 4.2 ) | chat-template tokens typed into search boxes (4.9% of episodes); an invented trajectory with a fake final answer | first-action truncation; stripping special tokens and stray trailing markup |
| Execution (§ 4.3 ) | every click at 3/4 of its intended coordinates; native dropdowns that clicks cannot operate; keystrokes lost to the wrong focus; clicks swallowed inside iframes; an Enter the prompt promised but the executor never sent | coordinate-space alignment; select ; fill ; Enter on newline; iframe DOM fallback |
| Feedback (§ 4.4 ) | a successful iframe click reported as “no detectable change”, steering the model away; failed inputs invisible in the screenshot | DOM and child-frame fingerprints; notes naming the element hit; fill read-back; tooltip text hash |
| Observation (§ 4.5 ) | values that appear only on hover; targets far down long pages; digits hidden by custom fonts; verification tools not used when needed | screenshot size cap; hover ; find_text ; read_text ; rule-based triggers |
| Guardrails (§ 4.6 ) | shortcuts through URLs and data APIs; endless repetition; tasks lost to a crashed worker or a failed API call | closed action set; hard constraints; executor budgets; scroll breaker; retries and dispatch |

## Task Setting

#### Protocol III.

Each task gives a natural-language instruction and an entry URL. The agent must operate the live site and call finished(content=...) with its answer. Tasks span document extraction, form interaction, multi-source comparison, complete data retrieval, and chart analysis [[1](#bib.bib1)]. There is no partial credit. Final scores combine answer correctness with a manual review of trajectories and code.

#### Submission and runtime.

Teams submit code to a private repository, and the organizers run it on 100 hidden tasks in a designated sandbox, as the challenge rules require [[2](#bib.bib3)]. The agent drives a Chrome browser over the Chrome DevTools Protocol (CDP) at a 1920 $\times$ 1080 viewport, within a fixed time budget per evaluation run. Each team gets at most one evaluation per day over a seven-day window, and only an aggregate score is returned. Models are called through an OpenAI-compatible API and must come from an approved list; the newest approved Anthropic model was Claude 4.6. We used claude-opus-4-6 throughout.

#### Validity criteria.

A score counts only if the run meets three criteria [[2](#bib.bib3)]. (i) *Step-by-step interaction*: every action follows from the current page; the agent may not bypass the interface, jump to precomputed results, or enumerate data APIs. (ii) *Real-time autonomy*: no pre-stored or cached answers. (iii) *Source compliance*: answers come from the designated site, without search engines or third-party data. Tasks may not be retried or reset once started; only individual steps may be retried (for example, after a failed model call).

#### Starting point.

We built WebFovea on the code template that the organizers gave every team: a trimmed-down copy of the WebRetriever repository’s reference implementation [[1](#bib.bib1)], an agent written for UI-TARS 1.5 [[9](#bib.bib10)]. For brevity, we also call this template the *reference implementation*. Appendix [A](#A1) lists which parts we kept and which are ours. We developed on the 100 publicly released Protocol III tasks, split into a 70-task development set (*dev70*) and a 30-task holdout set (*holdout30*) (§[5.1](#S5.SS1)).

## The WebFovea Agent

### Four stages and guardrails

At every step, the model looks at what it is shown and decides on one action. It never touches the browser directly: the harness carries its decision to the page and carries the page’s reaction back. We view this as a round trip through four stages, and a step succeeds only if all four work (Figure [1](#S2.F1), Table [2](#S2.T2)):

- •

  Parsing: what the model writes is what the harness understands.
- •

  Execution: the action the model intends is the one that happens on the page.
- •

  Feedback: the model is told what actually happened.
- •

  Observation: what the model needs to see is in front of it.

Around the loop, guardrails keep the agent within the rules and within its budget, and keep infrastructure faults from ending a task. They are not a stage of the round trip, but they decide which round trips are allowed and how many.

#### How WebFovea implements the loop.

WebFovea keeps the observe–think–act loop of the reference implementation. At each step, the model receives the task, a description of the action space and the hard constraints, the full text history of its earlier thoughts and actions, the five most recent screenshots, and, when relevant, a one-sentence *feedback note* about the previous action. It replies with a Thought and one Action. The agent is *vision-based*: the model receives no DOM or accessibility tree and acts through pixel coordinates. DOM access is confined to the executor and to two narrow text channels: the feedback notes and read\_text. Table [3](#S4.T3) lists the final action space. A single executor function is the only place where the agent can affect the browser.

Table 3: Final action space. Budgets are enforced by the executor, not only stated in the prompt.

| Action | Purpose (per-task budget) |
| --- | --- |
| click , left_double , right_single , drag , scroll , wait | Basic mouse and wait actions (inherited) |
| hover | Reveal tooltips / chart values |
| select(box, option) | Native <select> dropdowns |
| fill(box, content) | Focus, clear, type, read back |
| type(content) | Keystrokes; trailing \n presses Enter |
| hotkey(key) | Page-level keys; browser-level keys blocked |
| find_text(text) | Scroll text into view; returns no text ( $\leq$ 10) |
| read_text(near) | Read DOM text to verify a value ( $\leq$ 5) |
| back() / reload() | History back ( $\leq$ 15) / reload ( $\leq$ 2) |
| click_many(points) | Image-grid CAPTCHA only ( $\leq$ 6) |
| finished(content) | Submit answer (empty if unreachable) |

The rest of this section goes through the stages in the order a step passes through them, and ends with the guardrails.

### Parsing: reading the model’s reply as intended

![Refer to caption](images/08_WebFovea/token.png)


Figure 2: A parsing failure: a self-generated chat-template token typed into a data portal’s filter box (CSO PxStat; task: CPI for June 2022). The site filters on the literal string and returns no results. The model eventually diagnosed the problem in its own reasoning but kept re-emitting the token and ran out of its 40 steps.

We found two output failures that had nothing to do with reasoning. (i) *Invented continuations*: the model sometimes wrote the rest of the episode in one reply, with fake environment responses and a closing finished call; in one case, the agent submitted an answer at step 1 without ever seeing the data. We keep only the first Thought/Action pair. (ii) *Self-generated chat-template tokens*: the model occasionally appended tokens such as <|eot\_id|> or <|end\_of\_turn|>, probably imitating the <|box\_start|> syntax used in the prompt. These tokens were then typed into search boxes (Figure [2](#S4.F2)), and because each reply is fed back into the history, they recurred at every later step. Of the 305 task episodes we ran locally, 15 (4.9%) were contaminated; 12 of the 13 scorable ones failed, and success was 7.7% for contaminated episodes versus 41.7% for clean ones. This comparison is observational; the offline replay below shows that the fix itself is safe. We strip such tokens, together with stray markup after the action (such as <br>), while preserving <|box\_start|>/<|box\_end|>. When we replayed all 7,705 recorded steps offline, the fix changed all 551 contaminated steps and none of the 7,154 clean ones.

### Execution: making actions land

#### Coordinate-space alignment.

The reference implementation maps model coordinates to pixels with UI-TARS’s smart\_resize convention, which assumes a 28-pixel patch grid [[9](#bib.bib10), [17](#bib.bib13)]. For a 1920 $\times$ 1080 screenshot, this mapping is almost the identity, so the code treated the model’s coordinates as full-resolution pixels. Yet across 1,312 clicks in our first full run, *no* click fell to the right of $x{=}1440$ or below $y{=}810$ , and on two separate tasks the ratio between the intended and the clicked position was 4/3. A calibration experiment on a synthetic target image with six known markers showed that the API was downscaling the image before the model saw it. When we sent a 1920 $\times$ 1080 screenshot, the model’s coordinates needed a correction factor of 1.324/1.350 in $x$ / $y$ , consistent with downscaling to about 1440 $\times$ 810. When we sent 1440 $\times$ 810, the factor was 1.010/0.993.

The fix is to downscale every screenshot ourselves to at most 1440 $\times$ 810 and to map coordinates by the ratio of the *sent* image to the *actual* viewport, measured at runtime. On a real page, three targets that had been missed by 122–189 px were hit within 1–5 px (Figure [3](#S4.F3)). The model had been accurate to within a few pixels all along; the error was entirely in the conversion. On a paired set of 24 dev tasks, success rose from 8/24 to 20/24 with the version containing this fix (12 fixed, 0 broken), and the share of tasks that hit the step limit fell from 67% to 4%. That version also included other changes; we attribute most of the gain to this fix because misplaced clicks are what had kept tasks looping until they hit the step limit. Because the baseline could still take the goto shortcut (§[4.6](#S4.SS6)), which inflated its score, the true gain is, if anything, larger.

![Refer to caption](images/08_WebFovea/coord_before.png)

(a) old mapping

![Refer to caption](images/08_WebFovea/coord_after.png)

(b) after alignment

Figure 3: The same click before and after coordinate alignment (IMDb Advanced Title Search; red dot = executed click, ring added for visibility). (a) The model aimed at “Movie” at (287,400) in the downscaled image; the old mapping executed it almost unchanged at (285,396) on the 1920 $\times$ 1080 page. (b) After alignment, the model’s (284,396) is scaled by 4/3 to (379,528) and hits.

#### Acting on elements, not just pixels.

Some actions cannot be delivered by a pixel click. A native <select> opens a popup that the browser draws outside the page, so it never appears in the screenshot; in one task, the model clicked the same dropdown nine times and gave up. select locates the element at the given point and sets the option directly, trying in order an exact match, a match after normalization (“Vietnam” matches “Viet Nam”), and a substring match. Text input has a similar problem. With click+type, keystrokes go to whichever element has focus, so a slightly missed click sends them to the wrong element or nowhere; in 15 of the dev70 tasks, the model re-entered the same input at least once. fill focuses the editable element at the given point, including inside iframes and under overlays, clears it, and types real keystrokes so that autocomplete lists still appear. For native date inputs, it converts the value to ISO format.

#### Keeping the prompt’s promises.

The reference prompt told the model to end a type with \n to submit, but its executor never pressed Enter; 79 of 356 type calls (22%) had this form. The executor now presses Enter for them.

#### Iframe DOM fallback.

Embedded charts and document viewers, such as Flourish, Tableau, and SEC’s inline XBRL viewer, swallow some physical clicks. A scripted probe that made no model calls showed that three physical clicks on a cross-origin iframe near the bottom of the viewport had no effect, while one DOM-level click worked. When an action lands in a child frame and neither frame changes (as detected by the feedback stage, §[4.4](#S4.SS4)), the executor dispatches a complete sequence of DOM mouse events inside that frame (Figure [4](#S4.F4)). Frames from CAPTCHA providers are excluded: synthetic events there had no effect in our tests, and they are exactly what anti-bot systems look for.

![Refer to caption](images/08_WebFovea/iframe_click.png)

(a) click inside the iframe

![Refer to caption](images/08_WebFovea/iframe_final.png)

(b) final screenshot at finished(content=’6.7’)

Figure 4: Execution and feedback working together on a Tableau dashboard (Fragile States Index; task: Bolivia, 2024, Group Grievance). (a) The country list is inside an embedded frame at the bottom of the viewport. A first physical click on “Bolivia” had no effect. On the second, the child-frame fingerprint showed no change, so the executor dispatched a DOM click inside the frame, and the dashboard re-rendered for Bolivia. This task had never been solved in earlier runs with step limits of 40 or 80. (b) The answer is on screen, in the hover tooltip, when the agent finishes.

### Feedback: reporting what actually happened

Before and after every action, the executor records a DOM fingerprint (URL, title, node count, text length, scroll offsets, focus) and compares the two. Unlike a pixel diff, the fingerprint is not fooled by ticking clocks or rotating carousels. If nothing changed, the model receives a feedback note naming the element under the click point and whether it is clickable. Two refinements were needed. First, the fingerprint originally covered only the main frame, so a *successful* click inside an iframe was reported as “no detectable change”, and the model abandoned an action that had worked. We now also fingerprint the child frame the action lands in, and we no longer count focus moving into an iframe as a change, since that alone would make every click on an iframe look successful. Second, the fingerprint records only the length of the page text, so a tooltip replaced by another of the same length went unnoticed; for hovers and for SVG/canvas targets, we also compare a hash of the page text. Actions also report their own results: fill reads back the box’s actual value, and a failed select returns the list of available options, which the model has no other way to see.

Accurate feedback is necessary but not sufficient: on its own, it did not change the model’s behavior (§[5.4](#S5.SS4)). We therefore pair it with budgets that the executor enforces (§[4.6](#S4.SS6)).

### Observation: showing the model what it needs

The screenshot is the model’s main view, so information that never reaches it cannot inform the answer. hover reveals values that exist only in tooltips on charts and maps. find\_text works like the browser’s Ctrl+F: it scrolls the next match into view, searching child frames if the main frame has none, but it *never* returns text. The answer must still be read from the screenshot, which is the condition under which the organizers approved the tool. read\_text returns up to 600 characters of DOM text near a label. The prompt restricts it to *verifying* a value already read from the screenshot, not replacing it. Some sites hide digits behind custom fonts: the DOM holds rarely used code points that only the site’s font renders as digits. read\_text replaces each such character with “?” and reports how many it replaced. Discarding every passage that contains such characters would not work: on one site, only 3.5% of a line was obfuscated, and that 3.5% was the value we needed. The screenshot size cap (§[4.3](#S4.SS3)) also helps here: an image sent at 1440 $\times$ 810 is not resampled again by the API.

Tools help only if they are used at the right moment. We write each trigger as a rule in the prompt (“if your answer is a specific value, call read\_text once before finished”) rather than leaving it to the model’s judgment. On six targeted tasks, rewriting the trigger for find\_text as a rule raised its use from 2 tasks to 3; read\_text, written as a rule from the start, was used in 5. Being used is not the same as helping, however: read\_text fixed none of those tasks (§[5.4](#S5.SS4)). The model is often confident even when it is wrong, so it cannot reliably decide for itself when to check.

### Guardrails: rules, budgets, and robustness

#### Rules built into the harness.

An early version of the agent had a goto(url) action. An audit of its dev70 run found 692 goto calls: 18 of 70 tasks queried data APIs directly and 21 visited search engines, and 58% of its correct answers came from such shortcuts. Rather than asking the model to behave, WebFovea removes these paths from the action set, which is closed: there is no URL navigation, JavaScript, or HTTP access. goto and browser-level shortcuts (ctrl+l, F5, …) are still parsed, but only so that the executor can reject them with an explanation. What the action set cannot rule out, the prompt covers with fourteen hard constraints, including: stay on the site, set named filters through the page’s own controls, answer only from what was seen in this session (or submit an empty answer), and call finished only when the answer is visible on the *current* screenshot with filters still applied. Started tasks are never retried; after a browser disconnect, the task ends as a recorded failure. In the last 24-task regression run before submission, every final page had been reached through the site’s own interface, with no search-engine visits and no hand-built URLs. The organizers’ manual review deducted nothing.

#### Budgets enforced by the executor.

Each task gets 80 steps and 1,800 s. The two limits interact: each step includes a model call and page rendering, so the time limit is often reached first, and raising one limit without the other has little effect. Per-action budgets (Table [3](#S4.T3)) are enforced by the executor, which rejects over-budget calls with an explanation. The reference implementation’s scroll breaker ended a task after 10 consecutive scrolls. We changed it to end the task only if the page has also stopped changing, because the old rule had terminated a task that was legitimately reading a long table.

#### Robustness.

Model calls are retried on 403/429/5xx errors and timeouts, up to 6 attempts within 240 s; previously, repeated 403s or connection errors ended 4 of 305 task episodes (1.3%) at step 0. Tasks are dispatched from a shared queue rather than split statically, so a crashed worker loses one task rather than all of its remaining assigned tasks. After navigation, the executor waits between 1 and 8 s, returning as soon as the page has settled, instead of a fixed 3 s. Every exit path writes the required result files.

## Experiments

### Setup

With the organizers’ explicit permission, we developed on the 100 publicly released Protocol III tasks [[1](#bib.bib1)], split deterministically into dev70 and holdout30. We scored answers locally with exact, numeric (0.5% relative tolerance), and date matching, plus an optional LLM judge for semantic equivalence. Sixteen of the 100 sites were unreachable from our network (§[5.5](#S5.SS5)), which leaves 25 scorable tasks in holdout30. On the same code version, these 25 tasks scored 52.0% locally, and the hidden set scored 46.0 officially. The task sets differ, but the 6-point gap is within one binomial standard deviation (about 10 points for $n{=}25$ ), so we treat local numbers as a reasonable guide for relative comparisons.

### Official score trajectory

Table [4](#S5.T4) lists our four official submissions on the hidden set. Each submission bundled several changes, so gains cannot be attributed to single components. The +10 at the second submission came mostly from finishing more tasks. The first evaluation run had finished only 79 of 100 tasks when it reached its time limit; at its own accuracy (31 of 79, 39.2%), finishing 97 tasks, as the second run did, would have scored about 38. So roughly 7 of the 10 points came from completing more tasks and about 3 from answering more accurately.

Table 4: Official hidden-set scores in 2026 (answer accuracy). Manual review deducted no points from the final submission.

| Date | Score | Main additions |
| --- | --- | --- |
| Aug 29 | 31.0 | coordinate alignment, select , hover , reload ; closed action set, hard constraints |
| Aug 31 | 41.0 | find_text , back ; shared-queue dispatch |
| Sep 1 | 46.0 | token stripping; fill , Enter on newline; read_text ; scroll-breaker fix |
| Sep 2 | 57.0 | iframe fallback; find_text / read_text search child frames; 80 steps; model-call retries |

### Evidence for each stage

A 100-task evaluation cost about $170–230 and returned only an aggregate score, so we evaluated components on small targeted sets. Every paired comparison also included tasks that were *already passing*, so that regressions would show up. Table [5](#S5.T5) groups the strongest evidence by stage. The sample sizes are small, and we report them to show direction, not statistical significance. Most rows repeat numbers from §[4](#S4); the rest are new. hover, introduced together with coordinate alignment, solved 4 of 5 tasks that need tooltip values. On 8 tasks, raising the step limit from 40 to 80 increased the number solved from 0–1 to 4, and 2 of those 4 needed more than 40 steps. The reload budget was used in 5 tasks: it recovered 2 that were stuck on loading pages, saved budget in 2 others, and hurt none.

Table 5: Component evidence on local dev tasks, grouped by stage. “ $+x/-y$ ”: tasks fixed / broken in a paired comparison. $n$ counts tasks unless noted.

| Component | $n$ | Before $\rightarrow$ after |
| --- | --- | --- |
| Parsing |  |  |
| Token stripping (offline replay; $n$ = steps) | 7,705 | 551/551 fixed; 0 clean steps changed |
| Execution |  |  |
| Coordinate alignment ∗ | 24 | 8 $\rightarrow$ 20 (+12/ $-$ 0) |
| on a real page ( $n$ = targets) | 3 | miss by 122–189 px $\rightarrow$ 1–5 px |
| fill + Enter on newline | 10 | 2 $\rightarrow$ 4 (+2/ $-$ 0); 12% fewer steps |
| Execution and feedback |  |  |
| Iframe fallback (Tableau) | 1 | never solved $\rightarrow$ pass in 25 steps |
| Observation |  |  |
| hover (with alignment) | 5 | 0 $\rightarrow$ 4 |
| find_text (single task) | 1 | fail at 40 steps $\rightarrow$ pass in 12 |
| Guardrails |  |  |
| Hotkey block-list † | 10 | 0 $\rightarrow$ 2 (+2/ $-$ 0) |
| Step limit 40 $\rightarrow$ 80 | 8 | 0–1 $\rightarrow$ 4 (2 needed $>$ 40 steps) |
| Scroll-breaker criterion | 3 | 2 tasks recovered |
| reload budget | 5 | 2 recovered, 2 saved budget, 0 hurt |

∗Version-level comparison; alignment was the main change, and the baseline still had the goto shortcut. †Shipped together with the feedback notes and a later-removed goto.

### Negative results

Several changes that did not work shaped the final design:

- •

  Feedback alone does not change behavior. Adding “no detectable change” notes left 10 idle-looping tasks at 0/10, with the same 400 total steps. The notes reached the model, and its thoughts acknowledged them, yet it kept repeating the action. This is why the executor enforces budgets.
- •

  A heuristic idle breaker (stop after 6 no-change steps) terminated a task that would otherwise have succeeded and recovered none, so we reverted it.
- •

  read\_text was used in 5 of 6 targeted tasks but fixed none of them. The model looked up short, ambiguous labels (one label matched 124 elements). It also broke none, so we kept it, capped at five calls per task.
- •

  An early step-limit test (40 $\rightarrow$ 65) showed no gain. Repeated on current code (40 $\rightarrow$ 80), the comparison showed a real gain (Table [5](#S5.T5)): the first test had been run on an outdated version, a reminder to repeat ablations after upstream fixes.
- •

  The metric we chose in advance for fill (fewer repeated inputs) did not move (6 $\rightarrow$ 6). The improvement came through a different route: 12% fewer steps.

### Failure analysis

Table [6](#S5.T6) groups all 100 local tasks by their best outcome across all our runs, so the count of correct answers is an upper bound for any single version. Many of the remaining errors are not the agent’s. In 13 of these public tasks (not the hidden evaluation set), the reference answer no longer matches the live site because the data has been updated, or it uses a different metric definition (for example, 100-year versus 20-year global warming potential). Sixteen sites were unreachable from our network. The agent’s own errors are either capability gaps, meaning unsolved execution and observation problems such as canvas-only widgets and dense charts, or decision errors, which a verifier and task-type knowledge might address (§[6.3](#S6.SS3)). For the maintenance of WebRetriever [[1](#bib.bib1)] and similar live-site benchmarks, we suggest recording each reference answer together with a timestamped evidence screenshot.

Table 6: Best outcome per local task (100 public Protocol III tasks; approximate; some tasks fall into more than one bucket).

| Bucket | Tasks |
| --- | --- |
| Answered correctly (best across runs) | $\sim$ 55 |
| Reference answer outdated or defined differently | 13 |
| Site unreachable from our network | 16 |
| Structural: image-grid CAPTCHA, canvas-only UI, answer needs a typed URL or spans several pages | 6 |
| Capability gaps (iframe, chart, control) | $\sim$ 4 |
| Path not found / wrong decision | 3 |

### Cost

The average step consumed about 10.6k input and 127 output tokens; input exceeded output 83-fold, almost entirely because the five most recent screenshots are re-sent at every step. A 100-task run cost about $170–230. Prompt caching was unavailable through the mandated OpenAI-compatible endpoint.

## Discussion

### Design principles

We expect five principles, each supported by the evidence above, to apply beyond this challenge:

1. 1.

   Find the failing stage before blaming the model. Several failures that looked like reasoning errors, such as clicking empty space (§[4.3](#S4.SS3)) or abandoning an iframe click that had worked (§[4.4](#S4.SS4)), were execution or feedback failures.
2. 2.

   Define each action consistently everywhere it appears: in the prompt that describes it, the parser, the executor, and the feedback it produces. If any of these is missing, the action fails silently: hover could be executed but was never described to the model; the Enter on \n was promised but never pressed; the parser did not strip <|eot\_id|>. Automated tests now check this consistency.
3. 3.

   Enforce budgets in the executor, not the prompt. Prompt instructions alone did not stop repeated actions; hard limits with an explanation did.
4. 4.

   Write trigger conditions as rules, not as invitations to use a tool “when needed”.
5. 5.

   Add a compound action only when it removes a class of silent failure. fill was added because keyboard focus cannot be verified from a screenshot, not to save steps. That its measured gain came through fewer steps anyway (§[5.4](#S5.SS4)) shows why the mechanism and the outcome should be measured separately.

### Limitations

Our evidence has clear limits. (i) *One model.* All results use claude-opus-4-6. The four-stage view is model-agnostic, but we have not shown that each fix transfers, and some (coordinate alignment, token stripping) address problems specific to this model and its API. (ii) *No same-model baseline on the hidden set.* We never submitted the reference implementation itself, so the 31.0 starting point already includes several of our fixes; locally, the reference implementation with our model solved none of a 10-task subset. (iii) *Small samples.* Component evidence comes from targeted sets of 1–24 tasks and shows direction, not significance. (iv) *Live websites.* Sites change and some were unreachable from our network, so repeated runs of the same version vary, and each official score comes from a single run. (v) *Development data.* We developed on the public Protocol III tasks, so our local numbers are not comparable to leaderboard scores [[16](#bib.bib2)].

### Future work

We list future directions roughly in order of expected payoff relative to effort:

- •

  Routing steps to different models. Steps differ in what they need: locating a control, reading a dense table, deciding when to stop. Each step can go to a large or small multimodal model, a rule, or a classical vision routine, while the four stages and the guardrails stay the same.
- •

  Classical computer vision for feedback and observation. OCR to cross-check values read from screenshots; perceptual-hash change detection that catches canvas and image updates invisible to the DOM fingerprint; template matching for recurring widgets. The aim is an agent that keeps looking until the evidence is clear.
- •

  An independent verifier. Before finished, a separate model call with a fresh context, seeing only the task, the final screenshot, and the candidate answer, checks the answer, targeting wrong-row and wrong-table errors.
- •

  Native API with prompt caching and tool-use actions. Outside the challenge’s API constraints, this would cut cost by an estimated 55–70% and remove free-text parsing, and with it most parsing failures.
- •

  Hybrid observation. A list of interactive elements with coordinates, shown alongside the screenshot. This should be A/B-tested, since SeeAct [[13](#bib.bib7)] shows that hybrids are not automatically better.
- •

  Download-and-parse for PDF and spreadsheet sources, and task-type skills: short per-category checklists plus per-site operating notes, similar to the operational documentation of WebRetriever’s Protocol II [[1](#bib.bib1)].
- •

  Synthetic tasks and fine-tuning. Tasks with programmatic ground truth can be generated on the same sites, and teacher trajectories distilled into a smaller open model, to cut cost and internalize the prompt rules.

## Conclusion

In our experience, when a vision-based web agent fails on a live website, the cause often lies not in its reasoning but in how its decisions are carried out and reported back. WebFovea treats every step as a round trip through four stages (parsing, execution, feedback, and observation) and surrounds the loop with guardrails. Making these stages reliable raised its WebRetriever Challenge score from 31.0 to 57.0 across four submissions and placed it 2nd. Because the four-stage view does not depend on the model, it should carry over to stronger models, to combinations of models, and to new environments. Our main advice to builders of web agents: before blaming the model, check that its decisions actually reach the page, and that the page’s response actually reaches the model.

## Code Availability

The source code of WebFovea is publicly available on GitHub:

<https://github.com/jianganghan/WebFovea>

## Acknowledgments

We thank the organizers of the WebRetriever Challenge 2026 at Mininglamp Technology and the authors of WebRetriever [[1](#bib.bib1)] for the benchmark, the evaluation infrastructure, and timely answers to our questions about the rules.

## Disclosure of AI Use

Separately from the agent’s own model (claude-opus-4-6, §[3](#S3)), the author used Claude Code (Anthropic), an AI coding assistant, throughout this project: to implement and test agent components, to analyze experiment logs, and to help draft this report. The author conceived the approach and set the research direction; decided which failures to investigate and which changes to adopt, keep, or revert; designed the experiments and judged what their results did and did not show; checked the agent’s behavior against its trajectories; and reviewed all code, analyses, and text. The author takes full responsibility for the content.

## References

- [1]
  W. Dong, T. Fu, Z. Yu, H. Wang, A. Su, Z. Fang, Y. Chen, S. Wang, M. Wu, P. Jiang, Z. Lei, and C. Zhao (2026)
  WebRetriever: a large-scale comprehensive benchmark for efficient web agent evaluation.
  Note: arXiv:2607.06118
  External Links: 2607.06118
  Cited by: [§1](#S1.p1.1),
  [§2](#S2.SS0.SSS0.Px1.p1.1),
  [§3](#S3.SS0.SSS0.Px1.p1.1),
  [§3](#S3.SS0.SSS0.Px4.p1.1),
  [§5.1](#S5.SS1.p1.1),
  [§5.5](#S5.SS5.p1.1),
  [6th item](#S6.I2.i6.p1.1),
  [Acknowledgments](#Sx2.p1.1),
  [Abstract](#abstract1.1).
- [2]
  Mininglamp Technology (2026)
  WebRetriever Challenge 2026.
  Note: <https://mininglamp-ai.github.io/WebRetriever_Challenge/>
  Cited by: [§3](#S3.SS0.SSS0.Px2.p1.1),
  [§3](#S3.SS0.SSS0.Px3.p1.1),
  [Abstract](#abstract1.1).
- [3]
  S. Zhou, F. F. Xu, H. Zhu, X. Zhou, R. Lo, A. Sridhar, X. Cheng, T. Ou, Y. Bisk, D. Fried, U. Alon, and G. Neubig (2024)
  WebArena: a realistic web environment for building autonomous agents.
  In International Conference on Learning Representations (ICLR),
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- [4]
  X. Deng, Y. Gu, B. Zheng, S. Chen, S. Stevens, B. Wang, H. Sun, and Y. Su (2023)
  Mind2Web: towards a generalist agent for the web.
  In Advances in Neural Information Processing Systems (NeurIPS),
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- [5]
  T. Xie, D. Zhang, J. Chen, X. Li, S. Zhao, R. Cao, T. J. Hua, Z. Cheng, D. Shin, F. Lei, Y. Liu, Y. Xu, S. Zhou, S. Savarese, C. Xiong, V. Zhong, and T. Yu (2024)
  OSWorld: benchmarking multimodal agents for open-ended tasks in real computer environments.
  Note: arXiv:2404.07972
  External Links: 2404.07972
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- [6]
  H. He, W. Yao, K. Ma, W. Yu, Y. Dai, H. Zhang, Z. Lan, and D. Yu (2024)
  WebVoyager: building an end-to-end web agent with large multimodal models.
  In Proceedings of the Annual Meeting of the Association for Computational Linguistics (ACL),
  Cited by: [§2](#S2.SS0.SSS0.Px1.p1.1).
- [7]
  Anthropic (2024)
  Introducing computer use, a new Claude 3.5 Sonnet, and Claude 3.5 Haiku.
  Note: <https://www.anthropic.com/news/3-5-models-and-computer-use>
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [8]
  G. Comanici, E. Bieber, M. Schaekermann, I. Pasupat, N. Sachdeva, et al. (2025)
  Gemini 2.5: pushing the frontier with advanced reasoning, multimodality, long context, and next generation agentic capabilities.
  Note: arXiv:2507.06261
  External Links: 2507.06261
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [9]
  Y. Qin, Y. Ye, J. Fang, H. Wang, S. Liang, et al. (2025)
  UI-TARS: pioneering automated GUI interaction with native agents.
  Note: arXiv:2501.12326
  External Links: 2501.12326
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1),
  [§3](#S3.SS0.SSS0.Px4.p1.1),
  [§4.3](#S4.SS3.SSS0.Px1.p1.1).
- [10]
  K. Cheng, Q. Sun, Y. Chu, F. Xu, Y. Li, J. Zhang, and Z. Wu (2024)
  SeeClick: harnessing GUI grounding for advanced visual GUI agents.
  Note: arXiv:2401.10935
  External Links: 2401.10935
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [11]
  M. Müller and G. Žunič (2024)
  Browser Use: enable AI to control your browser.
   GitHub.
  Note: <https://github.com/browser-use/browser-use>
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [12]
  T. Abuelsaad, D. Akkil, P. Dey, A. Jagmohan, A. Vempaty, and R. Kokku (2024)
  Agent-E: from autonomous web navigation to foundational design principles in agentic systems.
  Note: arXiv:2407.13032
  External Links: 2407.13032
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [13]
  B. Zheng, B. Gou, J. Kil, H. Sun, and Y. Su (2024)
  GPT-4V(ision) is a generalist web agent, if grounded.
  In Proceedings of the 41st International Conference on Machine Learning (ICML),
  Proceedings of Machine Learning Research, Vol. 235, pp. 61349–61385.
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1),
  [5th item](#S6.I2.i5.p1.1).
- [14]
  J. Yang, H. Zhang, F. Li, X. Zou, C. Li, and J. Gao (2023)
  Set-of-Mark prompting unleashes extraordinary visual grounding in GPT-4V.
  Note: arXiv:2310.11441
  External Links: 2310.11441
  Cited by: [§2](#S2.SS0.SSS0.Px2.p1.1).
- [15]
  J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, and O. Press (2024)
  SWE-agent: agent-computer interfaces enable automated software engineering.
  Note: arXiv:2405.15793
  External Links: 2405.15793
  Cited by: [§2](#S2.SS0.SSS0.Px3.p1.1).
- [16]
  WebRetriever Team (2026)
  WebRetriever leaderboard.
  Note: <https://mininglamp-ai.github.io/WebRetriever/>Accessed September 2026
  Cited by: [Table 1](#S2.T1),
  [§6.2](#S6.SS2.p1.1).
- [17]
  S. Bai, K. Chen, X. Liu, J. Wang, W. Ge, et al. (2025)
  Qwen2.5-VL technical report.
  Note: arXiv:2502.13923
  External Links: 2502.13923
  Cited by: [§4.3](#S4.SS3.SSS0.Px1.p1.1).

## Appendix A Component Inventory

Table [7](#A1.T7) lists every component of WebFovea. For each one, it gives the stage it belongs to (§[4.1](#S4.SS1)) and where it came from: *inherited* unchanged from the reference implementation, *modified* from it, or *new*. The table also includes components that the main text mentions only briefly, such as back, reload, click\_many, and the task dispatcher.

Table 7: Component inventory. Not listed (inherited unchanged): CDP connection and authentication, click/scroll/drag primitives, randomized keystroke delay, no-cache request headers.

| Stage | Component | Origin | Stage | Component | Origin |
| --- | --- | --- | --- | --- | --- |
| Parsing | first-action truncation | new | Observation | 5-screenshot window + full text history | inherited |
| Parsing | special-token / trailing-markup stripping | new | Observation | screenshot size cap (1440 $\times$ 810) | new |
| Parsing | answer extraction from finished | modified | Observation | hover exposed to the model | modified |
| Execution | coordinate-space alignment | new | Observation | find_text (frame-aware, returns no text) | new |
| Execution | select for native dropdowns | new | Observation | read_text with de-obfuscation | new |
| Execution | fill with date handling | new | Observation | rule-based tool triggers | new |
| Execution | Enter on trailing \n | new | Guardrails | closed action set; goto rejected | new |
| Execution | iframe DOM fallback | new | Guardrails | browser-level hotkey block-list | new |
| Execution | click_many (image-grid CAPTCHA only) | new | Guardrails | 14 hard constraints | new |
| Execution | back , reload | new | Guardrails | executor budgets; 80 steps / 1,800 s | modified |
| Feedback | DOM fingerprint + notes | new | Guardrails | scroll breaker (requires no change) | modified |
| Feedback | child-frame fingerprint | new | Guardrails | no task retries; model-call retries | modified |
| Feedback | tooltip text hash | new | Guardrails | shared-queue dispatch; adaptive settle wait | modified |
| Feedback | fill read-back; select option list | new |  |  |  |
