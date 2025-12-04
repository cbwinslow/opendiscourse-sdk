// File: cmd/agenthub-tui/main.go
// Author: cbwinslow + ChatGPT (AI copilot)
// Summary:
//   Bubble Tea TUI for navigating the AI Agent Hub.
//   - Reads $AI_AGENT_HUB_ROOT (or ~/dev/ai-agent-hub)
//   - Loads global/agents.yaml
//   - Displays agents in a list
//   - Shows basic details for the selected agent
//
// Build:
//   go mod init cloudcurio.cc/ai-agent-hub-tui
//   go get github.com/charmbracelet/bubbletea@latest
//   go get github.com/charmbracelet/bubbles@latest
//   go get github.com/charmbracelet/lipgloss@latest
//   go get gopkg.in/yaml.v3
//   go build ./cmd/agenthub-tui
//
// Run:
//   AI_AGENT_HUB_ROOT=~/dev/ai-agent-hub ./agenthub-tui
//
package main

import (
    "fmt"
    "io/ioutil"
    "log"
    "os"
    "os/user"
    "path/filepath"

    tea "github.com/charmbracelet/bubbletea"
    "github.com/charmbracelet/bubbles/list"
    "github.com/charmbracelet/lipgloss"
    "gopkg.in/yaml.v3"
)

// Agent represents a single agent entry from global/agents.yaml
 type Agent struct {
    ID             string   `yaml:"id"`
    Name           string   `yaml:"name"`
    Type           string   `yaml:"type"`
    Binary         string   `yaml:"binary"`
    ConfigPath     string   `yaml:"config_path"`
    Profiles       []string `yaml:"profiles"`
    DefaultProfile string   `yaml:"default_profile"`
    MCPServers     []string `yaml:"mcp_servers"`
    Notes          string   `yaml:"notes"`
}

// AgentsFile is the YAML root struct.
type AgentsFile struct {
    Agents []Agent `yaml:"agents"`
}

// agentItem wraps Agent to implement list.Item.
type agentItem struct {
    agent Agent
}

func (a agentItem) Title() string {
    if a.agent.Name != "" {
        return fmt.Sprintf("%s (%s)", a.agent.Name, a.agent.ID)
    }
    return a.agent.ID
}

func (a agentItem) Description() string {
    t := a.agent.Type
    if t == "" {
        t = "unknown-type"
    }
    return fmt.Sprintf("type: %s | binary: %s", t, a.agent.Binary)
}

func (a agentItem) FilterValue() string {
    return a.agent.ID + " " + a.agent.Name + " " + a.agent.Type
}

// Styles
var (
    titleStyle  = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("81"))
    statusStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))
    helpStyle   = lipgloss.NewStyle().Foreground(lipgloss.Color("240")).Italic(true)
)

// model holds the Bubble Tea state.
type model struct {
    list    list.Model
    status  string
    hubRoot string
}

func initialModel() model {
    hubRoot := resolveHubRoot()
    items, status := loadAgentsAsItems(hubRoot)

    l := list.New(items, list.NewDefaultDelegate(), 0, 0)
    l.Title = "AI Agent Hub – Agents"
    l.SetFilteringEnabled(true)

    return model{
        list:    l,
        status:  status,
        hubRoot: hubRoot,
    }
}

// resolveHubRoot returns the agent hub root using AI_AGENT_HUB_ROOT or ~/dev/ai-agent-hub.
func resolveHubRoot() string {
    if root := os.Getenv("AI_AGENT_HUB_ROOT"); root != "" {
        return expandHome(root)
    }
    return filepath.Join(userHomeDir(), "dev", "ai-agent-hub")
}

// userHomeDir returns the current user's home directory.
func userHomeDir() string {
    if h, err := os.UserHomeDir(); err == nil {
        return h
    }
    if u, err := user.Current(); err == nil {
        return u.HomeDir
    }
    // Fallback to /tmp if everything else fails.
    return "/tmp"
}

// expandHome expands a leading ~ to the current user's home directory.
func expandHome(path string) string {
    if path == "" {
        return path
    }
    if path[0] != '~' {
        return path
    }
    home := userHomeDir()
    if path == "~" {
        return home
    }
    if len(path) > 1 && path[1] == '/' {
        return filepath.Join(home, path[2:])
    }
    // We don't support ~otheruser, just return original.
    return path
}

// loadAgentsAsItems loads global/agents.yaml and returns Bubble Tea list items.
func loadAgentsAsItems(hubRoot string) ([]list.Item, string) {
    agentsFile := filepath.Join(hubRoot, "global", "agents.yaml")
    data, err := ioutil.ReadFile(agentsFile)
    if err != nil {
        status := fmt.Sprintf("No agents.yaml found at %s. Use cc_new_agent to create agents.", agentsFile)
        return []list.Item{}, status
    }

    var af AgentsFile
    if err := yaml.Unmarshal(data, &af); err != nil {
        status := fmt.Sprintf("Failed to parse agents.yaml: %v", err)
        return []list.Item{}, status
    }

    if len(af.Agents) == 0 {
        status := "No agents registered yet. Use cc_new_agent in your shell to add some."
        return []list.Item{}, status
    }

    items := make([]list.Item, 0, len(af.Agents))
    for _, a := range af.Agents {
        items = append(items, agentItem{agent: a})
    }
    status := fmt.Sprintf("Loaded %d agents from %s", len(items), agentsFile)
    return items, status
}

// Init implements tea.Model.
func (m model) Init() tea.Cmd {
    return nil
}

// Update implements tea.Model.
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.list.SetSize(msg.Width, msg.Height-4)
        return m, nil

    case tea.KeyMsg:
        switch msg.String() {
        case "q", "esc", "ctrl+c":
            return m, tea.Quit
        case "enter":
            if item, ok := m.list.SelectedItem().(agentItem); ok {
                a := item.agent
                m.status = fmt.Sprintf("Selected %s (%s) – config: %s", a.Name, a.ID, a.ConfigPath)
            }
            return m, nil
        }
    }

    var cmd tea.Cmd
    m.list, cmd = m.list.Update(msg)
    return m, cmd
}

// View implements tea.Model.
func (m model) View() string {
    header := titleStyle.Render("AI Agent Hub TUI") + "\n" +
        fmt.Sprintf("Hub root: %s", m.hubRoot) + "\n\n"

    help := helpStyle.Render("↑/↓ to navigate • enter to select • q to quit")

    status := statusStyle.Render(m.status)

    return header + m.list.View() + "\n\n" + status + "\n" + help + "\n"
}

func main() {
    if err := run(); err != nil {
        log.Fatalf("error: %v", err)
    }
}

func run() error {
    m := initialModel()
    p := tea.NewProgram(m, tea.WithAltScreen())
    if _, err := p.Run(); err != nil {
        return fmt.Errorf("running TUI: %w", err)
    }
    return nil
}
