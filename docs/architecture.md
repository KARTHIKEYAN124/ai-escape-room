# Version 1 — model-managed game

![Version 1 architecture](architecture-v1.svg)

```mermaid
flowchart LR
    Player --> UI[Streamlit chat]
    UI --> History[Session conversation]
    History --> GM[Gemini Game Master]
    Room[Room prompt and solutions] --> GM
    GM --> Reply[Narrative and escape marker]
    Reply --> UI
    Reply --> History
```

The complete conversation is resent each turn. A model-generated escape marker controls completion. The room rules are instructions, not enforced constraints.

# Version 2 — validated game

![Version 2 architecture](architecture-v2.svg)

```mermaid
flowchart LR
    Player --> UI[Streamlit chat]
    UI --> Parser[Gemini action interpreter]
    Parser --> Check[JSON and explicit-code checks]
    Check --> Engine[Python action validation]
    Rules[Private puzzle rules] --> Engine
    State[Session State dataclass] <--> Engine
    Engine --> Outcome[Approved outcome descriptions]
    Outcome --> Narrator[Gemini selects approved phrasing]
    Narrator --> Guard[Validate selection or use canonical text]
    Guard --> UI
    UI --> History[Conversation log]
```

The action interpreter receives only the current message and an action schema. It has no private room solution configuration or state, although player messages can contain guesses or discovered clues. Python ignores any unrecognized fields and does not accept state updates. Narration receives only the already-approved outcome. API/JSON failures in Version 2 fall back to the offline parser or canonical narration with a visible warning. Generation retries transient server errors once. Version 1 can discover and retry a replacement model on 404; if recovery fails, the turn remains unsubmitted.
