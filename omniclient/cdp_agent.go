package main

import (
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/playwright-community/playwright-go"
)

const (
	maxSnapshotNodes = 400 // tetto righe per contenere i token
	maxNameRunes     = 100 // lunghezza massima del nome di un nodo
)

// WebSession e' la sessione browser di UN agente (un BrowserContext + una tab).
type WebSession struct {
	AgentID string

	// mu protegge lo stato letto/scritto spesso: mappa ref, generazione, posizione mouse.
	mu     sync.RWMutex
	refs   map[int]int64 // ref LLM -> backendDOMNodeId
	gen    int           // numero dello snapshot corrente
	mouseX float64
	mouseY float64

	// actionMu serializza le azioni CDP sulla stessa sessione (una alla volta).
	actionMu sync.Mutex

	context playwright.BrowserContext
	page    playwright.Page
	cdp     playwright.CDPSession
}

// ---------------------------------------------------------------------------
// Registro sessioni
// ---------------------------------------------------------------------------

type sessionRegistry struct {
	mu sync.Mutex
	m  map[string]*WebSession
}

var sessions = &sessionRegistry{m: map[string]*WebSession{}}

// GetOrCreate restituisce la sessione dell'agente, creandola se non esiste.
// Ogni agente ha un BrowserContext isolato (cookie e storage separati).
// ATTENZIONE: un contesto nuovo NON contiene i login del profilo Chrome principale.
func (r *sessionRegistry) GetOrCreate(agentID string) (*WebSession, error) {
	if agentID == "" {
		return nil, fmt.Errorf("agent_id obbligatorio")
	}
	r.mu.Lock()
	defer r.mu.Unlock()

	if s, ok := r.m[agentID]; ok {
		return s, nil
	}
	if pwBrowser == nil {
		return nil, fmt.Errorf("browser non inizializzato: chiamare InitWebAgent() all'avvio")
	}

	// NoViewport: evita l'emulazione di 1280x720, che altera l'impronta della finestra reale.
	ctx, err := pwBrowser.NewContext(playwright.BrowserNewContextOptions{
		NoViewport: playwright.Bool(true),
	})
	if err != nil {
		return nil, fmt.Errorf("creazione contesto: %w", err)
	}
	page, err := ctx.NewPage()
	if err != nil {
		_ = ctx.Close()
		return nil, fmt.Errorf("creazione pagina: %w", err)
	}
	cdp, err := ctx.NewCDPSession(page)
	if err != nil {
		_ = ctx.Close()
		return nil, fmt.Errorf("creazione sessione CDP: %w", err)
	}

	s := &WebSession{
		AgentID: agentID,
		refs:    map[int]int64{},
		context: ctx,
		page:    page,
		cdp:     cdp,
	}
	r.m[agentID] = s
	return s, nil
}

// Close chiude e rimuove la sessione di un agente.
func (r *sessionRegistry) Close(agentID string) error {
	r.mu.Lock()
	s, ok := r.m[agentID]
	delete(r.m, agentID)
	r.mu.Unlock()
	if !ok {
		return nil
	}
	_ = s.cdp.Detach()
	return s.context.Close()
}

// ---------------------------------------------------------------------------
// Tipi CDP
// ---------------------------------------------------------------------------

type axValue struct {
	Value json.RawMessage `json:"value"`
}

type axProperty struct {
	Name  string  `json:"name"`
	Value axValue `json:"value"`
}

type axNode struct {
	NodeID           string       `json:"nodeId"`
	ParentID         string       `json:"parentId"`
	Ignored          bool         `json:"ignored"`
	Role             axValue      `json:"role"`
	Name             axValue      `json:"name"`
	Value            axValue      `json:"value"`
	Properties       []axProperty `json:"properties"`
	BackendDOMNodeID int64        `json:"backendDOMNodeId"`
}

type axTreeResponse struct {
	Nodes []axNode `json:"nodes"`
}

