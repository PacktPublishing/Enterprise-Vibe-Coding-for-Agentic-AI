# Before You Start

Use this guide before opening the chapter assets. It explains the eight-chapter learning path, the repository conventions, and the difference between self-contained playbooks, repo-native primitives, and runnable prototypes.

➡️ **[Launch the Before You Start interactive guide](https://valentina-alto.github.io/Enterprise-Vibe-Coding-for-Agentic-AI/before%20you%20start/before-you-start.html)**

## Recommended Path

1. Open the interactive guide and scan the eight chapter outcomes.
2. Read a chapter, then open its `chapterN/README.md`.
3. Launch `chapterN-landing.html` to review the concepts interactively.
4. Inspect the linked primitives or prototype folders.
5. Begin with Chapter 1 if you want the full operating model; jump to Chapters 3–7 if you are applying the practices to an existing repository.

## Asset Types

| Asset | What it is | How to use it |
|---|---|---|
| `chapterN-landing.html` | Self-contained interactive playbook | Open locally or through GitHub Pages |
| `chapterN/README.md` | Chapter-specific asset index | Start here after reading the chapter |
| `.github/` | Instructions, prompts, agents, skills, hooks, workflows | Review and adapt inside a repository |
| `.vscode/mcp.json` | Example tool and data connector configuration | Treat as a least-privilege template |
| Chapter 6 application folders | Runnable Python prototypes | Follow each folder's requirements and supply local credentials |

## Important Notes

- GitHub Pages serves static HTML, CSS, JavaScript, images, and video; it does not run the Chapter 6 Flask applications.
- Hidden folders such as `.github/` and `.vscode/` contain important assets even when a file explorer does not show them by default.
- Never reuse example credentials. Keep real secrets outside version control.
- Paths containing spaces are valid; quote them in terminal commands and URL-encode them as `%20` in links.
