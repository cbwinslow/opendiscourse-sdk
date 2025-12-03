// cbw_bubbletea_wish_tui_main.go
// Author: cbwinslow + ChatGPT (GPT-5.1 Thinking)
// Date: 2025-11-20
// Summary:
//   Starter TUI framework using Charmbracelet ecosystem:
//   - bubbletea (core TUI engine)
//   - bubbles (UI components)
//   - lipgloss (styling)
//   - wish (SSH-exposed TUI server)
//   - optional integration hooks for gum, glow, mods, skate CLIs
//
// Features:
//   - Local terminal TUI mode
//   - Optional SSH server mode via wish (--ssh-server flag)
//   - Menu-based UI with keyboard navigation
//   - Status/log panel for command output
//   - Safe shell-out wrappers for external CLIs (gum, glow, mods, skate)
//
// Inputs:
//   - Command line flags (basic, see main())
//
// Outputs:
//   - Text-mode UI in terminal or over SSH
//
// Notes:
//   - This is a starter skeleton: extend the menu items and handlers
//   - All external CLIs are optional; absence is handled gracefully
//
// Modification Log:
//   - 2025-11-20: Initial version generated.

package main

import (
    "context"
    "errors"
    "fmt"
    "log"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "time"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/bubbles/help"
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/bubbles/viewport"
    "github.com/charmbracelet/lipgloss"

    wish "github.com/charmbracelet/wish"
    wishtea "github.com/charmbracelet/wish/bubbletea"
    "github.com/charmbracelet/wish/logging"
    "github.com/charmbracelet/wish/middleware"
)

// -----------------------------
// Constants & Config
// -----------------------------

const (
    appName        = "CBW BubbleTea Suite"
    sshListenAddr  = "0.0.0.0:23234"          // Change as desired
    sshHostKeyPath = "./cbw_tui_ssh_ed25519" // Wish will create if missing
)

// menuItem represents a selectable menu entry in the main list.
type menuItem struct {
    title       string
    description string
    actionID    string
}

func (i menuItem) Title() string       { return i.title }
func (i menuItem) Description() string { return i.description }
func (i menuItem) FilterValue() string { return i.title }

// keyMap defines the key bindings we want to expose in the help view.
type keyMap struct{
    Quit     tea.KeyMap
    Confirm  tea.KeyMap
    UpDown   tea.KeyMap
}

// we keep it simple and use bubbles/help default bindings, but keep this
// struct for future extension.

// model is the Bubble Tea model for our TUI.
type model struct {
    list    list.Model
    help    help.Model
    keys    keyMap
    status  viewport.Model
    width   int
    height  int
    ready   bool
}

// messages for asynchronous command completion.
type cmdResultMsg struct {
    actionID string
    output   string
    err      error
}

// -----------------------------
// Styling with lipgloss
// -----------------------------

var (
    titleStyle = lipgloss.NewStyle().
            Bold(true).
            Foreground(lipgloss.Color("10")).
            Background(lipgloss.Color("0")).
            Padding(0, 1)

    statusTitleStyle = lipgloss.NewStyle().
                Bold(true).
                Foreground(lipgloss.Color("13")).
                Padding(0, 1)

    statusBoxStyle = lipgloss.NewStyle().
            Border(lipgloss.RoundedBorder()).
            BorderForeground(lipgloss.Color("8")).
            Padding(1, 1)

    appBorderStyle = lipgloss.NewStyle().
            Border(lipgloss.RoundedBorder()).
            BorderForeground(lipgloss.Color("2")).
            Padding(1, 2)
)

// -----------------------------
// Initial Model
// -----------------------------