// rawToString converte un valore JSON CDP (stringa, bool, numero) in testo.
func rawToString(raw json.RawMessage) string {
	if len(raw) == 0 {
		return ""
	}
	var v interface{}
	if err := json.Unmarshal(raw, &v); err != nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	case bool:
		return strconv.FormatBool(t)
	case float64:
		return strconv.FormatFloat(t, 'f', -1, 64)
	default:
		return ""
	}
}

// clean normalizza spazi/newline e tronca il testo.
func clean(s string) string {
	s = strings.Join(strings.Fields(s), " ")
	r := []rune(s)
	if len(r) > maxNameRunes {
		return string(r[:maxNameRunes]) + "..."
	}
	return s
}

// cdpSend invia un comando CDP e decodifica la risposta in out (se non nil).
func (s *WebSession) cdpSend(method string, params map[string]interface{}, out interface{}) error {
	res, err := s.cdp.Send(method, params)
	if err != nil {
		return fmt.Errorf("%s: %w", method, err)
	}
	if out == nil {
		return nil
	}
	raw, err := json.Marshal(res)
	if err != nil {
		return fmt.Errorf("%s: codifica risposta: %w", method, err)
	}
	if err := json.Unmarshal(raw, out); err != nil {
		return fmt.Errorf("%s: decodifica risposta: %w", method, err)
	}
	return nil
}

// ---------------------------------------------------------------------------
// Step 2a: SnapshotState
// ---------------------------------------------------------------------------

var interactiveRoles = map[string]bool{
	"button": true, "link": true, "textbox": true, "searchbox": true,
	"combobox": true, "checkbox": true, "radio": true, "switch": true,
	"menuitem": true, "menuitemcheckbox": true, "menuitemradio": true,
	"tab": true, "option": true, "slider": true, "spinbutton": true,
	"treeitem": true,
}

// Ruoli input che meritano un ref anche senza nome accessibile.
var inputLikeRoles = map[string]bool{
	"textbox": true, "searchbox": true, "combobox": true, "checkbox": true,
	"radio": true, "switch": true, "slider": true, "spinbutton": true,
}

// SnapshotState ottiene l'AX tree via CDP, scarta i nodi nascosti/inutili,
// assegna ID sequenziali (ref) mappati sui backendDOMNodeId e restituisce
// il testo compatto per l'LLM. La mappa ref precedente viene sostituita:
// i ref di snapshot vecchi diventano invalidi.
func SnapshotState(sess *WebSession) (string, error) {
	if sess == nil {
		return "", fmt.Errorf("sessione nulla")
	}
	sess.actionMu.Lock()
	defer sess.actionMu.Unlock()

	var tree axTreeResponse
	if err := sess.cdpSend("Accessibility.getFullAXTree", nil, &tree); err != nil {
		return "", err
	}

	newRefs := make(map[int]int64)
	refNode := make(map[string]bool) // nodeId -> ha ottenuto un ref
	covered := make(map[string]bool) // nodeId -> il suo testo e' gia' nel nome di un antenato con ref
	var body strings.Builder
	nextID := 1
	lines := 0
	truncated := false

	for i := range tree.Nodes {
		n := &tree.Nodes[i]

		// Propaga la copertura dal padre (l'albero arriva in pre-ordine).
		covered[n.NodeID] = covered[n.ParentID] || refNode[n.ParentID]

		if n.Ignored {
			continue
		}
		role := rawToString(n.Role.Value)
		name := clean(rawToString(n.Name.Value))

		props := make(map[string]string, len(n.Properties))
		for _, p := range n.Properties {
			props[p.Name] = rawToString(p.Value.Value)
		}
		if props["hidden"] == "true" {
			continue
		}

		isRef := n.BackendDOMNodeID != 0 &&
			((interactiveRoles[role] && (name != "" || inputLikeRoles[role])) ||
				((role == "heading" || role == "img") && name != ""))

		isText := role == "StaticText" && len([]rune(name)) >= 2 && !covered[n.NodeID]

		if !isRef && !isText {
			continue
		}
		if lines >= maxSnapshotNodes {
			truncated = true
			break
		}

		if isText {
			fmt.Fprintf(&body, "    text %q\n", name)
			lines++
			continue
		}

		// Stati utili all'LLM (disabled, checked, ecc.).
		var states []string
		for _, k := range []string{"disabled", "required", "focused", "selected"} {
			if props[k] == "true" {
				states = append(states, k)
			}
		}
		for _, k := range []string{"checked", "expanded", "pressed"} {
			if v := props[k]; v != "" {
				states = append(states, k+"="+v)
			}
		}
		if lvl := props["level"]; role == "heading" && lvl != "" {
			states = append(states, "level="+lvl)
		}
		if inputLikeRoles[role] {
			if v := clean(rawToString(n.Value.Value)); v != "" {
				states = append(states, fmt.Sprintf("value=%q", v))
			}
		}

		id := nextID
		nextID++
		newRefs[id] = n.BackendDOMNodeID
		refNode[n.NodeID] = true

		fmt.Fprintf(&body, "[%d] %s %q", id, role, name)
		if len(states) > 0 {
			fmt.Fprintf(&body, " (%s)", strings.Join(states, ", "))
		}
		body.WriteByte('\n')
		lines++
	}

	// Sostituzione atomica della mappa ref.
	sess.mu.Lock()
	sess.refs = newRefs
	sess.gen++
	gen := sess.gen
	sess.mu.Unlock()

	title, _ := sess.page.Title()
	var out strings.Builder
	fmt.Fprintf(&out, "# snapshot %d | %s | %s\n", gen, clean(title), sess.page.URL())
	out.WriteString(body.String())
	if truncated {
		fmt.Fprintf(&out, "# ... troncato a %d righe; scorri o restringi la pagina e rifai lo snapshot\n", maxSnapshotNodes)
	}
	return out.String(), nil
}

