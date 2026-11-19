# Lost in the Crowd: Research Proposal Background

Johan Fernandez · November 2026 · draft

## Summary and status

People lose each other in crowds, and crowds are exactly where phone networks fail. It happens at a stadium
letting out, a parade, a beach on a holiday weekend, an evacuation, or a power cut that takes the cell towers
with it. This project asks whether phones can carry each other's messages, without a network, well enough that
a short "I'm lost, I'm here" reaches the right few people in time.

The idea is store-carry-forward. A phone seals a short message for its group. Any phone running the same app,
including a stranger's, can hold the sealed message without being able to read it, and pass it on to phones it
meets. Each message carries an expiry time and a hop limit so it cannot spread forever.

I first built and used this idea in a group-finding app for large music festivals. A festival is a useful test
bed: it is a temporary city of tens of thousands of people with poor connectivity and a timetable that moves the
crowd. But the question is general, and this proposal is written that way.

**Status, stated plainly.** The relay is designed and partly built. I have no measured delivery rates, delivery
times or battery figures. The only results here come from a small synthetic simulation (see `SIMULATION.md`).
Everything about real-world performance is a question, not a finding.

**Why this belongs in urban data science.** Whether a message can cross a crowd depends on how people move,
where they gather and how often they meet. Those are the questions urban researchers ask about mobility, density
and access to help. A study at a large music festival with more than 130,000 participants over 8 days used
Bluetooth sensing to map how crowds move and cluster ([Larsen et al., 2013](https://arxiv.org/abs/1306.3133)).
This project asks whether that same movement can carry messages, and for whom it fails.

## 1. Background

**Delay-tolerant networking (DTN).** Internet protocols assume an end-to-end path exists when a message is sent.
Fall (2003) argued that many "challenged" networks never have such a path, and proposed an overlay where nodes
store messages, carry them and forward them when a contact appears
([Fall, 2003](https://researchr.org/publication/Fall03)). This became the IETF DTN architecture
([RFC 4838](https://www.rfc-editor.org/rfc/rfc4838)) and the Bundle Protocol, now version 7
([RFC 9171](https://www.rfc-editor.org/rfc/rfc9171)). This project uses the store-carry-forward idea, not the
Bundle Protocol itself.

**Opportunistic and epidemic routing.** Epidemic routing copies every message to every node met, trading
storage and bandwidth for the best chance of delivery
([Vahdat and Becker, 2000](https://cseweb.ucsd.edu/~vahdat/papers/epidemic.pdf)). Later schemes limit copies.
Spray and Wait hands out a fixed number of copies and then waits for direct delivery
([Spyropoulos et al., 2005](https://researchr.org/publication/SpyropoulosPR05)). PRoPHET forwards to nodes likely
to meet the destination, based on past encounters ([RFC 6693](https://www.rfc-editor.org/rfc/rfc6693)). BUBBLE Rap
uses social community structure
([Hui et al., 2008](https://www.cl.cam.ac.uk/research/srg/netos/papers/13_2008_MOBIHOC.pdf)). Traces of real people
carrying small radios showed that the time between two people's meetings has a heavy tail, which limits how fast
any forwarding scheme can deliver
([Chaintreau et al., 2006](https://www.cl.cam.ac.uk/research/srg/netos/papers/2006-chaintreau2006impact.pdf)).
The design here is closest to epidemic routing with limits. It deliberately does not keep encounter history,
because a record of who met whom is itself sensitive.

**Prior mobile mesh systems.** Each system below solves part of the problem. None combines small private groups,
untrusted stranger carriers and phones only.

| System | Radio | Who relays | Security as documented | How this design differs |
|---|---|---|---|---|
| [FireChat](https://en.wikipedia.org/wiki/FireChat) (Open Garden, 2014) | Bluetooth, peer-to-peer Wi-Fi | Any user | Its makers said it "was not meant for secure or private communications"; apps not updated since 2018 | Every message is sealed; carriers cannot read it |
| Bridgefy | Bluetooth mesh | Any user | Researchers showed tracking, impersonation, message reading and a network-wide denial of service ([Albrecht et al., 2021](https://ia.cr/2021/214)); after a switch to the Signal protocol, private messages could still be read ([Albrecht et al., 2022](https://www.usenix.org/conference/usenixsecurity22/presentation/albrecht)) | Group-only messages; a cautionary precedent for any security claim, including mine |
| [Briar](https://briarproject.org/news/2017-beta-released-security-audit/) | Bluetooth, Wi-Fi, Tor | The user's contacts | Audited by Cure53 in 2017 (13 tester-days), which found it offers "a good level of privacy and security" | Briar syncs between known contacts; this design asks strangers to carry |
| [Meshtastic](https://meshtastic.org/docs/overview/encryption) | LoRa radios (separate hardware) | Any node on the channel | Channel messages use AES-CTR with a shared key and, by default, no integrity check; packet headers are never encrypted | Phones only, no extra hardware |
| Apple Find My offline finding | Bluetooth Low Energy | Nearby Apple devices | Meets its privacy goals but two flaws allowed location correlation, partly fixed ([Heinrich et al., 2021](https://petsymposium.org/popets/2021/popets-2021-0045.php)) | Find My is one-way, through Apple's servers; this carries two-way group messages with no server |

I could not verify Bridgefy's current protocol after 2022 or Briar's current release, so the table describes them
as of the cited reports.

## 2. The design in general terms

- **Sealed messages.** Each message is encrypted for one small group with authenticated encryption. Carriers
  cannot read it or change it without the change being detected.
- **Expiry and hop limit.** Each message has a lifetime and a maximum number of hand-offs, so old or distant
  messages stop moving.
- **Bounded storage.** Each phone holds a limited number of other people's messages, and urgent ones ("I'm lost")
  are kept ahead of routine ones.
- **Consistent meeting points.** When phones receive different versions of a group's meeting point in different
  orders, they settle on the same one.
- **Phone to phone only.** Discovery and transfer use the phone's built-in short-range radios. No server or extra
  hardware is involved.

Exact parameters are left out of this public version. The simulation uses example values, chosen for the
simulation, not those of any shipped app.

## 3. Privacy questions

Encryption hides what a message says, but not everything around it. These are the questions any design like this
has to answer, and that I will measure rather than assume:

- **Metadata.** What can a carrier learn from a message's size, timing, priority or position in the chain? The
  first place and time a message appears points to where its sender was.
- **Tracking by broadcast.** Phones have to advertise themselves to be found. Any value that stays constant lets an
  observer follow a phone or a group. This has happened before: Bluetooth address randomization was defeated by
  other identifiers in the same advertisements
  ([Becker et al., 2019](https://petsymposium.org/popets/2019/popets-2019-0036.php)), and Apple's Continuity
  messages leaked device details and allowed tracking
  ([Martin et al., 2019](https://petsymposium.org/popets/2019/popets-2019-0057.php)).
- **Group keys without a network.** Forward-secret group protocols such as MLS
  ([RFC 9420](https://www.rfc-editor.org/rfc/rfc9420)) need key updates to reach every member. That is hard when
  the network is the very thing that is missing.
- **Abuse by carriers.** A carrier cannot check a sealed message, so it cannot tell real messages from junk. How
  far can a malicious app flood or crowd out real messages, and what limits help?

## 4. Open research questions

None of these has an answer yet. Each is phrased so that the evaluation in section 5 can answer it.

1. **Density and adoption.** How do delivery probability and delivery time change with crowd density and with the
   share of people running the app? I expect a threshold below which carriers rarely link a group's members and
   delivery collapses. Where that threshold sits for real crowd movement is the main question.
2. **How crowds move.** Most relay studies use random walking. Real crowds gather around attractions, exits and
   timetables, and mix only at certain times. How much does that change delivery, and can it be predicted?
3. **Who actually carries.** On iPhones, peer-to-peer frameworks generally work only while the app is on screen.
   An Apple engineer wrote in June 2026 that Apple's peer-to-peer framework "was never meant to be used in the
   background" ([Apple Developer Forums](https://developer.apple.com/forums/thread/836124)). The real carrier pool
   may be a small fraction of installs, and this may matter more than any routing choice.
4. **Session limits and battery.** Short-range sessions hold only a few peers at once, so in a dense crowd a phone
   must choose whom to connect to. Discovery also costs battery
   ([Apple Developer Forums](https://developer.apple.com/forums/thread/776069)), and nobody keeps an app open that
   empties their phone.
5. **Platform change.** Apple is moving developers from its older peer-to-peer framework to the Network framework
   ([Apple Developer Forums](https://developer.apple.com/forums/thread/776069)), and added a
   [Wi-Fi Aware framework](https://developer.apple.com/documentation/wifiaware) in iOS 26 that runs in the
   background only between paired devices. That could suit a group's own phones, but not strangers.
6. **Who is left out.** People without the app, with older phones or on a different platform can neither send nor
   carry. Who does this help, and who does it miss?

## 5. Proposed evaluation (plan; a first synthetic run exists)

**Simulation.** A small first simulation is in this folder (`SIMULATION.md`). The full study would use the ONE
simulator, built for evaluating DTN protocols
([Keränen et al., 2009](https://eudl.eu/doi/10.4108/icst.simutools2009.5674)), and compare three kinds of movement:

1. Random waypoint, as a simple reference known to be unrealistic for people.
2. SLAW, a model fitted to real human walking traces ([Lee et al., 2009](https://dblp.org/rec/conf/infocom/LeeHKRC09)).
3. A scheduled-crowd model: people move between attractions on a timetable, stay in dense clusters, and spread
   out between them. Local crowd motion could follow the social force model of pedestrian dynamics
   ([Helbing and Molnár, 1995](https://arxiv.org/abs/cond-mat/9805244)).

Settings to vary are crowd size, the share running the app, the share with it open, group size, session limits,
storage limits and radio range.

**Baselines.**

| Baseline | What it shows |
|---|---|
| Group members only, no strangers | Whether stranger carriers add anything |
| Epidemic, no limits | Best-case delivery at the highest cost |
| Spray and Wait with a fixed copy count | Whether a copy limit can match delivery at lower cost |
| The design with limits | The design under test |

**Metrics.** Share of messages delivered within 5, 15 and 60 minutes; delivery time (median and 90th percentile);
copies per delivered message; urgent messages separately; and privacy measures such as how often a carrier could
guess the sender.

**Field study.** Two to four iPhones carried by people I recruit, first in an open space and then in a busy public
place. It would measure contact setup time, data moved per contact, the distance at which contacts fail and
battery drain per hour. Four phones cannot test crowd-scale delivery; that comes only from simulation. Any study
with participants beyond myself would need ethics review first.

## 6. Spatial methods and GeoAI

See `SPATIAL_METHODS.md`. In short: the app already uses rule-based spatial methods (distance and direction to a
friend, places described in words, walk times). It has no trained model yet. The GeoAI questions are a lost
person's likely position, crowd density over time, and meeting-point suggestions.

## 7. Limitations

- **Not measured:** delivery rate, delivery time, battery cost, radio range in a crowd and how many strangers would
  carry messages.
- **Not reviewed:** the security design has not been reviewed by anyone else. Bridgefy shipped security claims that
  outside researchers broke twice, so I treat my own claims as unproven until reviewed.
- **iPhone only so far:** this shrinks the carrier pool and skews who benefits.
- **Simulation validity:** movement models are simplifications. A crowd model is only as good as the movement data
  behind it, and I have not yet secured real crowd movement data.
- **Scope:** results from 2–4 phones will show whether the mechanism works between phones, not in a crowd.

## 8. Possible supervisors and labs

Each person below was confirmed on an official or reliable page in November 2026. I did not check whether any of
them is taking new students. New York programs come first.

| Person | Where | Why relevant | Fit caveat |
|---|---|---|---|
| [Gil Zussman](https://engineering.columbia.edu/faculty/gil-zussman) | Columbia, Electrical Engineering (department chair) | Wireless, mobile and resilient networks; leads Columbia's part of the NSF COSMOS wireless testbed in West Harlem | Strongest New York fit for the networking side |
| [Henning Schulzrinne](https://www.engineering.columbia.edu/about/news/henning-schulzrinne-wins-ieee-infocom-achievement-award) | Columbia, Computer Science | Long record in internet protocols and emergency communication | Current focus listed as internet fault diagnosis, grid security and IoT, not DTN |
| [Shivendra Panwar](https://engineering.nyu.edu/faculty/shivendra-panwar) | NYU Tandon, Electrical and Computer Engineering | Wireless networks; current work includes cooperative wireless networks | Focus is cellular and Wi-Fi, not delay tolerance |
| [Yong Liu](https://engineering.nyu.edu/faculty/yong-liu) | NYU Tandon, Electrical and Computer Engineering | Design, analysis and simulation of networks; online social networks | Fits the simulation and modeling part |
| [Brian Levine](https://www.cics.umass.edu/about/directory/brian-levine) | UMass Amherst | Co-author of MaxProp and the DieselNet bus DTN testbed | Listed research area is now security and privacy |
| [Jörg Ott](https://www.ce.cit.tum.de/en/cm/research-group/joerg-ott/) | TU Munich, Chair of Connected Mobility | Co-chaired the IRTF DTN research group; co-author of the ONE simulator | Outside the US |
| [Jon Crowcroft](https://www.cl.cam.ac.uk/~jac22) | University of Cambridge | Co-author of pocket switched networks and BUBBLE Rap | Outside the US |
| [Matthias Hollick](https://www.seemoo.tu-darmstadt.de/) | TU Darmstadt, Secure Mobile Networking Lab | Wireless security and privacy; his lab analyzed Apple's offline finding | Outside the US |
| [Kenny Paterson](https://en.wikipedia.org/wiki/Kenny_Paterson) | ETH Zurich, Applied Cryptography Group | Co-author of the second Bridgefy break | Cryptography, not networking; outside the US |

## References

Each entry was found on the linked page in November 2026. Where I link to a course copy or index page rather than
the publisher, I could not confirm the publisher's DOI from here.

1. Albrecht, M. R., Blasco, J., Jensen, R. B., and Mareková, L. (2021). Mesh messaging in large-scale protests: Breaking Bridgefy. CT-RSA 2021. [ia.cr/2021/214](https://ia.cr/2021/214)
2. Albrecht, M. R., Eikenberg, R., and Paterson, K. G. (2022). Breaking Bridgefy, again: Adopting libsignal is not enough. USENIX Security 2022, 269–286. [usenix.org](https://www.usenix.org/conference/usenixsecurity22/presentation/albrecht)
3. Apple. Wi-Fi Aware framework (iOS 26). [developer.apple.com](https://developer.apple.com/documentation/wifiaware)
4. Apple Developer Forums (2025, revised 2026). Developer Technical Support thread on moving peer-to-peer apps to the Network framework. [Thread 776069](https://developer.apple.com/forums/thread/776069)
5. Apple Developer Forums (June 2026). Developer Technical Support reply on background peer-to-peer operation. [Thread 836124](https://developer.apple.com/forums/thread/836124)
6. Barnes, R., et al. (2023). The Messaging Layer Security (MLS) Protocol. RFC 9420. [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9420)
7. Becker, J. K., Li, D., and Starobinski, D. (2019). Tracking anonymized Bluetooth devices. PoPETs 2019(3). [petsymposium.org](https://petsymposium.org/popets/2019/popets-2019-0036.php)
8. Briar Project (2017). Beta released, security audit. [briarproject.org](https://briarproject.org/news/2017-beta-released-security-audit/)
9. Burleigh, S., Fall, K., and Birrane, E. (2022). Bundle Protocol Version 7. RFC 9171. [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9171)
10. Cerf, V., et al. (2007). Delay-Tolerant Networking Architecture. RFC 4838. [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc4838)
11. Chaintreau, A., Hui, P., Crowcroft, J., Diot, C., Gass, R., and Scott, J. (2006). Impact of human mobility on the design of opportunistic forwarding algorithms. IEEE INFOCOM 2006. [cl.cam.ac.uk](https://www.cl.cam.ac.uk/research/srg/netos/papers/2006-chaintreau2006impact.pdf)
12. Fall, K. (2003). A delay-tolerant network architecture for challenged internets. ACM SIGCOMM 2003. [researchr.org](https://researchr.org/publication/Fall03)
13. FireChat. Wikipedia entry, used for dates and status only. [wikipedia.org](https://en.wikipedia.org/wiki/FireChat)
14. Heinrich, A., Stute, M., Kornhuber, T., and Hollick, M. (2021). Who can find my devices? Security and privacy of Apple's crowd-sourced Bluetooth location tracking system. PoPETs 2021(3), 227–245. [petsymposium.org](https://petsymposium.org/popets/2021/popets-2021-0045.php)
15. Helbing, D., and Molnár, P. (1995). Social force model for pedestrian dynamics. Physical Review E 51, 4282. [arxiv.org](https://arxiv.org/abs/cond-mat/9805244)
16. Hui, P., Crowcroft, J., and Yoneki, E. (2008). BUBBLE Rap: Social-based forwarding in delay tolerant networks. ACM MobiHoc 2008. [cl.cam.ac.uk](https://www.cl.cam.ac.uk/research/srg/netos/papers/13_2008_MOBIHOC.pdf)
17. Keränen, A., Ott, J., and Kärkkäinen, T. (2009). The ONE simulator for DTN protocol evaluation. SIMUTools 2009. [eudl.eu](https://eudl.eu/doi/10.4108/icst.simutools2009.5674)
18. Larsen, J. E., Sapiezynski, P., Stopczynski, A., Moerup, M., and Theodorsen, R. (2013). Crowds, Bluetooth, and rock'n'roll: Understanding music festival participant behavior. [arXiv:1306.3133](https://arxiv.org/abs/1306.3133)
19. Lee, K., Hong, S., Kim, S. J., Rhee, I., and Chong, S. (2009). SLAW: A new mobility model for human walks. IEEE INFOCOM 2009. [dblp.org](https://dblp.org/rec/conf/infocom/LeeHKRC09)
20. Lindgren, A., Doria, A., Davies, E., and Grasic, S. (2012). Probabilistic Routing Protocol for Intermittently Connected Networks (PRoPHET). RFC 6693. [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc6693)
21. Martin, J., et al. (2019). Handoff all your privacy: A review of Apple's Bluetooth Low Energy Continuity protocol. PoPETs 2019(4). [petsymposium.org](https://petsymposium.org/popets/2019/popets-2019-0057.php)
22. Meshtastic. Encryption overview. [meshtastic.org](https://meshtastic.org/docs/overview/encryption)
23. Spyropoulos, T., Psounis, K., and Raghavendra, C. S. (2005). Spray and wait: An efficient routing scheme for intermittently connected mobile networks. ACM WDTN 2005. [researchr.org](https://researchr.org/publication/SpyropoulosPR05)
24. Vahdat, A., and Becker, D. (2000). Epidemic routing for partially connected ad hoc networks. Technical report, Duke University. [cseweb.ucsd.edu](https://cseweb.ucsd.edu/~vahdat/papers/epidemic.pdf)

**I could not verify** the author lists marked "et al." in full, the RFC author lists for 4838, 9171 and 9420, or
the PoPETs issue number for Martin et al.; check these on the linked pages before submitting.