func initialModel() model {
    items := []list.Item{
        menuItem{title: "SSH TUI server info", description: "Show how to run this app over SSH via wish", actionID: "ssh_info"},
        menuItem{title: "Run gum demo", description: "If installed, run a simple gum style demo", actionID: "gum_demo"},
        menuItem{title: "Open markdown with glow", description: "If glow is installed, show README.md", actionID: "glow_readme"},
        menuItem{title: "Mods prompt helper", description: "Shell out to mods if installed", actionID: "mods_prompt"},
        menuItem{title: "Skate KV check", description: "If skate is installed, show namespaces", actionID: "skate_namespaces"},
        menuItem{title: "About", description: "Details about this TUI skeleton", actionID: "about"},
    }

    l := list.New(items, list.NewDefaultDelegate(), 0, 0)
    l.Title = appName
    l.SetShowStatusBar(false)
    l.SetFilteringEnabled(true)
    l.SetShowHelp(false)

    h := help.New()

    vp := viewport.New(0, 0)
    vp.SetContent("Select an item and press Enter to run it.")

    km := keyMap{ }

    return model{
        list:   l,
        help:   h,
        keys:   km,
        status: vp,
    }
}

// -----------------------------
// Model methods
// -----------------------------

func (m model) Init() tea.Cmd {
    return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width = msg.Width
        m.height = msg.Height
        m.ready = true

        // Allocate space: list on the left, status on the right.
        listWidth := m.width / 2
        statusWidth := m.width - listWidth - 4
        if statusWidth < 20 {
            statusWidth = 20
        }

        m.list.SetSize(listWidth, m.height-4)
        m.status.Width = statusWidth
        m.status.Height = m.height - 4
        return m, nil

    case tea.KeyMsg:
        switch msg.String() {
        case "ctrl+c", "q":
            return m, tea.Quit
        case "enter":
            // Run the action associated with the selected item.
            if sel, ok := m.list.SelectedItem().(menuItem); ok {
                return m, m.runAction(sel.actionID)
            }
        }

    case cmdResultMsg:
        // Update status viewport with command output.
        content := fmt.Sprintf("Action: %s\n\n", msg.actionID)
        if msg.err != nil {
            content += fmt.Sprintf("ERROR: %v\n\n", msg.err)
        }
        content += msg.output
        m.status.SetContent(content)
        return m, nil
    }

    // Let the list handle remaining messages.
    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    return m, cmd
}

func (m model) View() string {
    if !m.ready {
        return "Loading..."
    }

    header := titleStyle.Render(appName)

    // Left (menu) and right (status).
    left := m.list.View()
    rightTitle := statusTitleStyle.Render("Status / Output")
    rightBody := statusBoxStyle.Render(rightTitle+"\n"+m.status.View())

    // Place them side by side.
    main := lipgloss.JoinHorizontal(lipgloss.Top, left, rightBody)

    return appBorderStyle.Render(header+"\n\n"+main)
}

// -----------------------------
// Actions
// -----------------------------

func (m model) runAction(actionID string) tea.Cmd {
    switch actionID {
    case "ssh_info":
        return func() tea.Msg {
            text := fmt.Sprintf(`To run this TUI over SSH via wish:

1. Build the binary:
   go build -o cbw-tui

2. Run in SSH server mode on the host:
   ./cbw-tui --ssh-server

3. From a client:
   ssh -p %s user@host

wish will manage sessions and run this Bubble Tea app per connection.`, sshListenAddr)
            return cmdResultMsg{actionID: actionID, output: text}
        }

    case "gum_demo":
        return runExternalCLI(actionID, "gum", []string{"style", "--foreground=10", "--border-foreground=14", "CBW Gum Demo"})

    case "glow_readme":
        // Try to show README.md if it exists, otherwise just run glow.
        args := []string{"README.md"}
        if _, err := os.Stat("README.md"); errors.Is(err, os.ErrNotExist) {
            args = nil
        }
        return runExternalCLI(actionID, "glow", args)

    case "mods_prompt":
        return runExternalCLI(actionID, "mods", []string{"whoami"})

    case "skate_namespaces":
        return runExternalCLI(actionID, "skate", []string{"namespaces"})

    case "about":
        return func() tea.Msg {
            text := `This is a starter TUI skeleton built on the Charmbracelet ecosystem:

- bubbletea: core state machine + update loop
- bubbles: list + viewport components
- lipgloss: layout & styling
- wish: SSH server wrapping the Bubble Tea program
- gum / glow / mods / skate: optional external CLIs integrated via shell-out

Extend this by:
- Adding more menu items for SSH/key management, repo helpers, etc.
- Wiring in your own commands or Go functions per action.
- Turning this into a full "cbw-control" dashboard.`
            return cmdResultMsg{actionID: actionID, output: text}
        }

    default:
        return func() tea.Msg {
            return cmdResultMsg{actionID: actionID, output: "Unknown action", err: fmt.Errorf("unhandled action: %s", actionID)}
        }
    }
}

