# Agency Check integration

Agency Check is a human decision interface built on the same evidence
discipline as AI SAFE2. It is not a software merge gate.

The service planned for `agency-check.app` should translate a bounded evidence
set into one Decision Card:

- `ready_to_review`;
- `clarify_one_thing`;
- `pause_and_verify`.

Every card should preserve:

- the person's stated goal;
- the proposed action;
- supported facts and their sources;
- unknown or conflicting information;
- material tradeoffs;
- one next step;
- what Agency Check did and did not examine;
- the human's retained authority.

It must not call an action safe, execute the action, or convert an absence of
evidence into approval.

Public reference: https://cyberstrategyinstitute.com/agency-check/

