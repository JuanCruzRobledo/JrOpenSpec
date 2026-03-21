# Skill Registry — integrador

Generated: 2026-03-20
Project: integrador (restaurant management monorepo)

## User-Level Skills (`~/.claude/skills/`)

| Skill | Path | Trigger |
|-------|------|---------|
| sdd-apply | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-apply\SKILL.md` | Apply SDD tasks, implement changes |
| sdd-archive | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-archive\SKILL.md` | Archive completed changes |
| sdd-design | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-design\SKILL.md` | Design phase, sequence diagrams |
| sdd-explore | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-explore\SKILL.md` | Explore codebase for a change |
| sdd-init | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-init\SKILL.md` | Initialize SDD in a project |
| sdd-propose | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-propose\SKILL.md` | Propose a change |
| sdd-spec | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-spec\SKILL.md` | Write specifications |
| sdd-tasks | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-tasks\SKILL.md` | Break down tasks |
| sdd-verify | `C:\Users\Juan Cruz Robledo\.claude\skills\sdd-verify\SKILL.md` | Verify implementation |
| go-testing | `C:\Users\Juan Cruz Robledo\.claude\skills\go-testing\SKILL.md` | Go tests, Bubbletea TUI testing |
| skill-creator | `C:\Users\Juan Cruz Robledo\.claude\skills\skill-creator\SKILL.md` | Creating new AI skills |

## Project-Level Convention Files

| File | Path | Purpose |
|------|------|---------|
| CLAUDE.md (root) | `E:\ESCRITORIO\programar\2026\JrOpenSpec\CLAUDE.md` | Root project conventions, SDD navigation, patterns |
| CLAUDE.md (Dashboard) | `E:\ESCRITORIO\programar\2026\JrOpenSpec\Dashboard\CLAUDE.md` | Dashboard-specific patterns (to be created in phase 10) |
| CLAUDE.md (pwaMenu) | `E:\ESCRITORIO\programar\2026\JrOpenSpec\pwaMenu\CLAUDE.md` | pwaMenu patterns (to be created in phase 9) |
| CLAUDE.md (pwaWaiter) | `E:\ESCRITORIO\programar\2026\JrOpenSpec\pwaWaiter\CLAUDE.md` | pwaWaiter patterns (to be created in phase 8) |

## SDD Shared Conventions (`~/.claude/skills/_shared/`)

| File | Path |
|------|------|
| openspec-convention.md | `C:\Users\Juan Cruz Robledo\.claude\skills\_shared\openspec-convention.md` |
| engram-convention.md | `C:\Users\Juan Cruz Robledo\.claude\skills\_shared\engram-convention.md` (if exists) |

## Project-Level Skills (`.agent/skills/`)

| Skill | Trigger |
|-------|---------|
| `dashboard-crud-page` | Creating any CRUD page in Dashboard |
| `zustand-store-pattern` | Creating or modifying any Zustand store |
| `react19-form-pattern` | Creating forms in any frontend |
| `fastapi-domain-service` | Creating a new backend domain service or endpoint |
| `help-system-content` | Adding HelpButton to any Dashboard component |
| `ws-frontend-subscription` | Connecting a React component to WebSocket events |

## Notes

- SDD skills (sdd-*) are excluded from selection per registry rules
- Persistence mode: `openspec` (file-based at `openspec/`)
- Sub-project CLAUDE.md files will be created as each frontend phase is implemented