// ---------------------------------------------------------------------------
// Step 2b: TrustedClick
// ---------------------------------------------------------------------------

func quadArea(q []float64) float64 {
	// Formula del poligono (shoelace) su 4 punti.
	a := 0.0
	for i := 0; i < 4; i++ {
		j := (i + 1) % 4
		a += q[2*i]*q[2*j+1] - q[2*j]*q[2*i+1]
	}
	return math.Abs(a) / 2
}

func quadCenterSize(q []float64) (cx, cy, w, h float64) {
	minX, maxX := q[0], q[0]
	minY, maxY := q[1], q[1]
	for i := 0; i < 4; i++ {
		cx += q[2*i] / 4
		cy += q[2*i+1] / 4
		minX, maxX = math.Min(minX, q[2*i]), math.Max(maxX, q[2*i])
		minY, maxY = math.Min(minY, q[2*i+1]), math.Max(maxY, q[2*i+1])
	}
	return cx, cy, maxX - minX, maxY - minY
}

// targetPoint calcola centro e dimensioni (px CSS del viewport) del nodo.
// Usa DOM.getContentQuads (gestisce trasformazioni) con ripiego su DOM.getBoxModel.
func (s *WebSession) targetPoint(backendID int64) (cx, cy, w, h float64, err error) {
	params := map[string]interface{}{"backendNodeId": backendID}

	var quads struct {
		Quads [][]float64 `json:"quads"`
	}
	qErr := s.cdpSend("DOM.getContentQuads", params, &quads)
	if qErr == nil {
		best := 1.0
		found := false
		for _, q := range quads.Quads {
			if len(q) < 8 {
				continue
			}
			if a := quadArea(q); a > best {
				best = a
				cx, cy, w, h = quadCenterSize(q)
				found = true
			}
		}
		if found {
			return cx, cy, w, h, nil
		}
	}

	var box struct {
		Model struct {
			Content []float64 `json:"content"`
		} `json:"model"`
	}
	if bErr := s.cdpSend("DOM.getBoxModel", params, &box); bErr != nil {
		return 0, 0, 0, 0, fmt.Errorf("nodo non raggiungibile (ref scaduto?): %w", bErr)
	}
	if len(box.Model.Content) < 8 || quadArea(box.Model.Content) <= 1 {
		return 0, 0, 0, 0, fmt.Errorf("elemento senza area visibile")
	}
	cx, cy, w, h = quadCenterSize(box.Model.Content)
	return cx, cy, w, h, nil
}

