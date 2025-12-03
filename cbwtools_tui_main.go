// main.go - cbwtools TUI front-end
// =============================================================================
// Project       : cbwtools TUI
// Author        : cbwinslow (co-piloted by GPT-5.1 Thinking)
// Created       : 2025-11-19
// Summary       : Bubble Tea-based terminal UI for interacting with cbwtools.
//                 Uses the existing Python cbwtools CLI as a backend, calling
//                 it via os/exec to list and operate on secrets, bundles,
//                 shortcuts, repo aliases, folder aliases, and scripts.
//
// Inputs        : None directly; relies on environment variables.
//                 - CBWTOOLS_BIN (optional): path to cbwtools executable
//
// Outputs       : Terminal UI, stdout/stderr messages.
//
// Dependencies  :
//   Go modules:
//     - github.com/charmbracelet/bubbletea
//     - github.com/charmbracelet/bubbles/list
//     - github.com/charmbracelet/lipgloss
//
// Usage         :
//   go mod init github.com/youruser/cbwtools-tui
//   go get github.com/charmbracelet/bubbletea@latest
//   go get github.com/charmbracelet/bubbles@latest
//   go get github.com/charmbracelet/lipgloss@latest
//   go build -o cbwtools-tui
//   ./cbwtools-tui
//
// Notes         :
//   - This is a v1; it parses the text output from cbwtools list commands.
//     Later you can extend cbwtools to provide JSON output and switch this
//     UI to parse JSON instead.
//   - All actions are performed by invoking cbwtools; no secrets are stored
//     directly in this Go binary.
// =============================================================================

package main

import (
    "context"
    "fmt"
    "os"
    "os/exec"
    "strings"
    "time"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/lipgloss"
)

// -----------------------------------------------------------------------------
// Types & Enums
// -----------------------------------------------------------------------------

type section int

const (
    sectionSecrets section = iota
    sectionBundles
    sectionShortcuts
    sectionRepos
    sectionFolders
    sectionScripts
    sectionCount
)

func (s section) String() string {
    switch s {
    case sectionSecrets:
        return "Secrets"
    case sectionBundles:
        return "Bundles"
    case sectionShortcuts:
        return "Shortcuts"
    case sectionRepos:
        return "Repos"
    case sectionFolders:
        return "Folders"
    case sectionScripts:
        return "Scripts"
    default:
        return "Unknown"
    }
}

type entryType int

const (
    entrySecret entryType = iota
    entryBundle
    entryShortcut
    entryRepo
    entryFolder
    entryScript
)

// listItem implements list.Item from Bubbles.

type listItem struct {
    title string
    desc  string
    kind  entryType
}

func (i listItem) Title() string       { return i.title }
func (i listItem) Description() string { return i.desc }
func (i listItem) FilterValue() string { return i.title }

// Messages

type errMsg struct{ err error }

func (e errMsg) Error() string { return e.err.Error() }

type loadedItemsMsg struct {
    section section
    items   []list.Item
}

// -----------------------------------------------------------------------------
// Model
// -----------------------------------------------------------------------------

type model struct {
    section section
    list    list.Model

    status  string
    loading bool
    width   int
    height  int
}

// -----------------------------------------------------------------------------
// Styling
// -----------------------------------------------------------------------------

var (
    titleStyle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205"))
    statusStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
    activeTab    = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("86"))
    inactiveTab  = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
    borderStyle  = lipgloss.NewStyle().Border(lipgloss.NormalBorder()).Padding(0, 1)
    helpStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))
)

// -----------------------------------------------------------------------------
// Backend helpers: calling cbwtools
// -----------------------------------------------------------------------------

func cbwtoolsBin() string {
    if v := os.Getenv("CBWTOOLS_BIN"); v != "" {
        return v
    }
    // Assumes cbwtools is on PATH; you can also point this to cbwtools.py
    return "cbwtools"
}

// runCbwtools runs cbwtools with the given args and returns stdout as string.
// It uses a context with a reasonable timeout to avoid hanging the UI.

func runCbwtools(args ...string) (string, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    cmd := exec.CommandContext(ctx, cbwtoolsBin(), args...)
    cmd.Env = os.Environ()
    out, err := cmd.CombinedOutput()
    if ctx.Err() == context.DeadlineExceeded {
        return "", fmt.Errorf("cbwtools timeout")
    }
    if err != nil {
        return "", fmt.Errorf("cbwtools error: %w: %s", err, strings.TrimSpace(string(out)))
    }
    return string(out), nil
}

