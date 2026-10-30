# Presentation Script: Paper 167, WiCOMM 2026

**"Fail-Closed or Fail-Degraded? A Simulation Study of Forced Assurance Loss in Contested Multi-Hop QKD Networks"**
Speaker: Lakshya Jain. Co-author: Siddhi Arora.
Target length: about 9 minutes (8 slides, roughly 1,200 spoken words at a relaxed pace of 130 to 140 words per minute, plus pauses for pointing).

How to use this file: read only the plain paragraphs aloud. Anything in [square brackets] is a stage cue, not speech. Numbers are written the way you would say them.

| Slide | Heading | Time | Running total |
|---|---|---|---|
| 1 | Title | 0:30 | 0:30 |
| 2 | Motivation: When Quantum Key Runs Out | 1:10 | 1:40 |
| 3 | Research Gap and Contributions | 1:00 | 2:40 |
| 4 | System Model: Formation, Key Grades and Adversary | 1:25 | 4:05 |
| 5 | Metrics and Experimental Setup | 1:25 | 5:30 |
| 6 | Key Result: The Fail-Mode Exchange Rate | 1:30 | 7:00 |
| 7 | What Forcing Requires: Capability, Cut and Endurance | 1:15 | 8:15 |
| 8 | Conclusions and Recommendations for Operators | 0:50 | 9:05 |

---

## Slide 1. Title
*Suggested time: 0:30*

[Stand still, look at the audience, then glance at the title.]

Good morning, everyone. I'm Lakshya Jain, and this is joint work with my co-author, Siddhi Arora.

Our talk is about networks that use quantum physics to share secret keys. We ask a simple question. When such a network runs short of key, should it refuse to serve, or quietly fall back to weaker cryptography? And what does it cost an attacker to push it there?

Let me start with why this matters.

---

## Slide 2. Motivation: When Quantum Key Runs Out
*Suggested time: 1:10*

[Point to the mountains and the chain of relay towers.]

Picture a brigade in the mountains. It talks to its rear base through a chain of relay sites. [Point to the red keys on each link.] Every relay passes the key along, hop by hop, and every hop uses up secret key. So a path with n hops spends key n times over. Free-space links only make about a hundred bits per second. So key runs out long before the connection does.

At that point, the network has two choices.

[Point to the navy lock, Fail closed.] It can fail closed, and refuse the request. The commander sees an outage, and can react.

[Point to the red open lock, Fail degraded.] Or it can fail degraded, and switch to a weaker cipher. A standard, ITU-T Y.3803, allows this, as long as it is recorded. But nobody notices until an audit.

So which failure is worse? And what does an attacker have to spend to force the choice? To our knowledge, nobody had measured this on a multi-hop network. That is our gap.

---

## Slide 3. Research Gap and Contributions
*Suggested time: 1:00*

[Gesture down the four rows of the table.]

Prior work falls into four lines: routing, quality of service, key exhaustion and fallback, and adversary models. They check which path a request takes, who gets key first, and what happens when key runs out. But they all ask one question: was the request served? [Point to the column of ticks.] That is this column of ticks.

[Point to the shaded column of red crosses.] What none of them report is what protection the traffic actually got. A session that falls back to post-quantum cryptography still counts as served. We call this the missing column. How much traffic that was entitled to the strongest kind of key, one that stays secure even against unlimited computing power, was served without it?

[Point to the list on the right.] We add five things: a threat-aware model, two new metrics, a simple cut condition, evidence on five graphs, and honest checks of our own method.

First, the model.

---

## Slide 4. System Model: Formation, Key Grades and Adversary
*Suggested time: 1:25*

[Point to Figure 1 on the left, and trace the dashed orange links with the crosses.]

Our main network has eight nodes. The rear base is on the left, and the three forward posts are on the right. See the dashed orange links with the crosses? That is the minimum cut. Every session to the forward posts must cross one of those two links, and each carries just 240 bits per second. The fat fibre on the left cannot help, because its surplus is stranded one hop away.

[Point to the ladder on the right, top to bottom.] On the right is what we call the assurance ladder. Grade one is a one-time pad, the strongest. Grade two uses a quantum key inside a strong cipher. Grade three mixes quantum key with a post-quantum exchange called ML-KEM. Grade four is ML-KEM alone. Grades one and two count as key secured by physics. Three and four fall below it.

[Point to the Floors line under the ladder.] Each traffic class has a floor. Command traffic needs grade two, surveillance needs grade one, and logistics needs grade three.

[Point to the attacker icon.] The attacker raises the bit error rate, the fraction of bits that arrive wrong, on links it buys. Once that error rate passes seven and a half percent, the link aborts and stops making fresh key. But key already stored can still be spent, so the attack must outlast the stock.

Next, how we measure this.

---

## Slide 5. Metrics and Experimental Setup
*Suggested time: 1:25*

[Point to the long bar across the slide.]

Why new metrics? Because availability alone hides the damage. Look at fail-degraded under the held cut. Ninety-seven point five percent is served. But only six point six percent, the navy sliver, is at its proper grade. The red part is below it. So we split availability, A, into compliant service, Q, and below-floor service, L.

[Point to F, the middle definition.] Our headline metric is forced assurance loss, F. It is the share of entitled requests that end up below the strongest key. Blocked requests stay in the count, so the two fail modes are compared fairly.