// runExternalCLI safely shells out to an external CLI (gum, glow, mods, skate, ...)
// and returns its output as a cmdResultMsg.
func runExternalCLI(actionID, bin string, args []string) tea.Cmd {
    return func() tea.Msg {
        path, err := exec.LookPath(bin)
        if err != nil {
            return cmdResultMsg{
                actionID: actionID,
                err:      fmt.Errorf("%s not found in PATH (install it to use this action)", bin),
                output:   "",
            }
        }

        // Context with timeout for safety.
        ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
        defer cancel()

        cmd := exec.CommandContext(ctx, path, args...)
        cmd.Env = os.Environ()

        out, err := cmd.CombinedOutput()
        cleaned := strings.TrimSpace(string(out))

        // Avoid returning nil output, make it at least a placeholder.
        if cleaned == "" {
            cleaned = fmt.Sprintf("%s ran but produced no output.", filepath.Base(path))
        }

        return cmdResultMsg{
            actionID: actionID,
            err:      err,
            output:   cleaned,
        }
    }
}

// -----------------------------
// Wish SSH server wiring
// -----------------------------

// runSSHServer starts a wish-based SSH server that runs the Bubble Tea program
// for each incoming SSH session.
func runSSHServer() error {
    srv, err := wish.NewServer(
        wish.WithAddress(sshListenAddr),
        wish.WithHostKeyPath(sshHostKeyPath),
        wish.WithMiddleware(
            // Generic SSH middlewares.
            middleware.DefaultShell(),
            logging.Middleware(),
            // Bubble Tea session middleware.
            wishtea.Middleware(func(sess wishtea.Session) (tea.Model, []tea.ProgramOption) {
                m := initialModel()
                return m, []tea.ProgramOption{tea.WithAltScreen()}
            }),
        ),
    )
    if err != nil {
        return fmt.Errorf("failed to create SSH server: %w", err)
    }

    log.Printf("[INFO] SSH TUI server listening on %s (host key: %s)", sshListenAddr, sshHostKeyPath)

    if err := srv.ListenAndServe(); err != nil {
        return fmt.Errorf("ssh server stopped: %w", err)
    }
    return nil
}

// runLocalTUI starts the TUI in the current terminal.
func runLocalTUI() error {
    p := tea.NewProgram(initialModel(), tea.WithAltScreen())
    if _, err := p.Run(); err != nil {
        return fmt.Errorf("error running TUI: %w", err)
    }
    return nil
}

// -----------------------------
// main
// -----------------------------

func main() {
    log.SetPrefix("[cbw-tui] ")
    log.SetFlags(log.LstdFlags | log.Lshortfile)

    // Very small and explicit flag parsing to avoid pulling extra deps.
    useSSHServer := false
    for _, arg := range os.Args[1:] {
        switch arg {
        case "--ssh-server":
            useSSHServer = true
        case "-h", "--help":
            fmt.Println(appName)
            fmt.Println()
            fmt.Println("Usage:")
            fmt.Println("  cbw-tui           # run TUI in local terminal")
            fmt.Println("  cbw-tui --ssh-server  # run as wish SSH server")
            os.Exit(0)
        }
    }

    var err error
    if useSSHServer {
        err = runSSHServer()
    } else {
        err = runLocalTUI()
    }

    if err != nil {
        log.Println("fatal error:", err)
        os.Exit(1)
    }
}
