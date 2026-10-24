# FutureShield AI — SafeHer Guardian

A modular, safety-first AI agent built with **Fetch.ai uAgents** and the official **Agent Chat Protocol**, designed for seamless integration with **Agentverse** and **ASI:One**.

---

## 🛡️ Project Overview

**SafeHer Guardian** is an autonomous safety assistant engineered with deterministic Python safeguards and explainable natural language synthesis. 

### Core Capabilities
| # | Capability | Deterministic Enforcement |
|---|-----------|---------------------------|
| 1 | **Safety-First Navigation** | Alternative route scoring based on verified hazards; never invents live routes or travel times. |
| 2 | **Safety Evidence Analysis** | Assesses confidence and flags missing attributes; **never equates missing data with safety**. |
| 3 | **Safe Haven Discovery** | Discovers candidate hospitals, pharmacies, police stations, and petrol stations with explicit unverified hours caveats. |
| 4 | **Guardian Mode** | Enforces explicit consent checks, session lifecycles, and distinguishes simulated vs confirmed notifications. |
| 5 | **Emergency Assistance** | Deterministic access guidance for India's **112** unified emergency response with incident audit logging; never falsely claims police dispatch. |
| 6 | **Intelligent Rerouting** | Evaluates incoming hazard reports against credibility, freshness (<120 min), and relevance before rerouting. |
| 7 | **Privacy & Audit** | Time-limited location shares with auto-expiry, distance coarsening (data minimisation), and pseudonymised audit trails. |

---

## 🏛️ System Architecture

```
Ai agent/
├── agent.py               ← uAgent entry point with AgentChatProtocol:0.3.0 handlers
├── coordinator.py         ← Central intent parser, capability dispatcher, and LLM explainer
├── config.py              ← Environment-driven settings with structured startup logging
├── .env.example           ← Environment variable template (no hardcoded secrets)
├── .gitignore             ← Ignores secrets, logs, virtual environments, and caches
├── requirements.txt       ← Pinned dependencies compatible with Python 3.11+
├── capabilities/
│   ├── navigation.py      ← Capability 1: Route comparison & safety scoring
│   ├── safety_analysis.py ← Capability 2: Evidence scoring & missing data detection
│   ├── safe_haven.py      ← Capability 3: POI / refuge discovery with caveats
│   ├── guardian.py        ← Capability 4: Guardian sessions & consent enforcement
│   ├── emergency.py       ← Capability 5: Deterministic 112 guidance & incident logging
│   ├── rerouting.py       ← Capability 6: Hazard credibility verification & rerouting
│   └── privacy.py         ← Capability 7: Expiring shares, coordinate coarsening, audit logs
├── integrations/
│   └── llm.py             ← ASI:One / OpenAI-compatible client for NL explanations only
├── models/
│   ├── safety.py          ← Pydantic models for locations, routes, and hazards
│   ├── guardian.py        ← Pydantic models for sessions, consent, and notifications
│   ├── emergency.py       ← Pydantic models for emergency dispatch and incidents
│   └── privacy.py         ← Pydantic models for permission levels and audit records
└── tests/
    ├── conftest.py        ← Pytest fixtures
    ├── test_agent_chat.py ← Tests for Chat Protocol message & acknowledgment handling
    ├── test_coordinator.py← Integration tests for coordinator routing
    ├── test_navigation.py ← Tests for route options and safety ordering
    ├── test_safety_analysis.py ← Tests for missing data flagging and confidence
    ├── test_safe_haven.py ← Tests for safe haven caveats and filters
    ├── test_guardian.py   ← Tests for session lifecycles and consent validation
    ├── test_emergency.py  ← Tests for 112 response and dispatch status
    ├── test_rerouting.py  ← Tests for hazard validation and rerouting
    └── test_privacy.py    ← Tests for permission coarsening and audit logs
```

### Architectural Principles
1. **Deterministic Authority**: All safety scores, consent validations, coordinate coarsening, and emergency guidance are executed by deterministic Python logic.
2. **LLM as Explainer Only**: The ASI:One LLM (`asi1-mini` or compatible) is utilized exclusively for parsing user intent and generating empathetic explanations. If the LLM is unreachable or unconfigured, clean deterministic fallback explanations are returned.
3. **Transparent Truth in Safety**: Static test fixtures are clearly annotated (`[FIXTURE DATA]`), missing data is explicitly called out, and simulated notifications are labelled with `status="simulated"`.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11 or higher (tested on Python 3.11.9 and 3.13.5).
- A virtual environment or Anaconda environment.

### 2. Installation
Navigate to the project root directory:
```powershell
cd "c:\Documents\Desktop\Ai agent"
```

Install dependencies:
```powershell
pip install -r requirements.txt
```

### 3. Configuration
Copy the template to create your `.env` file:
```powershell
Copy-Item .env.example .env
```

Open `.env` in an editor and configure your environment variables:
```ini
# Identity seed (deterministic agent address)
AGENT_SEED="your-unique-seed-phrase-keep-this-private"

# Local listening port
AGENT_PORT=8000

# Optional: Agentverse API key (for Agentverse Mailbox connectivity)
AGENTVERSE_API_KEY=""

# Optional: ASI:One LLM API key (for natural language explanation)
ASI1_API_KEY=""
ASI1_BASE_URL="https://api.asi1.ai/v1"
ASI1_MODEL="asi1-mini"

# Safety & Privacy Defaults
LOCATION_SHARE_TTL_SECONDS=3600
ROUTING_PROVIDER="fixture"
POI_PROVIDER="fixture"
```

