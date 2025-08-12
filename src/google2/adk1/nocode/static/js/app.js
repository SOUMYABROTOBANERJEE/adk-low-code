/**
 * Google ADK No-Code Platform - Frontend Application
 */

class ADKPlatform {
    constructor() {
        this.currentAgent = null;
        this.currentSession = null;
        this.agents = [];
        this.tools = [];
        this.projects = [];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadInitialData();
        this.checkADKStatus();
    }
    
    bindEvents() {
        // Navigation buttons
        document.getElementById('newAgentBtn').addEventListener('click', () => this.showAgentConfig());
        document.getElementById('newToolBtn').addEventListener('click', () => this.showToolModal());
        document.getElementById('exportBtn').addEventListener('click', () => this.showExportOptions());
        
        // Agent configuration
        document.getElementById('agentConfigForm').addEventListener('submit', (e) => this.handleAgentSubmit(e));
        document.getElementById('cancelAgentBtn').addEventListener('click', () => this.hideAgentConfig());
        
        // Tool creation
        document.getElementById('toolForm').addEventListener('submit', (e) => this.handleToolSubmit(e));
        document.getElementById('cancelToolBtn').addEventListener('click', () => this.hideToolModal());
        document.getElementById('toolType').addEventListener('change', (e) => this.handleToolTypeChange(e));
        
        // Chat interface
        document.getElementById('sendMessageBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        document.getElementById('chatAgentSelect').addEventListener('change', (e) => this.selectChatAgent(e));
        
        // Temperature slider
        document.getElementById('agentTemperature').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });
        
        // Code generation
        document.getElementById('closeCodeModalBtn').addEventListener('click', () => this.hideCodeModal());
        document.getElementById('downloadCodeBtn').addEventListener('click', () => this.downloadCode());
        