// parseName extracts the logical name from a list line.
// Examples:
//   "  - openai/api_key (created: 2025...)"         -> "openai/api_key"
//   "  - install/dev-env: scripts/path (lang=...)" -> "install/dev-env"
//   "  - opendiscourse: https://..."               -> "opendiscourse"

func parseName(line string) string {
    line = strings.TrimSpace(line)
    if !strings.HasPrefix(line, "- ") {
        return ""
    }
    line = strings.TrimPrefix(line, "- ")

    // Prefer colon delimiter
    if idx := strings.Index(line, ":"); idx != -1 {
        return strings.TrimSpace(line[:idx])
    }
    // Fallback: stop at first " ("
    if idx := strings.Index(line, " ("); idx != -1 {
        return strings.TrimSpace(line[:idx])
    }
    return strings.TrimSpace(line)
}

// fetchSectionItems uses cbwtools list-* commands to build list items.

func fetchSectionItems(s section) ([]list.Item, error) {
    var (
        out string
        err error
    )

    switch s {
    case sectionSecrets:
        out, err = runCbwtools("list-secrets")
    case sectionBundles:
        // There is no explicit list-bundles command yet; we can approximate by
        // calling show-config in a later version. For now, show placeholder.
        return []list.Item{listItem{title: "(no explicit bundles list yet)", desc: "Use cbwtools save-folder-bundle from CLI.", kind: entryBundle}}, nil
    case sectionShortcuts:
        out, err = runCbwtools("list-shortcuts")
    case sectionRepos:
        out, err = runCbwtools("list-repo-aliases")
    case sectionFolders:
        out, err = runCbwtools("list-folder-aliases")
    case sectionScripts:
        out, err = runCbwtools("list-scripts")
    default:
        return nil, fmt.Errorf("unknown section")
    }

    if err != nil {
        return nil, err
    }

    var items []list.Item
    lines := strings.Split(out, "\n")
    for _, line := range lines {
        if strings.HasPrefix(strings.TrimSpace(line), "- ") {
            name := parseName(line)
            if name == "" {
                continue
            }
            li := listItem{title: name, desc: strings.TrimSpace(line), kind: entryFromSection(s)}
            items = append(items, li)
        }
    }

    if len(items) == 0 {
        items = append(items, listItem{title: "(none)", desc: "No items found in this section.", kind: entryFromSection(s)})
    }

    return items, nil
}

func entryFromSection(s section) entryType {
    switch s {
    case sectionSecrets:
        return entrySecret
    case sectionBundles:
        return entryBundle
    case sectionShortcuts:
        return entryShortcut
    case sectionRepos:
        return entryRepo
    case sectionFolders:
        return entryFolder
    case sectionScripts:
        return entryScript
    default:
        return entrySecret
    }
}

// -----------------------------------------------------------------------------
// Bubble Tea init/update/view
// -----------------------------------------------------------------------------

func initialModel() model {
    const defaultWidth = 80
    const defaultHeight = 24

    l := list.New([]list.Item{}, list.NewDefaultDelegate(), defaultWidth-4, defaultHeight-5)
    l.Title = "cbwtools"
    l.SetShowStatusBar(false)
    l.SetFilteringEnabled(true)

    m := model{
        section: sectionSecrets,
        list:    l,
        status:  "Loading secrets from cbwtools...",
        loading: true,
        width:   defaultWidth,
        height:  defaultHeight,
    }

    return m
}

func (m model) Init() tea.Cmd {
    return loadSectionCmd(m.section)
}