---

## 🧪 Testing and Verification

Run the comprehensive automated test suite (50 unit and integration tests):

```powershell
python -m pytest tests/ -v
```

### Test Coverage Highlights:
- **`test_agent_chat.py`**: Verifies that incoming `ChatMessage` triggers immediate `ChatAcknowledgement` with the correct `msg_id`, followed by a structured response wrapping `TextContent`.
- **`test_coordinator.py`**: Verifies fallback handling, keyword intent detection, and coordinator safety guarantees.
- **`test_navigation.py`**: Validates safety score descending order, fixture disclaimer tags, and absence of invented travel times.
- **`test_safety_analysis.py`**: Asserts missing data points are surfaced as risk factors and scores stay bounded in $[0.0, 10.0]$.
- **`test_guardian.py`**: Validates consent requirement before sending notifications, and ensures simulated notifications are marked as such.
- **`test_emergency.py`**: Guarantees `DispatchStatus` is `NOT_ATTEMPTED` and emergency guidance prioritizes India's unified **112**.
- **`test_privacy.py`**: Tests coordinate coarsening (None $\to$ ~5km $\to$ ~500m $\to$ exact) and non-reversible pseudonymised audit trails.

---

## 🏃 Running the Agent

Start the agent locally:
```powershell
python agent.py
```

Upon launching, the agent logs:
```text
=== SafeHer Guardian — Configuration Summary ===
  AGENT_NAME     : safeher_guardian
  AGENT_PORT     : 8000
  MAILBOX_ENABLED: False
  LLM_AVAILABLE  : False  (model=asi1-mini)
  ROUTING        : fixture
  POI            : fixture
  TRUSTED_CONTACTS: 0 configured
  AUDIT_LOG      : logs\audit.jsonl
=================================================
INFO: [safeher_guardian]: Starting agent with address: agent1qtemnxvnvc8yyt3nl6r0j9p6e4hekzp3a969k7xdhq9w3dzhd7jax5qysq2
INFO: [safeher_guardian]: Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1q...
```

---

## 🌐 Agentverse Onboarding & Public Reachability

### Understanding Local Execution vs Public Reachability
> ⚠️ **Important Reality Check**: Running `python agent.py` locally binds the agent to `127.0.0.1:8000`. By itself, **local execution does not make the agent accessible from the public internet or discoverable on Agentverse/ASI:One**.

To connect the local agent to Agentverse and make it discoverable by ASI:One, choose one of the two supported onboarding workflows:

### Option A: Agentverse Mailbox (Recommended for Local Development)
Agentverse Mailbox acts as a cloud message queue. When connected, Agentverse holds incoming messages and streams them over a secure outbound connection to your local machine, requiring **no port forwarding or public IP**.

1. Log in to [Agentverse.ai](https://agentverse.ai).
2. Go to your **Profile** (top right) $\to$ **API Keys** $\to$ **+ New API Key**.
3. Copy the key and add it to your `.env`:
   ```ini
   AGENTVERSE_API_KEY="av_your_api_key_here"
   ```
4. Restart `python agent.py`.
5. SafeHer Guardian detects the key and enables Mailbox mode (`mailbox=True`). Agentverse establishes the mailbox channel and registers the agent's protocol manifest on Almanac.

### Option B: Agent Inspector Linking
If connecting interactively:
1. Start the agent without Mailbox configured.
2. Copy the **Agent Inspector URL** printed in the terminal logs:
   `https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8000&address=agent1q...`
3. Open it in a browser on the same machine.
4. Click **Connect** and select **Mailbox** to provision a mailbox credential for the agent.

### Option C: Public Reverse Proxy / Endpoint Configuration
If hosting on custom cloud infrastructure or using a tunneling service (e.g., Cloudflare Tunnel):
1. Expose the HTTP port `8000` via a public HTTPS URL.
2. Configure the `endpoint` argument in `agent.py`:
   ```python
   agent = Agent(
       name=config.AGENT_NAME,
       seed=config.AGENT_SEED,
       port=config.AGENT_PORT,
       endpoint=["https://guardian.yourdomain.com/submit"]
   )
   ```
3. When started, the agent publishes this public endpoint to the Almanac contract.

---

## 💬 Interacting with the Agent via Agent Chat Protocol

Once linked to Agentverse, the agent responds to the official Agent Chat Protocol (`AgentChatProtocol:0.3.0`, digest `proto:30a801ed3a83...`):

1. **User sends `ChatMessage`** with `TextContent`.
2. **SafeHer Guardian sends `ChatAcknowledgement`** to confirm packet receipt.
3. **Coordinator parses intent**:
   - Navigation: `"What is the safest route to Central Station?"`
   - Safe Haven: `"Find a 24/7 pharmacy near me"`
   - Emergency: `"Help, someone is following me!"`
   - Evidence Analysis: `"Is it safe to walk through Sector 4 right now?"`
4. **Coordinator executes deterministic safety checks** and generates a structured response.
5. **Agent replies with `ChatMessage`** wrapping the advice and applicable caveats.
