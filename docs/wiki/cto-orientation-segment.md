# CTO Orientation Segment

**Owner:** `cto`
**Audience:** AutoGenesis employees attending orientation
**Session slot:** `0:05–0:13` in [Onboarding Plan](onboarding-plan.md)
**Status:** Active
**Last updated:** 2026-03-19

This is the CTO's live orientation segment for aligning the team on company mission, product architecture, team interfaces, engineering standards, and near-term technical priorities. Use it with the [Welcome Packet](onboarding-packet.md), [Architecture](architecture.md), [Employee System](employee-system.md), and [Handoff](../../HANDOFF.md).

## Segment Objective

By the end of this segment, every employee should understand:

- what AutoGenesis is trying to prove,
- how the product is structured end to end,
- how teams hand work to one another,
- what good engineering looks like here,
- and what the current technical priorities are.

## 8-Minute Run of Show

| Time | Topic | Key message |
|---|---|---|
| 0:05–0:06 | Mission and company framing | We are building a reliable operating model for multi-agent execution, not just a chatbot wrapper. |
| 0:06–0:08 | Product architecture | The product works because orchestration, employee state, and specialized workflows are all explicit and inspectable. |
| 0:08–0:10 | Team interfaces | Handoffs succeed only when ownership, artifacts, and blockers are named. |
| 0:10–0:12 | Engineering standards | Prefer simple, tested, well-documented systems with clear approval boundaries. |
| 0:12–0:13 | Near-term priorities and close | Prove the core loop in production-like conditions before expanding surface area. |

## Mission and Company Framing

### What AutoGenesis exists to do

AutoGenesis turns high-level goals into completed work through a structured team of specialized employees powered by OpenAI Codex. Our job is to make that execution model reliable enough that a human can inspect it, steer it, trust it, and recover it when something fails.

### What makes the product different

- **Role-based execution instead of one giant agent.** Work is decomposed and assigned to named employees with specific tools and responsibilities.
- **Persistent operational memory.** Each employee keeps durable context in `brain.db` and can receive async handoffs through `inbox.db`.
- **Inspectable state.** Plans live in markdown, operational state lives in SQLite, and the docs describe the system plainly.
- **Human approval where risk is real.** Credentials stay on the host, public posting requires approval, and escalation is explicit.

### The operating principle

We optimize for **autonomous execution with human oversight**. That means we value speed, but not at the cost of explainability, safe defaults, or recoverability.

## Product Architecture

### Mental model in one sentence

A user gives AutoGenesis a goal through the CLI, the CEO decomposes and assigns it, employee runtimes execute the work with durable context, and the system records enough state for humans to inspect, resume, or intervene.

### Architecture layers

| Layer | Primary components | Why it exists |
|---|---|---|
| Control surface | `autogenesis` CLI, docs, config | Entry point for users and operators |
| Runtime core | `CodexClient`, `AgentLoop`, `SubAgentManager`, `AutoGenesisConfig`, `EventBus` | Executes model calls, tool loops, and subprocess dispatch |
| Coordination plane | `CEOOrchestrator`, `EmployeeRegistry`, `EmployeeRuntime`, `BrainManager`, `InboxManager`, `ChangelogManager`, `MeetingManager`, `UnionManager` | Breaks work apart, routes it, and preserves context across employees |
| Specialized workflow lane | Twitter browser/queue/gateway/scheduler stack | Proves the platform on a real autonomous workflow with human approval gates |
| Hardening and extension plane | `security`, `tokens`, `optimizer`, `mcp`, `plugins` packages | Gives us the path to stronger guardrails, efficiency, and integrations |

### Core execution path

1. A user starts from the CLI with a goal, task, meeting, or workflow command.
2. The CEO or runtime decides what work needs to happen next.
3. Employee context is assembled from memory, inbox, changelog, and task instructions.
4. A Codex-backed subprocess executes the assignment.
5. Results are written back to SQLite, markdown plans, and shared docs.
6. The system either continues, retries once, or escalates.

### Architecture decisions to reinforce in the orientation

