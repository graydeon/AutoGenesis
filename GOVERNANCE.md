# Governance

## Current Model: BDFL

AutoGenesis is currently maintained under a Benevolent Dictator For Life (BDFL) model with a documented path toward a governance council as the project matures.

## Decision-Making

- **Architectural changes:** Require an RFC (Request for Comments) posted as a GitHub Discussion
- **Feature proposals:** GitHub Discussions for community input
- **Bug fixes and small improvements:** Standard PR review process

## Roles

### BDFL
Final decision authority on architectural direction and releases.

### Ethics/Safety Advisory
Owns the self-improvement guardrails and constitutional safety layer. Has veto power over changes to `prompts/system/constitution.yaml` and the security package.

### Maintainer
Can merge PRs, triage issues, and cut releases. Graduation path:
1. **Contributor:** 1+ merged PR
2. **Reviewer:** 3+ merged PRs, demonstrates understanding of codebase
3. **Maintainer:** Consistent contributions, nominated by existing maintainer

## Future

As the community grows, the project will transition to a council-based governance model with elected representatives from major contributor groups.