[Point to the T-star definition on the right.] A simple cut condition gives us a clock. The stock behind the cut, divided by the demand, is T-star. With stores at two percent, that is one point four four hours. After that, only refusal or fallback is left.

[Point to the line at the bottom.] We ran twenty-four hour attacks, twelve paired seeds, and bootstrap confidence intervals. A forty-three-check gate and a hundred and twenty-seven tests run first. We also checked our key accounting against four published measurements. Two of them did not match, and we say so in the paper.

Now, the result.

---

## Slide 6. Key Result: The Fail-Mode Exchange Rate
*Suggested time: 1:30*

[Pause, then gesture to both doughnuts.]

This is the result I would like you to remember. Same attack, same network, two fail modes.

[Point to the left doughnut, Fail closed.] Fail closed: almost everything is refused. Only six point seven percent is served at its proper grade.

[Point to the right doughnut, Fail degraded.] Fail degraded: almost everything is served, ninety-seven point five percent. But only six point six percent is at its proper grade. The red ring is service below the floor.

[Point to the large 90.1% on the right.] That is ninety point one percent of entitled requests losing the strongest protection. And ninety-three percent of served sessions end up on ML-KEM alone.

So the fallback does not buy assurance back. [Pause.] It hides the loss.

[Point to 87.6–92.9% at the bottom right.] This is not a quirk of one graph. On all five graphs, a held cut forces eighty-eight to ninety-three percent, and fail-closed service follows the stock-over-demand bound: it predicts six, nine and twelve percent, and we observe about six and a half, nine point six and twelve point three.

So what does it take to force this?

---

## Slide 7. What Forcing Requires: Capability, Cut and Endurance
*Suggested time: 1:15*

[Point to the three headings on the right, top to bottom.]

Three things, and the attacker needs all of them.

First, capability. A link only shuts down once the added error reaches zero point zero four five. Below that, under a tenth of a percent is forced.

Second, a cut. [Point to the flat red line in the chart.] An attacker who recomputes link importance after each removal needs only the two-link cut, however long the chain. A naive ranking, the rising navy line, makes depth look protective. It is not.

Third, endurance. [Point to the hourglass.] Stored key is a buffer, and the attacker has to drain it. With stores at two percent, first forcing comes after about one and a half hours. From full stores, nothing is forced in twenty-four hours. So stock is a real defence.

[Point to the small grey line at the bottom right.] We also tested key-aware routing, reservation floors, and a small learned controller. Each moves the numbers a little. The learned controller gains about one part in a thousand in score, and pays for it in one-time-pad traffic. None of them changes this picture.

Let me wrap up.

---

## Slide 8. Conclusions and Recommendations for Operators
*Suggested time: 0:50*

[Point to the takeaway sentence at the top.]

Let me summarise. Refusing costs availability. Degrading quietly costs assurance, and under a held cut that is about ninety percent of entitled traffic. An attacker needs capability, a cut and time, so stock behind the cut is a real defence.

[Point to the three rules on the left.] That gives operators three rules. Report Q and F next to availability. Keep enough stock behind the minimum cut for T-star hours of the attacks you fear. And set fail modes per traffic class, with a price on every exception.

If you remember one thing, [pause] report the grade of what you serve, not just whether you served it.

[Point to the line under the rules.] Our key rates are parameters and our graphs are synthetic, so cross-validation is next.

[Point to the Thank you panel.] Thank you. I'm happy to take questions.

---

## Backup answers for likely questions

**1. "Your graphs are synthetic and the key rates are parameters. Why should we believe this transfers?"**
You are right to ask. We do not claim these exact numbers describe a deployed network. What carries over is the structure. On all five graphs a held cut forces eighty-eight to ninety-three percent, and fail-closed service follows stock divided by demand. We swept the fill, load and attack costs, and cross-validation with a published simulator is our next step.

**2. "Two of your validation checks failed. Doesn't that undermine the model?"**
Both missed in the same direction. Real systems spend more key on authentication overhead than our lowest assumption of two messages per delivery. So we solved for the count, about seven per hop, and used seven by default, testing two and forty as well. The headline loss only moves between about eighty-eight and ninety-four percent. We reported the mismatch rather than hiding it.

**3. "Doesn't the learned controller solve the problem?"**
Not in our audit. On held-out seeds the best learner gains about one part in a thousand in score, and a simple heuristic reaches ninety-nine point eight percent of that. It also lowers compliant surveillance service by about two point eight points and raises payload-weighted forced loss by about one point seven. Our lesson is that floors must be priced per class.

---

## Pacing tips

- Aim for about 130 to 140 words per minute. If you reach slide 6 after 5 minutes 30 seconds, you are on schedule.
- Slide 6 is the anchor. Never shorten it. If you need time, trim slides 3 and 7 first, by skipping the list of five contributions and the sentence about routing, floors and the controller.
- Pause for two full seconds after "It hides the loss." That sentence is the takeaway.
- Say "T-star" as two words, and say "bits per second", not "bit/s".
- Do not read numbers off the slide. Say each one once, then point at it.
- Move your hand to the next thing on the slide before you start talking about it, so the audience looks where you look.
- If a question needs more than a minute, offer to continue after the session. Keep Q and A to the backup answers above.
- Finish the transition sentence at the end of each slide before you click. The audience then hears the next idea as the slide changes.