- **SQLite + markdown over hidden state.** If the system matters, an operator should be able to inspect it.
- **Host-side secrets + scoped tokens.** Agents do not need raw credentials to do useful work.
- **Progressive tool disclosure.** We control context size and reduce accidental tool overexposure.
- **Explicit retries and escalation.** Failure handling is part of the design, not an afterthought.

## Team Interfaces

The product only works when handoffs are crisp. Every team interface needs a clear owner, a clear artifact, and a clear next step.

| Interface | Primary contract | Default artifact |
|---|---|---|
| Product Manager ↔ CTO | Turn scope and priorities into technical sequencing and tradeoffs | plan, acceptance criteria, architecture notes |
| CTO ↔ Backend / Frontend | Set boundaries, interfaces, and implementation shape | docs, API/schema notes, task breakdown |
| Engineering ↔ QA | Translate changes into verifiable behavior | tests, repro steps, validation notes |
| Engineering ↔ DevOps | Make software runnable, observable, and supportable | config changes, runbooks, health checks |
| Engineering ↔ Security | Preserve approval boundaries, secrets handling, and auth assumptions | security review notes, risk callouts |
| Engineering ↔ Technical Writer | Keep docs aligned with current behavior and operator needs | wiki updates, README/HANDOFF changes |
| Engineering ↔ Social / Product | Ensure external claims match actual shipped behavior | approved launch notes, capability summary |

### Standard handoff expectations

- Name the **owner** and the **next action**.
- State **what changed**, **where it changed**, and **how it was verified**.
- Surface blockers early instead of waiting for a perfect update.
- Record durable context in docs, changelog, or memory so the next employee can continue.

## Engineering Standards

### What good engineering means here

1. **Clarify before building.** Ask questions when requirements, risks, or constraints are ambiguous.
2. **Prefer the simplest design that survives reality.** Use straightforward systems before adding cleverness.
3. **Keep state inspectable.** Favor markdown, SQLite, and explicit configs over opaque behavior.
4. **Protect trust boundaries.** Secrets stay on the host, public actions require approval, and risky behavior must be obvious.
5. **Ship with verification.** Code changes should come with tests, reproducible commands, or documented validation.
6. **Document as part of the work.** If behavior, ownership, or workflow changed, the docs should change too.
7. **Escalate fast.** Do not hide failures; make retry, pause, and human intervention normal parts of execution.

### Definition-of-done checklist

A change is not done until it has:

- working code or workflow behavior,
- validation evidence,
- updated docs or operator notes when behavior changed,
- a named owner for any remaining blocker,
- and no violation of security or approval boundaries.

## Near-Term Technical Priorities

As of **March 19, 2026**, the near-term priorities are:

1. **Prove live Codex execution end to end.** The major remaining real-world gap in the handoff is validating the system with live ChatGPT Plus OAuth credentials rather than only local and mocked paths.
2. **Close remaining operational wiring gaps.** Finish the unresolved pieces called out in the implementation plan: gateway/scheduler wiring, standup and meeting orchestration, service registration, and dispatch-path polish.
3. **Harden the orchestration path.** Improve observability, resume behavior, and operator confidence around CEO dispatch, retries, and escalations.
4. **Wire the scaffolded platform modules in the right order.** Security, token controls, optimizer hooks, MCP, and plugins already exist as architecture lanes; the next step is disciplined integration, not speculative expansion.
5. **Maintain release discipline while narrowing scope.** Keep tests green, docs current, and avoid adding new surface area until the core loop is proven under realistic usage.

### What is intentionally not the priority

- Expanding breadth before the core loop is reliable
- Hiding complexity behind magic instead of documenting it
- Adding automation that weakens approval or security boundaries

## Closing Message for the Session

The key idea to leave with the team is simple: **AutoGenesis is a reliability project disguised as an agent product.** If we keep ownership explicit, state inspectable, docs current, and safety boundaries intact, the product can move fast without becoming fragile.

## Related Docs

- [Welcome Packet](onboarding-packet.md)
- [Onboarding Plan](onboarding-plan.md)
- [Architecture](architecture.md)
- [Employee System](employee-system.md)
- [CEO Orchestrator](ceo-orchestrator.md)
- [Twitter Agent](twitter-agent.md)
- [Handoff](../../HANDOFF.md)
