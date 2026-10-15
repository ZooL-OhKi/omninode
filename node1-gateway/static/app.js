const OMNINODE_KEY = 'omninode-super-secure-key-2026'; // Da gestire con auth in futuro
const nodesList = document.getElementById('nodes-list');
const chatHistory = document.getElementById('chat-history');
const commandInput = document.getElementById('command-input');
const sendBtn = document.getElementById('send-btn');

function addMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    msg.textContent = text;
    chatHistory.appendChild(msg);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function fetchNodes() {
    try {
        const res = await fetch('/api/v1/nodes', {
            headers: { 'x-omninode-key': OMNINODE_KEY }
        });
        const data = await res.json();
        nodesList.innerHTML = '';
        if(data.nodes.length === 0) {
            nodesList.innerHTML = '<div class="node-card text-muted">Nessun nodo attivo rilevato.</div>';
            return;
        }
        data.nodes.forEach(node => {
            const card = document.createElement('div');
            card.className = 'node-card';
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>${node.node_id}</strong>
                    <span class="status-badge ${node.status}">${node.status}</span>
                </div>
                <div style="color: var(--text-muted);">Load: ${node.load}%</div>
            `;
            nodesList.appendChild(card);
        });
    } catch (e) {
        console.error("Errore fetch nodi", e);
    }
}

sendBtn.addEventListener('click', () => {
    const text = commandInput.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    commandInput.value = '';
    
    // Stub per l'invio all'LLM/Gateway: In futuro interfaccerà l'API MCP/Tasks
    setTimeout(() => {
        addMessage("Comando ricevuto. (Integrazione LLM in attesa della Phase 4)", 'ai');
    }, 500);
});

commandInput.addEventListener('keypress', (e) => {
    if(e.key === 'Enter') sendBtn.click();
});

// Polling nodi ogni 5 secondi
setInterval(fetchNodes, 5000);
fetchNodes();
