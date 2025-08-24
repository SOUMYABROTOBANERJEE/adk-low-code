/**
 * Agent Genie - Tata Steel AI Platform - Frontend Application
 */

class AgentGeniePlatform {
    constructor() {
        this.currentAgent = null;
        this.currentSession = null;
        this.agents = [];
        this.tools = [];
        this.projects = [];
        
        this.init();
    }
    
    init() {
        console.log('Initializing AgentGeniePlatform...');
        this.bindEvents();
        console.log('Events bound, loading initial data...');
        this.loadInitialData();
        this.checkADKStatus();
        this.showSection('dashboard'); // Show dashboard by default
        console.log('Initialization complete');
    }
    
    bindEvents() {
        console.log('Binding events...');
        
        // Navigation buttons
        document.querySelectorAll('[data-section]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const section = e.target.dataset.section;
                await this.showSection(section);
            });
        });
        
        // Dashboard Quick Action buttons
        document.getElementById('dashboardCreateAgentBtn')?.addEventListener('click', async () => {
            await this.showSection('agents');
            setTimeout(() => this.showModal('agentModal'), 100);
        });
        document.getElementById('dashboardCreateToolBtn')?.addEventListener('click', async () => {
            await this.showSection('tools');
            setTimeout(() => this.showModal('toolModal'), 100);
        });
        
        // Create buttons
        const createAgentBtn = document.getElementById('createAgentBtn');
        const createToolBtn = document.getElementById('createToolBtn');
        const createProjectBtn = document.getElementById('createProjectBtn');
        
        console.log('Create buttons found:', {
            createAgentBtn: !!createAgentBtn,
            createToolBtn: !!createToolBtn,
            createProjectBtn: !!createProjectBtn
        });
        
        createAgentBtn?.addEventListener('click', () => this.showModal('agentModal'));
        createToolBtn?.addEventListener('click', () => this.showModal('toolModal'));
        createProjectBtn?.addEventListener('click', () => this.showModal('projectModal'));
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.hideAllModals());
        });
        
        // Agent configuration
        document.getElementById('agentConfigForm')?.addEventListener('submit', (e) => this.handleAgentSubmit(e));
        document.getElementById('cancelAgentBtn')?.addEventListener('click', () => this.hideModal('agentModal'));
        
        // Tool creation
        document.getElementById('toolForm')?.addEventListener('submit', (e) => this.handleToolSubmit(e));
        document.getElementById('cancelToolBtn')?.addEventListener('click', () => this.hideModal('toolModal'));
        document.getElementById('toolType')?.addEventListener('change', (e) => this.handleToolTypeChange(e));
        
        // Project creation
        document.getElementById('projectForm')?.addEventListener('submit', (e) => this.handleProjectSubmit(e));
        document.getElementById('cancelProjectBtn')?.addEventListener('click', () => this.hideModal('projectModal'));
        
        // Sub-agent management
        document.getElementById('addSubAgentBtn')?.addEventListener('click', () => this.showModal('subAgentModal'));
        document.getElementById('addExistingAsSubBtn')?.addEventListener('click', () => this.showModal('linkExistingAgentModal'));
        document.getElementById('subAgentForm')?.addEventListener('submit', (e) => this.handleSubAgentSubmit(e));
        document.getElementById('linkExistingAgentForm')?.addEventListener('click', (e) => this.handleLinkExistingAgentSubmit(e));
        document.getElementById('cancelSubAgentBtn')?.addEventListener('click', () => this.hideModal('subAgentModal'));
        document.getElementById('cancelLinkExistingBtn')?.addEventListener('click', () => this.hideModal('linkExistingAgentModal'));
        document.getElementById('parentAgentSelect')?.addEventListener('change', (e) => this.onParentAgentChange(e));
        
        // Sub-agent functionality in agent modal
        const addExistingBtn = document.getElementById('addExistingAsSubInAgentBtn');
        const addNewBtn = document.getElementById('addNewSubAgentInAgentBtn');
        
        console.log('Sub-agent buttons found:', {
            addExistingBtn: !!addExistingBtn,
            addNewBtn: !!addNewBtn
        });
        
        addExistingBtn?.addEventListener('click', () => {
            console.log('Add Existing button clicked!');
            this.showSelectExistingAgentModal();
        });
        addNewBtn?.addEventListener('click', () => {
            console.log('Add New button clicked!');
            this.addNewSubAgentField();
        });
        document.getElementById('cancelSelectExistingBtn')?.addEventListener('click', () => this.hideModal('selectExistingAgentModal'));
        document.getElementById('confirmSelectExistingBtn')?.addEventListener('click', () => this.confirmSelectExistingAgent());
        
        // Chat interface
        document.getElementById('sendMessageBtn')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('chatInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        document.getElementById('chatAgentSelect')?.addEventListener('change', (e) => this.selectChatAgent(e));
        document.getElementById('clearChatBtn')?.addEventListener('click', () => this.clearChat());
        
        // Temperature slider
        document.getElementById('agentTemperature')?.addEventListener('input', (e) => {
            const valueDisplay = document.getElementById('temperatureValue');
            if (valueDisplay) valueDisplay.textContent = e.target.value;
        });
        
        // AI Suggestion buttons
        document.getElementById('suggestAgentNameBtn')?.addEventListener('click', () => this.suggestAgentName());
        document.getElementById('suggestAgentDescriptionBtn')?.addEventListener('click', () => this.suggestAgentDescription());
        document.getElementById('suggestAgentSystemPromptBtn')?.addEventListener('click', () => this.suggestAgentSystemPrompt());
        document.getElementById('suggestToolNameBtn')?.addEventListener('click', () => this.suggestToolName());
        document.getElementById('suggestToolDescriptionBtn')?.addEventListener('click', () => this.suggestToolDescription());
        document.getElementById('suggestToolCodeBtn')?.addEventListener('click', () => this.suggestToolCode());
        document.getElementById('generateToolCodeBtn')?.addEventListener('click', () => this.generateToolCode());
        
        // Notifications
        document.getElementById('notificationsBtn')?.addEventListener('click', () => this.handleNotifications());
        
        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.logout());
    }
    
    // Sub-agent functionality in agent modal
    showSelectExistingAgentModal() {
        console.log('showSelectExistingAgentModal called');
        this.showModal('selectExistingAgentModal');
        this.populateAvailableAgentsForSelection();
    }
    
    async populateAvailableAgentsForSelection() {
        console.log('populateAvailableAgentsForSelection called');
        const container = document.getElementById('availableAgentsList');
        if (!container) {
            console.error('availableAgentsList container not found');
            return;
        }
        
        try {
            const availableAgents = await this.loadAvailableAgentsForSub();
            console.log('Available agents loaded:', availableAgents);
            
            if (availableAgents.length === 0) {
                container.innerHTML = `
                    <div class="text-center text-gray-500 py-4">
                        <i class="fas fa-robot text-2xl mb-2"></i>
                        <p>No agents available for sub-agent selection</p>
                        <p class="text-sm">Create some agents first to use them as sub-agents</p>
                    </div>
                `;
                return;
            }
            
            // Add header with instructions
            container.innerHTML = `
                <div class="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
                    <p class="text-sm text-blue-800">
                        <i class="fas fa-info-circle mr-1"></i>
                        Select one or more agents to use as sub-agents. You can select multiple agents.
                    </p>
                </div>
            `;
            
            availableAgents.forEach(agent => {
                const agentDiv = document.createElement('div');
                agentDiv.className = 'flex items-center p-3 border border-gray-200 rounded-md mb-2 hover:bg-gray-50 transition-colors';
                agentDiv.innerHTML = `
                    <input type="checkbox" id="select_${agent.id}" value="${agent.id}" class="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500">
                    <label for="select_${agent.id}" class="flex-1 cursor-pointer">
                        <div class="font-medium text-gray-900">${agent.name}</div>
                        <div class="text-sm text-gray-600">${agent.description || 'No description'}</div>
                        <div class="flex items-center space-x-2 mt-1">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                ${agent.agent_type || 'unknown'}
                            </span>
                            ${agent.tools && agent.tools.length > 0 ? 
                                `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    ${agent.tools.length} tools
                                </span>` : ''
                            }
                        </div>
                    </label>
                `;
                container.appendChild(agentDiv);
            });
        } catch (error) {
            console.error('Error populating available agents:', error);
        }
    }
    
    addNewSubAgentField() {
        console.log('addNewSubAgentField called');
        const container = document.getElementById('newSubAgentsContainer');
        if (!container) {
            console.error('newSubAgentsContainer not found');
            return;
        }
        
        const subAgentId = 'sub_' + Date.now();
        const subAgentDiv = document.createElement('div');
        subAgentDiv.className = 'border border-gray-300 rounded-md p-3 bg-gray-50';
        subAgentDiv.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">New Sub-Agent</span>
                <button type="button" onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Name</label>
                    <input type="text" name="subAgentName_${subAgentId}" class="w-full p-2 text-sm border border-gray-300 rounded-md" required>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">Type</label>
                    <select name="subAgentType_${subAgentId}" class="w-full p-2 text-sm border border-gray-300 rounded-md">
                        <option value="llm">LLM Agent</option>
                        <option value="sequential">Sequential Agent</option>
                        <option value="parallel">Parallel Agent</option>
                        <option value="loop">Loop Agent</option>
                    </select>
                </div>
                <div class="md:col-span-2">
                    <label class="block text-xs font-medium text-gray-700 mb-1">Description</label>
                    <textarea name="subAgentDescription_${subAgentId}" rows="2" class="w-full p-2 text-sm border border-gray-300 rounded-md"></textarea>
                </div>
                <div class="md:col-span-2">
                    <label class="block text-xs font-medium text-gray-700 mb-1">System Prompt</label>
                    <textarea name="subAgentSystemPrompt_${subAgentId}" rows="2" class="w-full p-2 text-sm border border-gray-300 rounded-md"></textarea>
                </div>
            </div>
        `;
        container.appendChild(subAgentDiv);
        console.log('New sub-agent field added');
    }
    
    confirmSelectExistingAgent() {
        const selectedAgents = Array.from(document.querySelectorAll('#availableAgentsList input:checked')).map(cb => cb.value);
        if (selectedAgents.length === 0) {
            this.showMessage('Please select at least one agent', 'error');
            return;
        }
        
        // Add selected agents to the existing sub-agents selection
        this.addSelectedAgentsToSelection(selectedAgents);
        
        // Show success message with count
        const agentNames = selectedAgents.map(id => this.agents.find(a => a.id === id)?.name).filter(Boolean);
        this.showMessage(`Added ${selectedAgents.length} sub-agent(s): ${agentNames.join(', ')}`, 'success');
        
        this.hideModal('selectExistingAgentModal');
    }
    
    async showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.classList.remove('hidden');
        }
        
        // Update navigation active state
        document.querySelectorAll('[data-section]').forEach(btn => {
            btn.classList.remove('bg-primary', 'text-white');
            btn.classList.add('text-gray-600', 'hover:text-gray-900');
        });
        
        const activeBtn = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('text-gray-600', 'hover:text-gray-900');
            activeBtn.classList.add('bg-primary', 'text-white');
        }
        
        // Load section-specific data
        if (sectionName === 'agents') {
            // Reload agents data and then render
            await this.loadAgents();
            this.renderAgentsGrid();
        } else if (sectionName === 'tools') {
            // Reload tools data and then render
            await this.loadTools();
            this.renderToolsGrid();
        } else if (sectionName === 'projects') {
            this.renderProjectsGrid();
        } else if (sectionName === 'sub-agents') {
            // Special handling for sub-agents section
            await this.populateParentAgentSelect();
            await this.populateExistingAgentSelect();
        }
    }
    
    showModal(modalId) {
        document.getElementById(modalId)?.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
        
        // Populate tools selection if opening agent modal
        if (modalId === 'agentModal') {
            this.populateAgentToolsSelection();
        }
        
        // Show function code section by default when opening tool modal
        if (modalId === 'toolModal') {
            const functionSection = document.getElementById('functionCodeSection');
            const toolType = document.getElementById('toolType');
            
            // Since "function" is the default value, show the section
            if (functionSection && toolType?.value === 'function') {
                functionSection.classList.remove('hidden');
            }
        }
    }
    
    hideModal(modalId) {
        document.getElementById(modalId)?.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        
        // Reset forms when closing modals
        if (modalId === 'toolModal') {
            const form = document.getElementById('toolForm');
            if (form) {
                form.reset();
                // Hide function code section after reset
                const functionSection = document.getElementById('functionCodeSection');
                if (functionSection) {
                    functionSection.classList.add('hidden');
                }
            }
        } else if (modalId === 'agentModal') {
            const form = document.getElementById('agentConfigForm');
            if (form) {
                form.reset();
            }
        } else if (modalId === 'projectModal') {
            const form = document.getElementById('projectForm');
            if (form) {
                form.reset();
            }
        }
    }
    
    hideAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.add('hidden');
        });
        document.body.classList.remove('overflow-hidden');
    }
    
    async loadInitialData() {
        try {
            this.showLoading(true);
            await Promise.all([
                this.loadAgents(),
                this.loadTools(),
                this.loadProjects()
            ]);
            this.updateDashboardStats();
            this.updateUserDisplay();
            this.showLoading(false);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showMessage('Error loading data. Please refresh the page.', 'error');
            this.showLoading(false);
        }
    }
    
    updateUserDisplay() {
        // Update user display name from localStorage
        const userEmail = localStorage.getItem('userEmail');
        const userDisplayName = document.getElementById('userDisplayName');
        const userAvatar = document.querySelector('#userMenuBtn .h-8.w-8 span');
        
        if (userEmail && userDisplayName) {
            // Extract name from email (before @ symbol)
            const name = userEmail.split('@')[0];
            // Capitalize first letter
            const displayName = name.charAt(0).toUpperCase() + name.slice(1);
            userDisplayName.textContent = displayName;
            
            // Update avatar initial
            if (userAvatar) {
                userAvatar.textContent = displayName.charAt(0).toUpperCase();
            }
        }
    }
    
    updateDashboardStats() {
        const agentCount = document.getElementById('agentCount');
        const toolCount = document.getElementById('toolCount');
        const projectCount = document.getElementById('projectCount');
        const chatCount = document.getElementById('chatCount');
        
        if (agentCount) agentCount.textContent = this.agents.length;
        if (toolCount) toolCount.textContent = this.tools.length;
        if (projectCount) projectCount.textContent = this.projects.length;
        if (chatCount) chatCount.textContent = '0'; // Could be enhanced to show actual chat sessions
        
        // Update recent agents and tools sections
        this.updateRecentAgents();
        this.updateRecentTools();
    }
    
    updateRecentAgents() {
        const container = document.getElementById('recentAgents');
        if (!container) return;
        
        if (this.agents.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <i class="fas fa-robot text-2xl mb-2"></i>
                    <p class="text-sm">No agents created yet</p>
                    <button onclick="app.showSection('agents').catch(console.error)" class="text-primary hover:text-primary/80 text-sm mt-2">
                        Create your first agent →
                    </button>
                </div>
            `;
            return;
        }
        
        // Show up to 3 recent agents
        const recentAgents = this.agents.slice(0, 3);
        container.innerHTML = recentAgents.map(agent => `
            <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div class="h-8 w-8 bg-blue-100 rounded-lg flex items-center justify-center">
                    <i class="fas fa-robot text-blue-600"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${agent.name}</p>
                    <p class="text-xs text-gray-500 truncate">${agent.description || 'No description'}</p>
                </div>
                <button onclick="app.startChat('${agent.id}')" class="text-blue-500 hover:text-blue-700 p-1">
                    <i class="fas fa-comments text-sm"></i>
                </button>
            </div>
        `).join('');
        
        if (this.agents.length > 3) {
            container.innerHTML += `
                <div class="text-center pt-2">
                                            <button onclick="app.showSection('agents').catch(console.error)" class="text-primary hover:text-primary/80 text-sm">
                            View all ${this.agents.length} agents →
                        </button>
                </div>
            `;
        }
    }
    
    updateRecentTools() {
        const container = document.getElementById('recentTools');
        if (!container) return;
        
        if (this.tools.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <i class="fas fa-tools text-2xl mb-2"></i>
                    <p class="text-sm">No tools created yet</p>
                    <button onclick="app.showSection('tools').catch(console.error)" class="text-primary hover:text-primary/80 text-sm mt-2">
                        Create your first tool →
                    </button>
                </div>
            `;
            return;
        }
        
        // Show up to 3 recent tools
        const recentTools = this.tools.slice(0, 3);
        container.innerHTML = recentTools.map(tool => `
            <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div class="h-8 w-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <i class="fas fa-tools text-green-600"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${tool.name}</p>
                    <p class="text-xs text-gray-500 truncate">${tool.description || 'No description'}</p>
                </div>
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    ${tool.tool_type}
                </span>
            </div>
        `).join('');
        
        if (this.tools.length > 3) {
            container.innerHTML += `
                <div class="text-center pt-2">
                                            <button onclick="app.showSection('tools').catch(console.error)" class="text-primary hover:text-primary/80 text-sm">
                            View all ${this.tools.length} tools →
                        </button>
                </div>
            `;
        }
    }
    
    async checkADKStatus() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            const statusElement = document.getElementById('adkStatus');
            if (statusElement) {
                const indicator = statusElement.querySelector('div');
                const text = statusElement.querySelector('span');
                
                if (data.adk_available) {
                    indicator.className = 'w-3 h-3 rounded-full status-indicator online';
                    text.textContent = 'ADK Available';
                } else {
                    indicator.className = 'w-3 h-3 rounded-full status-indicator offline';
                    text.textContent = 'ADK Not Available';
                }
            }
        } catch (error) {
            console.error('Error checking ADK status:', error);
            const statusElement = document.getElementById('adkStatus');
            if (statusElement) {
                const indicator = statusElement.querySelector('div');
                const text = statusElement.querySelector('span');
                
                indicator.className = 'w-3 h-3 rounded-full status-indicator offline';
                text.textContent = 'Connection Error';
            }
        }
        
        // Check for notifications (simulate for demo)
        this.checkNotifications();
    }
    
    checkNotifications() {
        // For demo purposes, randomly show/hide notification dot
        // In production, this would check actual notifications
        const notificationDot = document.getElementById('notificationDot');
        if (notificationDot) {
            // Simulate notifications - you can replace this with actual logic
            const hasNotifications = Math.random() > 0.7; // 30% chance of having notifications
            if (hasNotifications) {
                notificationDot.classList.remove('hidden');
            } else {
                notificationDot.classList.add('hidden');
            }
        }
    }
    
    handleNotifications() {
        // Clear notification dot when bell is clicked
        const notificationDot = document.getElementById('notificationDot');
        if (notificationDot) {
            notificationDot.classList.add('hidden');
            this.showMessage('Notifications cleared', 'info');
        }
    }
    
    async loadAgents() {
        try {
            console.log('Loading agents...');
            const response = await fetch('/api/agents');
            console.log('Agents response status:', response.status);
            const data = await response.json();
            console.log('Agents response data:', data);
            this.agents = data.agents || [];
            console.log('Agents loaded:', this.agents);
            this.updateChatAgentSelect();
        } catch (error) {
            console.error('Error loading agents:', error);
        }
    }
    
    async loadTools() {
        try {
            console.log('Loading tools...');
            const response = await fetch('/api/tools');
            console.log('Tools response status:', response.status);
            const data = await response.json();
            console.log('Tools response data:', data);
            this.tools = data.tools || [];
            console.log('Tools loaded:', this.tools);
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
    
    renderAgentsGrid() {
        console.log('Rendering agents grid...');
        console.log('Agents to render:', this.agents);
        const container = document.getElementById('agentsGrid');
        if (!container) {
            console.error('Agents grid container not found!');
            return;
        }
        
        container.innerHTML = '';
        
        if (this.agents.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 mb-4">
                        <i class="fas fa-robot text-6xl"></i>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No agents created yet</h3>
                    <p class="text-gray-500 mb-4">Create your first AI agent to get started</p>
                    <button onclick="app.showModal('agentModal')" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
                        <i class="fas fa-plus mr-2"></i>Create Agent
                    </button>
                </div>
            `;
            return;
        }
        
        this.agents.forEach(agent => {
            const agentElement = this.createAgentCard(agent);
            container.appendChild(agentElement);
        });
    }
    
    createAgentCard(agent) {
        const div = document.createElement('div');
        div.className = 'bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow';
        
        div.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${agent.name}</h3>
                    <p class="text-sm text-gray-600 mb-3">${agent.description}</p>
                    <div class="flex items-center space-x-2 mb-3">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${agent.agent_type}
                        </span>
                        ${(agent.tags || []).map(tag => `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                ${tag}
                            </span>
                        `).join('')}
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="text-blue-500 hover:text-blue-700 p-2 rounded-lg hover:bg-blue-50 transition-colors" onclick="app.editAgent('${agent.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-green-500 hover:text-green-700 p-2 rounded-lg hover:bg-green-50 transition-colors" onclick="app.startChat('${agent.id}')">
                        <i class="fas fa-comments"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 transition-colors" onclick="app.deleteAgent('${agent.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    renderToolsGrid() {
        console.log('Rendering tools grid...');
        console.log('Tools to render:', this.tools);
        const container = document.getElementById('toolsGrid');
        if (!container) {
            console.error('Tools grid container not found!');
            return;
        }
        
        container.innerHTML = '';
        
        if (this.tools.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 mb-4">
                        <i class="fas fa-tools text-6xl"></i>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No tools created yet</h3>
                    <p class="text-gray-500 mb-4">Create your first tool to extend agent capabilities</p>
                    <button onclick="app.showModal('toolModal')" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
                        <i class="fas fa-plus mr-2"></i>Create Tool
                    </button>
                </div>
            `;
            return;
        }
        
        this.tools.forEach(tool => {
            const toolElement = this.createToolCard(tool);
            container.appendChild(toolElement);
        });
    }
    
    createToolCard(tool) {
        const div = document.createElement('div');
        div.className = 'bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow';
        
        div.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${tool.name}</h3>
                    <p class="text-sm text-gray-600 mb-3">${tool.description}</p>
                    <div class="flex items-center space-x-2">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            ${tool.tool_type}
                        </span>
                        ${(tool.tags || []).map(tag => `
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                ${tag}
                            </span>
                        `).join('')}
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="text-blue-500 hover:text-blue-700 p-2 rounded-lg hover:bg-blue-50 transition-colors" onclick="app.editTool('${tool.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 transition-colors" onclick="app.deleteTool('${tool.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    renderProjectsGrid() {
        const container = document.getElementById('projectsGrid');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (this.projects.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="text-gray-400 mb-4">
                        <i class="fas fa-project-diagram text-6xl"></i>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No projects created yet</h3>
                    <p class="text-gray-500 mb-4">Create your first project to organize your agents and tools</p>
                    <button onclick="app.showModal('projectModal')" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
                        <i class="fas fa-plus mr-2"></i>Create Project
                    </button>
                </div>
            `;
            return;
        }
        
        this.projects.forEach(project => {
            const projectElement = this.createProjectCard(project);
            container.appendChild(projectElement);
        });
    }
    
    createProjectCard(project) {
        const div = document.createElement('div');
        div.className = 'bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow';
        
        div.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${project.name}</h3>
                    <p class="text-sm text-gray-600 mb-3">${project.description}</p>
                    <div class="flex items-center space-x-2">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            ${project.agents?.length || 0} agents
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            ${project.tools?.length || 0} tools
                        </span>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button class="text-blue-500 hover:text-blue-700 p-2 rounded-lg hover:bg-blue-50 transition-colors" onclick="app.editProject('${project.id}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 transition-colors" onclick="app.deleteProject('${project.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        return div;
    }
    
    updateChatAgentSelect() {
        const select = document.getElementById('chatAgentSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select an agent to chat with...</option>';
        
        this.agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.id;
            option.textContent = agent.name;
            select.appendChild(option);
        });
    }
    
    async startChat(agentId) {
        this.currentAgent = this.agents.find(a => a.id === agentId);
        this.currentSession = null;
        this.clearChat();
        this.showMessage(`Selected agent: ${this.currentAgent.name}`, 'info');
        await this.showSection('chat');
        this.selectChatAgent({ target: { value: agentId } });
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
    
    async handleAgentSubmit(e) {
        e.preventDefault();
        console.log('Agent form submitted');
        
        const formData = new FormData(e.target);
        console.log('Form data:', Object.fromEntries(formData));
        
        // Generate a unique ID for new agents
        const agentId = this.currentAgent?.id || this.generateAgentId();
        
        // Collect sub-agent data
        const existingSubAgents = Array.from(document.querySelectorAll('#existingSubAgentsSelection input:checked')).map(cb => cb.value);
        const newSubAgents = this.collectNewSubAgentsData();
        
        const agentData = {
            id: agentId,
            name: formData.get('agentName'),
            description: formData.get('agentDescription'),
            agent_type: formData.get('agentType'),
            system_prompt: formData.get('agentSystemPrompt'),
            instructions: formData.get('agentInstructions') || '',
            model_settings: {
                model: document.getElementById('agentModel')?.value || 'gemini-2.0-flash',
                temperature: parseFloat(document.getElementById('agentTemperature')?.value || '0.7'),
                max_tokens: parseInt(document.getElementById('agentMaxTokens')?.value || '1000')
            },
            tools: Array.from(document.querySelectorAll('#agentToolsSelection input:checked')).map(cb => cb.value),
            sub_agents: {
                existing: existingSubAgents,
                new: newSubAgents
            },
            tags: []
        };
        
        console.log('Agent data to send:', agentData);
        
        try {
            this.showLoading(true);
            const url = this.currentAgent ? `/api/agents/${this.currentAgent.id}` : '/api/agents';
            const method = this.currentAgent ? 'PUT' : 'POST';
            
            console.log('Sending request to:', url, 'with method:', method);
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentData)
            });
            
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log('Success response:', result);
                this.showMessage(`Agent ${this.currentAgent ? 'updated' : 'created'} successfully!`, 'success');
                await this.loadAgents();
                this.hideModal('agentModal');
                this.renderAgentsGrid();
                this.updateDashboardStats();
            } else {
                const error = await response.json();
                console.error('Error response:', error);
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error saving agent:', error);
            this.showMessage('Error saving agent', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleToolSubmit(e) {
        e.preventDefault();
        
        const toolType = document.getElementById('toolType').value;
        const functionCode = document.getElementById('toolFunctionCode')?.value;
        
        // Validate function code is provided for function tools
        if (toolType === 'function' && !functionCode?.trim()) {
            this.showMessage('Function code is required for function tools', 'error');
            return;
        }
        
        const toolData = {
            id: document.getElementById('toolId').value,
            name: document.getElementById('toolName').value,
            description: document.getElementById('toolDescription').value,
            tool_type: toolType,
            function_code: functionCode || null,
            tags: []
        };
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(toolData)
            });
            
            if (response.ok) {
                this.showMessage('Tool created successfully!', 'success');
                await this.loadTools();
                this.hideModal('toolModal');
                this.renderToolsGrid();
                this.updateDashboardStats();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error creating tool:', error);
            this.showMessage('Error creating tool', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async handleProjectSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const projectData = {
            name: formData.get('projectName'),
            description: formData.get('projectDescription'),
            agents: [],
            tools: []
        };
        
        try {
            this.showLoading(true);
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
            
            if (response.ok) {
                this.showMessage('Project created successfully!', 'success');
                await this.loadProjects();
                this.hideModal('projectModal');
                this.renderProjectsGrid();
                this.updateDashboardStats();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            this.showMessage('Error creating project', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    handleToolTypeChange(e) {
        const functionSection = document.getElementById('functionCodeSection');
        if (functionSection) {
            if (e.target.value === 'function') {
                functionSection.classList.remove('hidden');
            } else {
                functionSection.classList.add('hidden');
            }
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
            this.showLoading(true);
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
        } finally {
            this.showLoading(false);
        }
    }
    
    addChatMessage(role, content) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-4 ${role === 'user' ? 'text-right' : 'text-left'}`;
        
        const bubble = document.createElement('div');
        bubble.className = `inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            role === 'user' 
                ? 'bg-primary text-white ml-auto' 
                : role === 'assistant' 
                    ? 'bg-gray-100 text-gray-900' 
                    : 'bg-red-100 text-red-900'
        }`;
        bubble.textContent = content;
        
        messageDiv.appendChild(bubble);
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    clearChat() {
        const container = document.getElementById('chatMessages');
        if (container) {
            container.innerHTML = '<div class="text-center text-gray-500 py-8">Select an agent to start chatting</div>';
        }
    }
    
    async deleteAgent(agentId) {
        if (!confirm('Are you sure you want to delete this agent?')) return;
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/agents/${agentId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.showMessage('Agent deleted successfully!', 'success');
                await this.loadAgents();
                this.renderAgentsGrid();
                this.updateDashboardStats();
            } else {
                this.showMessage('Error deleting agent', 'error');
            }
        } catch (error) {
            console.error('Error deleting agent:', error);
            this.showMessage('Error deleting agent', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteTool(toolId) {
        if (!confirm('Are you sure you want to delete this tool?')) return;
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/tools/${toolId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.showMessage('Tool deleted successfully!', 'success');
                await this.loadTools();
                this.renderToolsGrid();
                this.updateDashboardStats();
            } else {
                this.showMessage('Error deleting tool', 'error');
            }
        } catch (error) {
            console.error('Error deleting tool:', error);
            this.showMessage('Error deleting tool', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    async deleteProject(projectId) {
        if (!confirm('Are you sure you want to delete this project?')) return;
        
        try {
            this.showLoading(true);
            const response = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
            
            if (response.ok) {
                this.showMessage('Project deleted successfully!', 'success');
                await this.loadProjects();
                this.renderProjectsGrid();
                this.updateDashboardStats();
            } else {
                this.showMessage('Error deleting project', 'error');
            }
        } catch (error) {
            console.error('Error deleting project:', error);
            this.showMessage('Error deleting project', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    editAgent(agentId) {
        this.currentAgent = this.agents.find(a => a.id === agentId);
        if (this.currentAgent) {
            this.populateAgentForm(this.currentAgent);
            this.showModal('agentModal');
        }
    }
    
    editTool(toolId) {
        // Implementation for editing tools
        this.showMessage('Tool editing coming soon!', 'info');
    }
    
    editProject(projectId) {
        // Implementation for editing projects
        this.showMessage('Project editing coming soon!', 'info');
    }
    
    populateAgentForm(agent) {
        const nameField = document.getElementById('agentName');
        const typeField = document.getElementById('agentType');
        const descField = document.getElementById('agentDescription');
        const promptField = document.getElementById('agentSystemPrompt');
        const instructionsField = document.getElementById('agentInstructions');
        const modelField = document.getElementById('agentModel');
        const tempField = document.getElementById('agentTemperature');
        const maxTokensField = document.getElementById('agentMaxTokens');
        
        if (nameField) nameField.value = agent.name;
        if (typeField) typeField.value = agent.agent_type;
        if (descField) descField.value = agent.description;
        if (promptField) promptField.value = agent.system_prompt;
        if (instructionsField) instructionsField.value = agent.instructions || '';
        if (modelField) modelField.value = agent.model_settings?.model || 'gemini-2.0-flash';
        if (tempField) tempField.value = agent.model_settings?.temperature || 0.7;
        if (maxTokensField) maxTokensField.value = agent.model_settings?.max_tokens || 1000;
        
        // Update temperature display
        const tempValue = document.getElementById('temperatureValue');
        if (tempValue) tempValue.textContent = agent.model_settings?.temperature || 0.7;
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.toggle('hidden', !show);
        }
    }
    
    showMessage(message, type = 'info') {
        const container = document.getElementById('messageContainer');
        if (!container) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-4 p-4 rounded-lg max-w-sm ${
            type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
            type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
            'bg-blue-100 text-blue-800 border border-blue-200'
        }`;
        
        messageDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        container.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    logout() {
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userEmail');
        window.location.href = '/login';
    }
    
    generateAgentId() {
        // Generate a unique ID for new agents
        const timestamp = Date.now();
        const random = Math.random().toString(36).substring(2, 8);
        return `agent_${timestamp}_${random}`;
    }
    
    populateAgentToolsSelection() {
        const container = document.getElementById('agentToolsSelection');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (this.tools.length === 0) {
            container.innerHTML = '<p class="text-sm text-gray-500">No tools available. Create tools first.</p>';
            return;
        }
        
        this.tools.forEach(tool => {
            const div = document.createElement('div');
            div.className = 'flex items-center space-x-2 mb-2';
            
            div.innerHTML = `
                <input type="checkbox" id="tool_${tool.id}" value="${tool.id}" class="rounded">
                <label for="tool_${tool.id}" class="text-sm text-gray-700">${tool.name}</label>
            `;
            
            container.appendChild(div);
        });
    }
    
    // AI Suggestion Methods (keeping existing functionality)
    async suggestAgentName() {
        const description = document.getElementById('agentDescription')?.value;
        if (!description?.trim()) {
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
                const nameField = document.getElementById('agentName');
                if (nameField) nameField.value = data.suggestion;
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
        const name = document.getElementById('agentName')?.value;
        const agentType = document.getElementById('agentType')?.value;
        
        if (!name?.trim()) {
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
                const descField = document.getElementById('agentDescription');
                if (descField) descField.value = data.suggestion;
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
        const name = document.getElementById('agentName')?.value;
        const description = document.getElementById('agentDescription')?.value;
        const agentType = document.getElementById('agentType')?.value;
        
        if (!name?.trim() || !description?.trim()) {
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
                const promptField = document.getElementById('agentSystemPrompt');
                if (promptField) promptField.value = data.suggestion;
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
        const description = document.getElementById('toolDescription')?.value;
        const toolType = document.getElementById('toolType')?.value;
        
        if (!description?.trim()) {
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
                const nameField = document.getElementById('toolName');
                if (nameField) nameField.value = data.suggestion;
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
        const name = document.getElementById('toolName')?.value;
        const toolType = document.getElementById('toolType')?.value;
        
        if (!name?.trim()) {
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
                const descField = document.getElementById('toolDescription');
                if (descField) descField.value = data.suggestion;
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
        const name = document.getElementById('toolName')?.value;
        const description = document.getElementById('toolDescription')?.value;
        const toolType = document.getElementById('toolType')?.value;
        
        if (!name?.trim() || !description?.trim()) {
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
                const codeField = document.getElementById('toolFunctionCode');
                if (codeField) codeField.value = data.suggestion;
                this.showMessage('AI code suggestion applied!', 'success');
            } else {
                this.showMessage('Failed to get AI code suggestion', 'error');
            }
        } catch (error) {
            console.error('Error getting tool code suggestion:', error);
            this.showMessage('Error getting AI code suggestion', 'error');
        }
    }
    
    async generateToolCode() {
        const name = document.getElementById('toolName')?.value;
        const description = document.getElementById('toolDescription')?.value;
        const toolType = document.getElementById('toolType')?.value;
        
        if (!name?.trim() || !description?.trim()) {
            this.showMessage('Please enter both name and description first to generate code', 'warning');
            return;
        }
        
        if (toolType !== 'function') {
            this.showMessage('Code generation is only available for function tools', 'warning');
            return;
        }
        
        try {
            this.showLoading(true);
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
                const codeField = document.getElementById('toolFunctionCode');
                if (codeField) {
                    codeField.value = data.suggestion;
                    this.showMessage('Python code generated successfully!', 'success');
                }
            } else {
                this.showMessage('Failed to generate Python code', 'error');
            }
        } catch (error) {
            console.error('Error generating tool code:', error);
            this.showMessage('Error generating Python code', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // Sub-Agent Management Methods
    async loadSubAgentsForAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/sub-agents`);
            const data = await response.json();
            return data.sub_agents || [];
        } catch (error) {
            console.error('Error loading sub-agents:', error);
            return [];
        }
    }

    async loadAvailableAgentsForSub() {
        try {
            const response = await fetch('/api/agents/available-for-sub');
            const data = await response.json();
            return data.agents || [];
        } catch (error) {
            console.error('Error loading available agents for sub:', error);
            return [];
        }
    }

    async onParentAgentChange(event) {
        const agentId = event.target.value;
        if (!agentId) {
            this.renderSubAgentsList([]);
            return;
        }

        try {
            const subAgents = await this.loadSubAgentsForAgent(agentId);
            this.renderSubAgentsList(subAgents);
        } catch (error) {
            console.error('Error loading sub-agents:', error);
            this.showMessage('Error loading sub-agents', 'error');
        }
    }

    renderSubAgentsList(subAgents) {
        const container = document.getElementById('subAgentsList');
        if (!container) return;

        if (subAgents.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-sitemap text-4xl mb-4"></i>
                    <p>No sub-agents found for this agent</p>
                    <p class="text-sm">Use the buttons above to add sub-agents</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        subAgents.forEach(subAgent => {
            const subAgentElement = this.createSubAgentCard(subAgent);
            container.appendChild(subAgentElement);
        });
    }

    createSubAgentCard(subAgent) {
        const div = document.createElement('div');
        div.className = 'bg-gray-50 rounded-lg p-4 border border-gray-200';
        
        div.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1">
                    <h4 class="font-medium text-gray-900 mb-1">${subAgent.name}</h4>
                    <p class="text-sm text-gray-600 mb-2">${subAgent.description || 'No description'}</p>
                    <div class="flex items-center space-x-2">
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${subAgent.agent_type || 'unknown'}
                        </span>
                        ${subAgent.is_enabled ? 
                            '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">Enabled</span>' :
                            '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">Disabled</span>'
                        }
                    </div>
                </div>
                <button onclick="app.removeSubAgent('${subAgent.id}')" class="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors" title="Remove sub-agent">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        return div;
    }

    async handleSubAgentSubmit(event) {
        event.preventDefault();
        
        const parentAgentId = document.getElementById('parentAgentSelect')?.value;
        if (!parentAgentId) {
            this.showMessage('Please select a parent agent first', 'warning');
            return;
        }

        const formData = {
            name: document.getElementById('subAgentName')?.value,
            description: document.getElementById('subAgentDescription')?.value,
            agent_type: document.getElementById('subAgentType')?.value,
            system_prompt: document.getElementById('subAgentSystemPrompt')?.value,
            is_enabled: true
        };

        try {
            this.showLoading(true);
            const response = await fetch(`/api/agents/${parentAgentId}/sub-agents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showMessage('Sub-agent added successfully!', 'success');
                this.hideModal('subAgentModal');
                this.resetSubAgentForm();
                
                // Refresh sub-agents list
                const subAgents = await this.loadSubAgentsForAgent(parentAgentId);
                this.renderSubAgentsList(subAgents);
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail || 'Failed to add sub-agent'}`, 'error');
            }
        } catch (error) {
            console.error('Error adding sub-agent:', error);
            this.showMessage('Error adding sub-agent', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async handleLinkExistingAgentSubmit(event) {
        event.preventDefault();
        
        const parentAgentId = document.getElementById('parentAgentSelect')?.value;
        const existingAgentId = document.getElementById('existingAgentSelect')?.value;
        
        if (!parentAgentId) {
            this.showMessage('Please select a parent agent first', 'warning');
            return;
        }
        
        if (!existingAgentId) {
            this.showMessage('Please select an agent to link', 'warning');
            return;
        }

        try {
            this.showLoading(true);
            const response = await fetch(`/api/agents/${parentAgentId}/sub-agents/from-existing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source_agent_id: existingAgentId })
            });

            if (response.ok) {
                this.showMessage('Agent linked as sub-agent successfully!', 'success');
                this.hideModal('linkExistingAgentModal');
                this.resetLinkExistingAgentForm();
                
                // Refresh sub-agents list
                const subAgents = await this.loadSubAgentsForAgent(parentAgentId);
                this.renderSubAgentsList(subAgents);
                
                // Refresh available agents dropdown
                this.populateExistingAgentSelect();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail || 'Failed to link agent'}`, 'error');
            }
        } catch (error) {
            console.error('Error linking agent:', error);
            this.showMessage('Error linking agent', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async removeSubAgent(subAgentId) {
        const parentAgentId = document.getElementById('parentAgentSelect')?.value;
        if (!parentAgentId) {
            this.showMessage('No parent agent selected', 'warning');
            return;
        }

        if (!confirm('Are you sure you want to remove this sub-agent?')) return;

        try {
            this.showLoading(true);
            const response = await fetch(`/api/agents/${parentAgentId}/sub-agents/${subAgentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showMessage('Sub-agent removed successfully!', 'success');
                
                // Refresh sub-agents list
                const subAgents = await this.loadSubAgentsForAgent(parentAgentId);
                this.renderSubAgentsList(subAgents);
                
                // Refresh available agents dropdown
                this.populateExistingAgentSelect();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail || 'Failed to remove sub-agent'}`, 'error');
            }
        } catch (error) {
            console.error('Error removing sub-agent:', error);
            this.showMessage('Error removing sub-agent', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    resetSubAgentForm() {
        document.getElementById('subAgentForm')?.reset();
    }

    resetLinkExistingAgentForm() {
        document.getElementById('linkExistingAgentForm')?.reset();
    }

    async populateExistingAgentSelect() {
        const select = document.getElementById('existingAgentSelect');
        if (!select) return;

        try {
            const availableAgents = await this.loadAvailableAgentsForSub();
            
            // Clear existing options
            select.innerHTML = '<option value="">Choose an agent...</option>';
            
            // Add available agents
            availableAgents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = `${agent.name} - ${agent.description}`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error populating existing agent select:', error);
        }
    }

    async populateParentAgentSelect() {
        const select = document.getElementById('parentAgentSelect');
        if (!select) return;

        try {
            // Clear existing options
            select.innerHTML = '<option value="">Choose an agent...</option>';
            
            // Add all agents
            this.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent.id;
                option.textContent = agent.name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error populating parent agent select:', error);
        }
    }
    
    // Sub-agent functionality in agent modal
    addSelectedAgentsToSelection(selectedAgentIds) {
        const container = document.getElementById('existingSubAgentsSelection');
        if (!container) return;
        
        // Check if agents are already selected to avoid duplicates
        const existingSelections = Array.from(container.querySelectorAll('input[type="checkbox"]')).map(cb => cb.value);
        
        selectedAgentIds.forEach(agentId => {
            // Skip if already selected
            if (existingSelections.includes(agentId)) {
                return;
            }
            
            const agent = this.agents.find(a => a.id === agentId);
            if (agent) {
                const agentDiv = document.createElement('div');
                agentDiv.className = 'flex items-center p-3 border border-blue-200 rounded-md mb-2 bg-blue-50 hover:bg-blue-100 transition-colors';
                agentDiv.innerHTML = `
                    <input type="checkbox" name="existingSubAgent_${agentId}" value="${agentId}" checked class="mr-3 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500">
                    <label class="flex-1">
                        <div class="font-medium text-gray-900">${agent.name}</div>
                        <div class="text-sm text-gray-600">${agent.description || 'No description'}</div>
                        <div class="flex items-center space-x-2 mt-1">
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${agent.agent_type || 'unknown'}
                            </span>
                            ${agent.tools && agent.tools.length > 0 ? 
                                `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    ${agent.tools.length} tools
                                </span>` : ''
                            }
                        </div>
                    </label>
                    <button type="button" onclick="this.remove()" class="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors" title="Remove sub-agent">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                container.appendChild(agentDiv);
            }
        });
        
        // Update the selection count display
        this.updateSubAgentSelectionCount();
    }
    
    clearAllSubAgentSelections() {
        const existingContainer = document.getElementById('existingSubAgentsSelection');
        const newContainer = document.getElementById('newSubAgentsContainer');
        
        if (existingContainer) {
            existingContainer.innerHTML = '';
        }
        
        if (newContainer) {
            newContainer.innerHTML = '';
        }
        
        // Update counts
        this.updateSubAgentSelectionCount();
        this.updateNewSubAgentCount();
        
        this.showMessage('All sub-agent selections cleared', 'info');
    }
    
    updateSubAgentSelectionCount() {
        const container = document.getElementById('existingSubAgentsSelection');
        if (!container) return;
        
        const selectedCount = container.querySelectorAll('input[type="checkbox"]').length;
        const headerElement = container.previousElementSibling;
        
        if (headerElement && headerElement.querySelector('.sub-agent-count')) {
            headerElement.querySelector('.sub-agent-count').textContent = selectedCount;
        }
    }
    
    updateNewSubAgentCount() {
        const container = document.getElementById('newSubAgentsContainer');
        if (!container) return;
        
        const newSubAgentCount = container.querySelectorAll('div').length;
        const headerElement = container.previousElementSibling;
        
        if (headerElement && headerElement.querySelector('.new-sub-agent-count')) {
            headerElement.querySelector('.new-sub-agent-count').textContent = newSubAgentCount;
        }
    }
    
    collectNewSubAgentsData() {
        const newSubAgents = [];
        const newSubAgentDivs = document.querySelectorAll('#newSubAgentsContainer > div');
        
        newSubAgentDivs.forEach(div => {
            const nameInput = div.querySelector('input[name^="subAgentName_"]');
            const typeSelect = div.querySelector('select[name^="subAgentType_"]');
            const descriptionTextarea = div.querySelector('textarea[name^="subAgentDescription_"]');
            const systemPromptTextarea = div.querySelector('textarea[name^="subAgentSystemPrompt_"]');
            
            if (nameInput && nameInput.value.trim()) {
                newSubAgents.push({
                    id: `new_sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    name: nameInput.value.trim(),
                    agent_type: typeSelect ? typeSelect.value : 'llm',
                    description: descriptionTextarea ? descriptionTextarea.value.trim() : '',
                    system_prompt: systemPromptTextarea ? systemPromptTextarea.value.trim() : '',
                    is_enabled: true,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                });
            }
        });
        
        console.log('Collected new sub-agents data:', newSubAgents);
        return newSubAgents;
    }
    

}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing AgentGeniePlatform...');
    try {
        window.app = new AgentGeniePlatform();
        console.log('AgentGeniePlatform initialized successfully');
        
        // Test if the create tool button exists
        const createToolBtn = document.getElementById('createToolBtn');
        console.log('Create Tool Button found:', createToolBtn);
        
        if (createToolBtn) {
            console.log('Button text:', createToolBtn.textContent);
            console.log('Button classes:', createToolBtn.className);
        }
        
    } catch (error) {
        console.error('Error initializing AgentGeniePlatform:', error);
    }
});