        // AI Suggestion buttons
        document.getElementById('suggestAgentNameBtn').addEventListener('click', () => this.suggestAgentName());
        document.getElementById('suggestAgentDescriptionBtn').addEventListener('click', () => this.suggestAgentDescription());
        document.getElementById('suggestAgentSystemPromptBtn').addEventListener('click', () => this.suggestAgentSystemPrompt());
        document.getElementById('suggestToolNameBtn').addEventListener('click', () => this.suggestToolName());
        document.getElementById('suggestToolDescriptionBtn').addEventListener('click', () => this.suggestToolDescription());
        document.getElementById('suggestToolCodeBtn').addEventListener('click', () => this.suggestToolCode());
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadAgents(),
                this.loadTools(),
                this.loadProjects()
            ]);
            this.updateCounts();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showMessage('Error loading data. Please refresh the page.', 'error');
        }
    }
    
    async checkADKStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            const statusElement = document.getElementById('adkStatus');
            const indicator = statusElement.querySelector('div');
            const text = statusElement.querySelector('span');
            
            if (data.adk_available) {
                indicator.className = 'w-3 h-3 rounded-full status-indicator online';
                text.textContent = 'ADK Available';
            } else {
                indicator.className = 'w-3 h-3 rounded-full status-indicator offline';
                text.textContent = 'ADK Not Available';
            }
        } catch (error) {
            console.error('Error checking ADK status:', error);
            const statusElement = document.getElementById('adkStatus');
            const indicator = statusElement.querySelector('div');
            const text = statusElement.querySelector('span');
            
            indicator.className = 'w-3 h-3 rounded-full status-indicator offline';
            text.textContent = 'Connection Error';
        }
    }
    
    async loadAgents() {
        try {
            const response = await fetch('/api/agents');
            const data = await response.json();
            this.agents = data.agents || [];
            this.renderAgents();
            this.updateChatAgentSelect();
        } catch (error) {
            console.error('Error loading agents:', error);
        }
    }
    
    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            const data = await response.json();
            this.tools = data.tools || [];
            this.renderTools();
            this.updateToolSelection();
        } catch (error) {
            console.error('Error loading tools:', error);
        }
    }
    
    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();
            this.projects = data.projects || [];
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }
    
    renderAgents() {
        const container = document.getElementById('agentsList');
        container.innerHTML = '';
        
        if (this.agents.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No agents created yet</p>';
            return;
        }
        
        this.agents.forEach(agent => {
            const agentElement = this.createAgentElement(agent);
            container.appendChild(agentElement);
        });
    }
    
    createAgentElement(agent) {
        const div = document.createElement('div');
        div.className = 'agent-card bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow';
        div.dataset.agentId = agent.id;
        
        div.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-medium text-gray-800">${agent.name}</h3>
                <span class="agent-type-badge ${agent.agent_type}">${agent.agent_type}</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">${agent.description}</p>
            <div class="flex items-center justify-between">
                <div class="flex space-x-1">
                    ${agent.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <div class="flex space-x-1">
                    <button class="text-blue-500 hover:text-blue-700 p-1" onclick="app.editAgent('${agent.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-green-500 hover:text-green-700 p-1" onclick="app.generateCode('${agent.id}')">
                        <i class="fas fa-code"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-1" onclick="app.deleteAgent('${agent.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        div.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.selectAgent(agent.id);
            }
        });
        
        return div;
    }
    
    renderTools() {
        const container = document.getElementById('toolsList');
        container.innerHTML = '';
        
        if (this.tools.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No tools created yet</p>';
            return;
        }
        
        this.tools.forEach(tool => {
            const toolElement = this.createToolElement(tool);
            container.appendChild(toolElement);
        });
    }
    
    createToolElement(tool) {
        const div = document.createElement('div');
        div.className = 'tool-card bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow';
        div.dataset.toolId = tool.id;
        
        div.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-medium text-gray-800">${tool.name}</h3>
                <span class="tool-type-badge ${tool.tool_type}">${tool.tool_type}</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">${tool.description}</p>
            <div class="flex items-center justify-between">
                <div class="flex space-x-1">
                    ${tool.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <div class="flex space-x-1">
                    <button class="text-blue-500 hover:text-blue-700 p-1" onclick="app.editTool('${tool.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-1" onclick="app.deleteTool('${tool.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        div.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                this.selectTool(tool.id);
            }
        });
        
        return div;
    }
    
    updateChatAgentSelect() {
        const select = document.getElementById('chatAgentSelect');
        select.innerHTML = '<option value="">Select an agent to chat with...</option>';
        
        this.agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.id;
            option.textContent = agent.name;
            select.appendChild(option);
        });
    }
    
    updateToolSelection() {
        const container = document.getElementById('agentToolsSelection');
        container.innerHTML = '';
        
        this.tools.forEach(tool => {
            const div = document.createElement('div');
            div.className = 'flex items-center space-x-2';
            
            div.innerHTML = `
                <input type="checkbox" id="tool_${tool.id}" value="${tool.id}" class="rounded">
                <label for="tool_${tool.id}" class="text-sm text-gray-700">${tool.name}</label>
            `;
            
            container.appendChild(div);
        });
    }
    
    updateCounts() {
        document.getElementById('agentCount').textContent = this.agents.length;
        document.getElementById('toolCount').textContent = this.tools.length;
    }
    
    showAgentConfig(agentId = null) {
        const panel = document.getElementById('agentConfigPanel');
        panel.classList.remove('hidden');
        
        if (agentId) {
            this.loadAgentForEdit(agentId);
        } else {
            this.resetAgentForm();
        }
        
        // Scroll to configuration panel
        panel.scrollIntoView({ behavior: 'smooth' });
    }
    
    hideAgentConfig() {
        document.getElementById('agentConfigPanel').classList.add('hidden');
        this.resetAgentForm();
    }
    
    resetAgentForm() {
        document.getElementById('agentConfigForm').reset();
        document.getElementById('temperatureValue').textContent = '0.7';
        document.getElementById('agentTemperature').value = '0.7';
        this.currentAgent = null;
    }
    
    async loadAgentForEdit(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}`);
            const agent = await response.json();
            
            this.currentAgent = agent;
            this.populateAgentForm(agent);
        } catch (error) {
            console.error('Error loading agent for edit:', error);
            this.showMessage('Error loading agent for editing', 'error');
        }
    }
    
    populateAgentForm(agent) {
        document.getElementById('agentName').value = agent.name;
        document.getElementById('agentType').value = agent.agent_type;
        document.getElementById('agentDescription').value = agent.description;
        document.getElementById('agentSystemPrompt').value = agent.system_prompt;
        document.getElementById('agentInstructions').value = agent.instructions || '';
        document.getElementById('agentModel').value = agent.model_settings?.model || 'gemini-2.0-flash';
        document.getElementById('agentTemperature').value = agent.model_settings?.temperature || 0.7;
        document.getElementById('temperatureValue').textContent = agent.model_settings?.temperature || 0.7;
        document.getElementById('agentMaxTokens').value = agent.model_settings?.max_tokens || 1000;
        
        // Check appropriate tools
        agent.tools.forEach(toolId => {
            const checkbox = document.getElementById(`tool_${toolId}`);
            if (checkbox) checkbox.checked = true;
        });
    }
    
    async handleAgentSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const agentData = {
            id: this.currentAgent?.id,
            name: formData.get('agentName') || document.getElementById('agentName').value,
            description: formData.get('agentDescription') || document.getElementById('agentDescription').value,
            agent_type: formData.get('agentType') || document.getElementById('agentType').value,
            system_prompt: formData.get('agentSystemPrompt') || document.getElementById('agentSystemPrompt').value,
            instructions: formData.get('agentInstructions') || document.getElementById('agentInstructions').value,
            model_settings: {
                model: document.getElementById('agentModel').value,
                temperature: parseFloat(document.getElementById('agentTemperature').value),
                max_tokens: parseInt(document.getElementById('agentMaxTokens').value)
            },
            tools: Array.from(document.querySelectorAll('#agentToolsSelection input:checked')).map(cb => cb.value),
            tags: []
        };
        
        try {
            const url = this.currentAgent ? `/api/agents/${this.currentAgent.id}` : '/api/agents';
            const method = this.currentAgent ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentData)
            });
            
            if (response.ok) {
                this.showMessage(`Agent ${this.currentAgent ? 'updated' : 'created'} successfully!`, 'success');
                await this.loadAgents();
                this.hideAgentConfig();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error saving agent:', error);
            this.showMessage('Error saving agent', 'error');
        }
    }
    
    showToolModal() {
        document.getElementById('toolModal').classList.remove('hidden');
    }
    
    hideToolModal() {
        document.getElementById('toolModal').classList.add('hidden');
        document.getElementById('toolForm').reset();
        document.getElementById('functionCodeSection').classList.add('hidden');
    }
    
    handleToolTypeChange(e) {
        const functionSection = document.getElementById('functionCodeSection');
        if (e.target.value === 'function') {
            functionSection.classList.remove('hidden');
        } else {
            functionSection.classList.add('hidden');
        }
    }
    
    async handleToolSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const toolData = {
            name: formData.get('toolName') || document.getElementById('toolName').value,
            description: formData.get('toolDescription') || document.getElementById('toolDescription').value,
            tool_type: formData.get('toolType') || document.getElementById('toolType').value,
            function_code: document.getElementById('toolFunctionCode').value || null,
            tags: []
        };
        
        try {
            const response = await fetch('/api/tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolData)
            });
            
            if (response.ok) {
                this.showMessage('Tool created successfully!', 'success');
                await this.loadTools();
                this.hideToolModal();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error creating tool:', error);
            this.showMessage('Error creating tool', 'error');
        }
    }
    
    selectChatAgent(e) {
        const agentId = e.target.value;
        if (agentId) {
            this.currentAgent = this.agents.find(a => a.id === agentId);
            this.currentSession = null;
            this.clearChat();
            this.showMessage(`Selected agent: ${this.currentAgent.name}`, 'info');
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message || !this.currentAgent) {
            this.showMessage('Please select an agent and enter a message', 'warning');
            return;
        }
        
        // Add user message to chat
        this.addChatMessage('user', message);
        input.value = '';
        
        try {
            const response = await fetch(`/api/chat/${this.currentAgent.id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    session_id: this.currentSession
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.addChatMessage('assistant', data.response);
            } else {
                this.addChatMessage('system', `Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addChatMessage('system', 'Error: Failed to send message');
        }
    }
    
    addChatMessage(role, content) {
        const container = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        messageDiv.textContent = content;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    clearChat() {
        document.getElementById('chatMessages').innerHTML = 
            '<div class="text-center text-gray-500">Select an agent to start chatting</div>';
    }
    
    async generateCode(agentId) {
        try {
            const response = await fetch(`/api/generate/${agentId}`, { method: 'POST' });
            const data = await response.json();
            
            document.getElementById('generatedCode').textContent = data.code;
            document.getElementById('codeModal').classList.remove('hidden');
        } catch (error) {
            console.error('Error generating code:', error);
            this.showMessage('Error generating code', 'error');
        }
    }
    
    hideCodeModal() {
        document.getElementById('codeModal').classList.add('hidden');
    }
    
    downloadCode() {
        const code = document.getElementById('generatedCode').textContent;
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'agent.py';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    async deleteAgent(agentId) {
        if (!confirm('Are you sure you want to delete this agent?')) return;
        
        try {
            const response = await fetch(`/api/agents/${agentId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.showMessage('Agent deleted successfully!', 'success');
                await this.loadAgents();
            } else {
                this.showMessage('Error deleting agent', 'error');
            }
        } catch (error) {
            console.error('Error deleting agent:', error);
            this.showMessage('Error deleting agent', 'error');
        }
    }
    
    async deleteTool(toolId) {
        if (!confirm('Are you sure you want to delete this tool?')) return;
        
        try {
            const response = await fetch(`/api/tools/${toolId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.showMessage('Tool deleted successfully!', 'success');
                await this.loadTools();
            } else {
                this.showMessage('Error deleting tool', 'error');
            }
        } catch (error) {
            console.error('Error deleting tool:', error);
            this.showMessage('Error deleting tool', 'error');
        }
    }
    
    showExportOptions() {
        // Simple export options - could be expanded
        if (this.agents.length === 0) {
            this.showMessage('No agents to export', 'warning');
            return;
        }
        
        this.showMessage('Export functionality coming soon!', 'info');
    }
    
    showMessage(message, type = 'info') {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} fixed top-4 right-4 z-50 max-w-sm`;
        messageDiv.textContent = message;
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'float-right font-bold text-lg cursor-pointer ml-2';
        closeBtn.onclick = () => messageDiv.remove();
        messageDiv.appendChild(closeBtn);
        
        document.body.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    // Utility methods
    selectAgent(agentId) {
        // Remove previous selection
        document.querySelectorAll('.agent-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to current card
        const card = document.querySelector(`[data-agent-id="${agentId}"]`);
        if (card) {
            card.classList.add('selected');
        }
        
        this.showAgentConfig(agentId);
    }
    
    selectTool(toolId) {
        // Remove previous selection
        document.querySelectorAll('.tool-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Add selection to current card
        const card = document.querySelector(`[data-tool-id="${toolId}"]`);
        if (card) {
            card.classList.add('selected');
        }
    }
    
    // AI Suggestion Methods
    async suggestAgentName() {
        const description = document.getElementById('agentDescription').value;
        if (!description.trim()) {
            this.showMessage('Please enter a description first to get name suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/agent/name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: description.trim() })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('agentName').value = data.suggestion;
                this.showMessage('AI suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting agent name suggestion:', error);
            this.showMessage('Error getting AI suggestion', 'error');
        }
    }
    
    async suggestAgentDescription() {
        const name = document.getElementById('agentName').value;
        const agentType = document.getElementById('agentType').value;
        
        if (!name.trim()) {
            this.showMessage('Please enter a name first to get description suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/agent/description', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), agent_type: agentType })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('agentDescription').value = data.suggestion;
                this.showMessage('AI suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting agent description suggestion:', error);
            this.showMessage('Error getting AI suggestion', 'error');
        }
    }
    
    async suggestAgentSystemPrompt() {
        const name = document.getElementById('agentName').value;
        const description = document.getElementById('agentDescription').value;
        const agentType = document.getElementById('agentType').value;
        
        if (!name.trim() || !description.trim()) {
            this.showMessage('Please enter both name and description first to get system prompt suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/agent/system_prompt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: name.trim(), 
                    description: description.trim(), 
                    agent_type: agentType 
                })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('agentSystemPrompt').value = data.suggestion;
                this.showMessage('AI suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting agent system prompt suggestion:', error);
            this.showMessage('Error getting AI suggestion', 'error');
        }
    }
    
    async suggestToolName() {
        const description = document.getElementById('toolDescription').value;
        const toolType = document.getElementById('toolType').value;
        
        if (!description.trim()) {
            this.showMessage('Please enter a description first to get name suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/tool/name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ description: description.trim(), tool_type: toolType })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('toolName').value = data.suggestion;
                this.showMessage('AI suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting tool name suggestion:', error);
            this.showMessage('Error getting AI suggestion', 'error');
        }
    }
    
    async suggestToolDescription() {
        const name = document.getElementById('toolName').value;
        const toolType = document.getElementById('toolType').value;
        
        if (!name.trim()) {
            this.showMessage('Please enter a name first to get description suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/tool/description', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), tool_type: toolType })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('toolDescription').value = data.suggestion;
                this.showMessage('AI suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting tool description suggestion:', error);
            this.showMessage('Error getting AI suggestion', 'error');
        }
    }
    
    async suggestToolCode() {
        const name = document.getElementById('toolName').value;
        const description = document.getElementById('toolDescription').value;
        const toolType = document.getElementById('toolType').value;
        
        if (!name.trim() || !description.trim()) {
            this.showMessage('Please enter both name and description first to get code suggestions', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/suggestions/tool/code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: name.trim(), 
                    description: description.trim(), 
                    tool_type: toolType 
                })
            });
            
            const data = await response.json();
            if (data.success) {
                document.getElementById('toolFunctionCode').value = data.suggestion;
                this.showMessage('AI code suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI code suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting tool code suggestion:', error);
            this.showMessage('Error getting AI code suggestion', 'error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ADKPlatform();
});