func loadSectionCmd(s section) tea.Cmd {
    return func() tea.Msg {
        items, err := fetchSectionItems(s)
        if err != nil {
            return errMsg{err}
        }
        return loadedItemsMsg{section: s, items: items}
    }
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    var cmds []tea.Cmd

    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c", "q":
            return m, tea.Quit
        case "tab":
            m.section = (m.section + 1) % sectionCount
            m.status = fmt.Sprintf("Switched to %s", m.section)
            m.loading = true
            return m, loadSectionCmd(m.section)
        case "shift+tab":
            if m.section == 0 {
                m.section = sectionCount - 1
            } else {
                m.section--
            }
            m.status = fmt.Sprintf("Switched to %s", m.section)
            m.loading = true
            return m, loadSectionCmd(m.section)
        case "r":
            // Reload current section
            m.status = fmt.Sprintf("Reloading %s...", m.section)
            m.loading = true
            return m, loadSectionCmd(m.section)
        case "enter":
            // Perform default action based on entry type
            if sel, ok := m.list.SelectedItem().(listItem); ok {
                return m.handleEnter(sel)
            }
        }

    case tea.WindowSizeMsg:
        m.width = msg.Width
        m.height = msg.Height
        m.list.SetSize(msg.Width-4, msg.Height-5)

    case loadedItemsMsg:
        if msg.section == m.section {
            m.list.SetItems(msg.items)
            m.loading = false
            m.status = fmt.Sprintf("Loaded %d items from %s", len(msg.items), m.section)
        }

    case errMsg:
        m.status = fmt.Sprintf("Error: %v", msg.err)
        m.loading = false
    }

    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    cmds = append(cmds, cmd)

    return m, tea.Batch(cmds...)
}

func (m model) handleEnter(it listItem) (tea.Model, tea.Cmd) {
    name := it.title

    switch it.kind {
    case entrySecret:
        // Show secret value using cbwtools get-secret --raw
        go func() {
            out, err := runCbwtools("get-secret", name, "--raw")
            if err != nil {
                fmt.Fprintf(os.Stderr, "get-secret error: %v\n", err)
                return
            }
            fmt.Printf("\n%s = %s\n", name, strings.TrimSpace(out))
        }()
        m.status = fmt.Sprintf("Fetched secret '%s' (printed to stdout).", name)

    case entryShortcut:
        go func() {
            fmt.Printf("\nRunning shortcut '%s'...\n", name)
            _, err := runCbwtools("run-shortcut", name, "--yes")
            if err != nil {
                fmt.Fprintf(os.Stderr, "run-shortcut error: %v\n", err)
            }
        }()
        m.status = fmt.Sprintf("Triggered shortcut '%s' via cbwtools.", name)

    case entryScript:
        go func() {
            fmt.Printf("\nRunning script '%s'...\n", name)
            _, err := runCbwtools("run-script", name, "--yes")
            if err != nil {
                fmt.Fprintf(os.Stderr, "run-script error: %v\n", err)
            }
        }()
        m.status = fmt.Sprintf("Triggered script '%s' via cbwtools.", name)

    case entryRepo:
        // For repos, default action: clone-repo-alias into cwd/<name>
        go func() {
            fmt.Printf("\nCloning repo alias '%s'...\n", name)
            _, err := runCbwtools("clone-repo-alias", name)
            if err != nil {
                fmt.Fprintf(os.Stderr, "clone-repo-alias error: %v\n", err)
            }
        }()
        m.status = fmt.Sprintf("Triggered clone for repo alias '%s'.", name)

    case entryFolder:
        // For folders, just print path line to stdout
        fmt.Printf("\nFolder alias '%s' selected (see cbwtools list-folder-aliases for path).\n", name)
        m.status = fmt.Sprintf("Selected folder alias '%s'.", name)

    case entryBundle:
        fmt.Printf("\nBundles currently require manual handling via cbwtools CLI.\n")
        m.status = "Bundle selected (no default action yet)."
    }

    return m, nil
}

// -----------------------------------------------------------------------------
// View
// -----------------------------------------------------------------------------

func (m model) View() string {
    if m.width == 0 || m.height == 0 {
        return "Loading..."
    }

    // Tabs
    var tabs []string
    for s := section(0); s < sectionCount; s++ {
        if s == m.section {
            tabs = append(tabs, activeTab.Render(s.String()))
        } else {
            tabs = append(tabs, inactiveTab.Render(s.String()))
        }
    }

    header := titleStyle.Render("cbwtools TUI") + "  " + strings.Join(tabs, " | ")

    content := m.list.View()

    help := helpStyle.Render("tab/shift+tab: switch section  •  r: reload  •  enter: action  •  q: quit")
    status := statusStyle.Render(m.status)

    joined := fmt.Sprintf("%s\n%s\n\n%s\n%s", header, borderStyle.Render(content), status, help)
    return joined
}

// -----------------------------------------------------------------------------
// Main
// -----------------------------------------------------------------------------

func main() {
    p := tea.NewProgram(initialModel(), tea.WithAltScreen())
    if _, err := p.Run(); err != nil {
        fmt.Fprintf(os.Stderr, "Error running program: %v\n", err)
        os.Exit(1)
    }
}