func (s *WebSession) mouse(kind string, x, y float64, button string, buttons, clickCount int) error {
	return s.cdpSend("Input.dispatchMouseEvent", map[string]interface{}{
		"type":       kind,
		"x":          x,
		"y":          y,
		"button":     button,
		"buttons":    buttons,
		"clickCount": clickCount,
	}, nil)
}

// TrustedClick risolve il ref in coordinate e produce eventi mouse "hardware"
// (Input.dispatchMouseEvent), quindi con isTrusted=true.
func TrustedClick(sess *WebSession, refID int) (string, error) {
	if sess == nil {
		return "", fmt.Errorf("sessione nulla")
	}
	sess.actionMu.Lock()
	defer sess.actionMu.Unlock()

	sess.mu.RLock()
	backendID, ok := sess.refs[refID]
	startX, startY := sess.mouseX, sess.mouseY
	gen := sess.gen
	sess.mu.RUnlock()
	if !ok {
		return "", fmt.Errorf("ref %d inesistente o scaduto: eseguire di nuovo web_snapshot", refID)
	}

	// Porta la tab in primo piano e il nodo nel viewport.
	_ = sess.cdpSend("Page.bringToFront", nil, nil)
	if err := sess.cdpSend("DOM.scrollIntoViewIfNeeded", map[string]interface{}{"backendNodeId": backendID}, nil); err != nil {
		return "", fmt.Errorf("ref %d non piu' nel DOM (snapshot %d): rifare web_snapshot: %w", refID, gen, err)
	}

	cx, cy, w, h, err := sess.targetPoint(backendID)
	if err != nil {
		return "", err
	}

	// Punto di click con piccolo scarto casuale interno all'elemento.
	px := cx + (rand.Float64()-0.5)*w*0.4
	py := cy + (rand.Float64()-0.5)*h*0.4
	if px < 1 || py < 1 {
		return "", fmt.Errorf("elemento fuori dal viewport (%.0f,%.0f)", px, py)
	}

	// Controllo occlusione: chi si trova davvero in quel punto?
	warn := ""
	var hit struct {
		BackendNodeID int64 `json:"backendNodeId"`
	}
	if err := sess.cdpSend("DOM.getNodeForLocation", map[string]interface{}{"x": int(px), "y": int(py)}, &hit); err == nil && hit.BackendNodeID != backendID {
		warn = " | ATTENZIONE: nel punto cliccato c'e' un altro nodo (figlio o overlay)"
	}

	if startX == 0 && startY == 0 {
		startX = 100 + rand.Float64()*200
		startY = 100 + rand.Float64()*200
	}

	// Movimento con curva smoothstep e micro-jitter.
	steps := 8 + rand.Intn(7)
	for i := 1; i <= steps; i++ {
		t := float64(i) / float64(steps)
		e := t * t * (3 - 2*t)
		mx := startX + (px-startX)*e
		my := startY + (py-startY)*e
		if i < steps {
			mx += (rand.Float64() - 0.5) * 2
			my += (rand.Float64() - 0.5) * 2
		}
		if err := sess.mouse("mouseMoved", mx, my, "none", 0, 0); err != nil {
			return "", err
		}
		time.Sleep(time.Duration(8+rand.Intn(14)) * time.Millisecond)
	}

	if err := sess.mouse("mousePressed", px, py, "left", 1, 1); err != nil {
		return "", err
	}
	time.Sleep(time.Duration(45+rand.Intn(70)) * time.Millisecond)
	if err := sess.mouse("mouseReleased", px, py, "left", 0, 1); err != nil {
		return "", err
	}

	sess.mu.Lock()
	sess.mouseX, sess.mouseY = px, py
	sess.mu.Unlock()

	return fmt.Sprintf("click ok su ref %d (snapshot %d) in (%.0f,%.0f)%s", refID, gen, px, py, warn), nil
}
