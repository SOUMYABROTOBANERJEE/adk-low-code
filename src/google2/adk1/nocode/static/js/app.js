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
        this.bindEmbedEvents(); // Bind embed functionality
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
        document.getElementById('dashboardStartChatBtn')?.addEventListener('click', async () => {
            await this.showSection('chat');
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
        
        // User dropdown functionality
        document.getElementById('userMenuBtn')?.addEventListener('click', (e) => this.toggleUserDropdown(e));
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => this.closeUserDropdown(e));
        
        // Logo click functionality
        document.querySelector('.logo-container')?.addEventListener('click', () => this.handleLogoClick());
        
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
            // Reload projects data and then render
            await this.loadProjects();
            this.renderProjectsGrid();
        } else if (sectionName === 'sub-agents') {
            // Load sub-agents for the selected agent
            this.populateParentAgentSelect();
        } else if (sectionName === 'embeds') {
            // Load embeds for the selected agent
            this.populateEmbedAgentSelect();
            this.loadAgentEmbeds();
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
        
        // Update profile dropdown
        this.updateProfileDropdown();
    }
    
    updateProfileDropdown() {
        const userEmail = localStorage.getItem('userEmail');
        const userName = localStorage.getItem('userName');
        
        if (userEmail) {
            // Update profile info
            const profileName = document.getElementById('profileName');
            const profileEmail = document.getElementById('profileEmail');
            const profileAvatar = document.getElementById('profileAvatar');
            
            if (profileName) {
                profileName.textContent = userName || userEmail.split('@')[0];
            }
            if (profileEmail) {
                profileEmail.textContent = userEmail;
            }
            if (profileAvatar) {
                const initial = (userName || userEmail).charAt(0).toUpperCase();
                profileAvatar.textContent = initial;
            }
        }
        
        // Update usage statistics
        this.updateUsageStatistics();
        
        // Update recent agents
        this.updateRecentAgents();
    }
    
    async updateUsageStatistics() {
        try {
            // Get comprehensive usage statistics from the new API
            const response = await fetch('/api/usage/statistics');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.statistics;
                
                // Update the display with real data from Firestore
                document.getElementById('totalAgents').textContent = stats.total_agents;
                document.getElementById('totalTools').textContent = stats.total_tools;
                document.getElementById('totalProjects').textContent = stats.total_projects;
                document.getElementById('totalChats').textContent = stats.total_chat_sessions;
                
                // Update token consumption display
                this.updateTokenConsumption(stats.agent_token_usage, stats.total_tokens);
            } else {
                // Fallback to individual API calls if the new endpoint fails
                await this.updateUsageStatisticsFallback();
            }
        } catch (error) {
            console.error('Error updating usage statistics:', error);
            // Fallback to individual API calls
            await this.updateUsageStatisticsFallback();
        }
    }
    
    async updateUsageStatisticsFallback() {
        try {
            // Get agents count
            const agentsResponse = await fetch('/api/agents');
            const agentsData = await agentsResponse.json();
            const agentsCount = agentsData.agents ? agentsData.agents.length : 0;
            
            // Get tools count
            const toolsResponse = await fetch('/api/tools');
            const toolsData = await toolsResponse.json();
            const toolsCount = toolsData.tools ? toolsData.tools.length : 0;
            
            // Get projects count
            const projectsResponse = await fetch('/api/projects');
            const projectsData = await projectsResponse.json();
            const projectsCount = projectsData.projects ? projectsData.projects.length : 0;
            
            // Update the display
            document.getElementById('totalAgents').textContent = agentsCount;
            document.getElementById('totalTools').textContent = toolsCount;
            document.getElementById('totalProjects').textContent = projectsCount;
            document.getElementById('totalChats').textContent = '0'; // Placeholder for now
        } catch (error) {
            console.error('Error updating usage statistics fallback:', error);
        }
    }
    
    updateTokenConsumption(agentTokenUsage, totalTokens) {
        // Find or create token consumption section
        let tokenSection = document.getElementById('tokenConsumption');
        if (!tokenSection) {
            // Create token consumption section if it doesn't exist
            const usageSection = document.querySelector('#userDropdown .space-y-4');
            if (usageSection) {
                const tokenHtml = `
                    <div id="tokenConsumption" class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3">
                        <div class="flex items-center justify-between mb-2">
                            <h4 class="text-sm font-medium text-gray-900">Token Usage</h4>
                            <span class="text-xs text-gray-600">${totalTokens.toLocaleString()} total</span>
                        </div>
                        <div id="topAgentsTokens" class="space-y-1">
                            <!-- Top agents by token usage will be populated here -->
                        </div>
                    </div>
                `;
                usageSection.insertAdjacentHTML('beforeend', tokenHtml);
                tokenSection = document.getElementById('tokenConsumption');
            }
        }
        
        if (tokenSection && agentTokenUsage.length > 0) {
            const topAgentsContainer = document.getElementById('topAgentsTokens');
            if (topAgentsContainer) {
                const topAgents = agentTokenUsage.slice(0, 3); // Show top 3 agents
                topAgentsContainer.innerHTML = topAgents.map(agent => `
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-gray-700 truncate">${agent.agent_name}</span>
                        <span class="text-gray-600 font-medium">${agent.total_tokens.toLocaleString()}</span>
                    </div>
                `).join('');
            }
        }
    }
    
    async updateRecentAgents() {
        try {
            // Try to get recent agents from the new usage statistics API first
            const statsResponse = await fetch('/api/usage/statistics');
            const statsData = await statsResponse.json();
            
            let recentAgents = [];
            if (statsData.success && statsData.statistics.recent_agents) {
                recentAgents = statsData.statistics.recent_agents;
            } else {
                // Fallback to the old API
                const response = await fetch('/api/agents');
                const data = await response.json();
                recentAgents = data.agents || [];
            }
            
            const recentAgentsList = document.getElementById('recentAgentsList');
            if (recentAgentsList) {
                if (recentAgents.length === 0) {
                    recentAgentsList.innerHTML = '<div class="text-xs text-gray-500 text-center py-2">No agents created yet</div>';
                } else {
                    // Show up to 5 recent agents with more details
                    const displayAgents = recentAgents.slice(0, 5);
                    recentAgentsList.innerHTML = displayAgents.map(agent => {
                        const statusColor = agent.is_enabled ? 'bg-green-500' : 'bg-gray-400';
                        const createdDate = agent.created_at ? new Date(agent.created_at).toLocaleDateString() : 'Unknown';
                        
                        return `
                            <div class="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer transition-colors" onclick="platform.showSection('agents')">
                                <div class="w-2 h-2 ${statusColor} rounded-full flex-shrink-0"></div>
                                <div class="flex-1 min-w-0">
                                    <div class="text-xs text-gray-700 truncate font-medium">${agent.name}</div>
                                    <div class="text-xs text-gray-500">${createdDate}</div>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }
        } catch (error) {
            console.error('Error updating recent agents:', error);
            const recentAgentsList = document.getElementById('recentAgentsList');
            if (recentAgentsList) {
                recentAgentsList.innerHTML = '<div class="text-xs text-red-500 text-center py-2">Failed to load agents</div>';
            }
        }
    }
    
    async showUsageAnalytics() {
        console.log('Opening usage analytics modal...');
        const modal = document.getElementById('usageAnalyticsModal');
        const loading = document.getElementById('analyticsLoading');
        const content = document.getElementById('analyticsContent');
        
        console.log('Modal elements found:', { modal: !!modal, loading: !!loading, content: !!content });
        
        if (modal) {
            // Show modal immediately
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            modal.style.display = 'flex';
            modal.style.visibility = 'visible';
            
            if (loading) {
                loading.classList.remove('hidden');
                loading.style.display = 'block';
            }
            if (content) {
                content.classList.add('hidden');
                content.style.display = 'none';
            }
            
            try {
                console.log('Fetching usage statistics...');
                // Fetch usage statistics
                const response = await fetch('/api/usage/statistics');
                const data = await response.json();
                
                console.log('Received analytics data:', data);
                
                if (data.success) {
                    this.populateAnalyticsModal(data.statistics);
                    if (loading) {
                        loading.classList.add('hidden');
                        loading.style.display = 'none';
                    }
                    if (content) {
                        content.classList.remove('hidden');
                        content.style.display = 'block';
                    }
                } else {
                    throw new Error('Failed to fetch analytics data');
                }
            } catch (error) {
                console.error('Error loading analytics:', error);
                if (loading) {
                    loading.innerHTML = `
                        <div class="text-center py-8">
                            <i class="fas fa-exclamation-triangle text-2xl text-red-500 mb-4"></i>
                            <p class="text-red-600">Failed to load analytics data</p>
                            <button onclick="app.showUsageAnalytics()" class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
                                Try Again
                            </button>
                        </div>
                    `;
                }
            }
        } else {
            console.error('Usage analytics modal not found');
            this.showMessage('Usage Analytics modal not found. Please refresh the page.', 'error');
        }
    }
    
    closeUsageAnalytics() {
        console.log('Closing usage analytics modal...');
        const modal = document.getElementById('usageAnalyticsModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            modal.style.display = 'none';
            modal.style.visibility = 'hidden';
            console.log('Modal closed successfully');
        } else {
            console.error('Usage analytics modal not found');
        }
    }
    
    showProfileSettings() {
        console.log('Opening profile settings...');
        // For now, show a simple alert. In production, this would open a settings modal
        this.showMessage('Profile Settings - Coming Soon!', 'info');
    }
    
    showHelpSupport() {
        console.log('Opening help & support...');
        // Create and show help accordion modal
        this.createHelpSupportModal();
    }
    
    createHelpSupportModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('helpSupportModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        const modalHtml = `
            <div id="helpSupportModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
                    <div class="flex items-center justify-between p-6 border-b border-gray-200">
                        <h2 class="text-2xl font-bold text-gray-900">Help & Support</h2>
                        <button onclick="app.closeHelpSupport()" class="text-gray-400 hover:text-gray-600 transition-colors">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                    
                    <div class="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
                        <div class="space-y-4">
                            <!-- FAQ Accordion -->
                            <div class="space-y-2">
                                <h3 class="text-lg font-semibold text-gray-900 mb-4">Frequently Asked Questions</h3>
                                
                                <div class="border border-gray-200 rounded-lg">
                                    <button onclick="app.toggleAccordion('faq1')" class="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                                        <span class="font-medium">How do I create a new agent?</span>
                                        <i id="faq1-icon" class="fas fa-chevron-down transition-transform"></i>
                                    </button>
                                    <div id="faq1-content" class="hidden px-4 py-3 border-t border-gray-200">
                                        <p class="text-gray-700">To create a new agent, click on the "Create Agent" button on the dashboard, fill in the agent details, and click "Create Agent". You can also add tools to your agent during creation.</p>
                                    </div>
                                </div>
                                
                                <div class="border border-gray-200 rounded-lg">
                                    <button onclick="app.toggleAccordion('faq2')" class="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                                        <span class="font-medium">How do I add tools to my agent?</span>
                                        <i id="faq2-icon" class="fas fa-chevron-down transition-transform"></i>
                                    </button>
                                    <div id="faq2-content" class="hidden px-4 py-3 border-t border-gray-200">
                                        <p class="text-gray-700">You can add tools to your agent by selecting them in the "Tools" section when creating or editing an agent. Tools provide additional functionality like calculations, API calls, or custom functions.</p>
                                    </div>
                                </div>
                                
                                <div class="border border-gray-200 rounded-lg">
                                    <button onclick="app.toggleAccordion('faq3')" class="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                                        <span class="font-medium">How do I embed an agent on my website?</span>
                                        <i id="faq3-icon" class="fas fa-chevron-down transition-transform"></i>
                                    </button>
                                    <div id="faq3-content" class="hidden px-4 py-3 border-t border-gray-200">
                                        <p class="text-gray-700">To embed an agent, first create and save your agent, then click "Create Embed" in the agent form. Copy the generated embed code and paste it into your website's HTML.</p>
                                    </div>
                                </div>
                                
                                <div class="border border-gray-200 rounded-lg">
                                    <button onclick="app.toggleAccordion('faq4')" class="w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between">
                                        <span class="font-medium">What is token usage?</span>
                                        <i id="faq4-icon" class="fas fa-chevron-down transition-transform"></i>
                                    </button>
                                    <div id="faq4-content" class="hidden px-4 py-3 border-t border-gray-200">
                                        <p class="text-gray-700">Token usage refers to the computational units consumed when your agents process requests. Each message and response consumes tokens, and you can track usage in the Usage Analytics section.</p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Contact Support -->
                            <div class="mt-8 p-4 bg-blue-50 rounded-lg">
                                <h4 class="font-semibold text-blue-900 mb-2">Need More Help?</h4>
                                <p class="text-blue-800 mb-3">If you can't find the answer to your question, please contact our support team:</p>
                                <div class="space-y-2">
                                    <p class="text-blue-700"><i class="fas fa-envelope mr-2"></i>Email: tsl.ai@tatasteel.com</p>
                                    <p class="text-blue-700"><i class="fas fa-phone mr-2"></i>Phone: +91-XXX-XXXX-XXX</p>
                                    <p class="text-blue-700"><i class="fas fa-clock mr-2"></i>Support Hours: Mon-Fri 9AM-6PM IST</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    
    closeHelpSupport() {
        const modal = document.getElementById('helpSupportModal');
        if (modal) {
            modal.remove();
        }
    }
    
    toggleAccordion(faqId) {
        const content = document.getElementById(faqId + '-content');
        const icon = document.getElementById(faqId + '-icon');
        
        if (content && icon) {
            if (content.classList.contains('hidden')) {
                content.classList.remove('hidden');
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                content.classList.add('hidden');
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        }
    }
    
    populateAnalyticsModal(stats) {
        console.log('Populating analytics modal with data:', stats);
        
        // Update overview cards
        const totalAgentsEl = document.getElementById('analyticsTotalAgents');
        const totalToolsEl = document.getElementById('analyticsTotalTools');
        const totalChatsEl = document.getElementById('analyticsTotalChats');
        const totalTokensEl = document.getElementById('analyticsTotalTokens');
        
        if (totalAgentsEl) totalAgentsEl.textContent = stats.total_agents || 0;
        if (totalToolsEl) totalToolsEl.textContent = stats.total_tools || 0;
        if (totalChatsEl) totalChatsEl.textContent = stats.total_chat_sessions || 0;
        if (totalTokensEl) totalTokensEl.textContent = (stats.total_tokens || 0).toLocaleString();
        
        // Populate agent token usage chart
        this.populateAgentTokenChart(stats.agent_token_usage || []);
        
        // Populate recent agents
        this.populateAnalyticsRecentAgents(stats.recent_agents || []);
    }
    
    populateAgentTokenChart(agentTokenUsage) {
        const chartContainer = document.getElementById('agentTokenChart');
        if (!chartContainer || !agentTokenUsage.length) {
            chartContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No token usage data available</p>';
            return;
        }
        
        const maxTokens = Math.max(...agentTokenUsage.map(agent => agent.total_tokens));
        
        chartContainer.innerHTML = agentTokenUsage.map(agent => {
            const percentage = (agent.total_tokens / maxTokens) * 100;
            return `
                <div class="flex items-center space-x-4">
                    <div class="w-32 text-sm text-gray-700 truncate" title="${agent.agent_name}">
                        ${agent.agent_name}
                    </div>
                    <div class="flex-1 bg-gray-200 rounded-full h-6 relative">
                        <div class="bg-gradient-to-r from-blue-500 to-purple-500 h-6 rounded-full transition-all duration-1000 ease-out" 
                             style="width: ${percentage}%"></div>
                        <div class="absolute inset-0 flex items-center justify-center text-xs font-medium text-white">
                            ${agent.total_tokens.toLocaleString()} tokens
                        </div>
                    </div>
                    <div class="w-20 text-sm text-gray-600 text-right">
                        ${agent.chat_sessions} sessions
                    </div>
                </div>
            `;
        }).join('');
    }
    
    populateAnalyticsRecentAgents(recentAgents) {
        const container = document.getElementById('analyticsRecentAgents');
        if (!container) return;
        
        if (!recentAgents || recentAgents.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent agents found</p>';
            return;
        }
        
        container.innerHTML = recentAgents.map(agent => {
            const statusColor = agent.is_enabled ? 'bg-green-500' : 'bg-gray-400';
            const createdDate = agent.created_at ? new Date(agent.created_at).toLocaleDateString() : 'Unknown';
            
            return `
                <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div class="w-3 h-3 ${statusColor} rounded-full flex-shrink-0"></div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-gray-900 truncate">${agent.name}</div>
                        <div class="text-xs text-gray-500">Created: ${createdDate}</div>
                    </div>
                    <div class="text-xs text-gray-400">
                        ${agent.is_enabled ? 'Active' : 'Inactive'}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    toggleUserDropdown(e) {
        e.stopPropagation();
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) {
            dropdown.classList.toggle('hidden');
        }
    }
    
    closeUserDropdown(e) {
        const dropdown = document.getElementById('userDropdown');
        const userMenuBtn = document.getElementById('userMenuBtn');
        
        // If called without event (e.g., from close button), just close the dropdown
        if (!e) {
            if (dropdown) {
                dropdown.classList.add('hidden');
            }
            return;
        }
        
        // If called with event, check if click is outside dropdown
        if (dropdown && userMenuBtn && !userMenuBtn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    }
    
    handleLogoClick() {
        // Add a special effect when logo is clicked
        const logoContainer = document.querySelector('.logo-container');
        if (logoContainer) {
            logoContainer.style.animation = 'none';
            setTimeout(() => {
                logoContainer.style.animation = 'logoPulse 4s ease-in-out infinite';
            }, 100);
        }
        
        // Navigate to dashboard
        this.showSection('dashboard');
        
        // Show a welcome message
        this.showMessage('Welcome to Agent Genie! 🚀', 'success');
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
                const indicator = statusElement.querySelector('.status-indicator');
                const text = statusElement.querySelector('span');
                
                if (indicator && text) {
                    // Clear all status classes first
                    indicator.className = indicator.className.replace(/online|offline/g, '').trim();
                    indicator.classList.add('status-indicator');
                
                    if (data.adk_available) {
                        indicator.classList.add('online');
                        text.textContent = 'ADK Available';
                    } else {
                        indicator.classList.add('offline');
                        text.textContent = 'ADK Not Available';
                    }
                }
            }
        } catch (error) {
            console.error('Error checking ADK status:', error);
            const statusElement = document.getElementById('adkStatus');
            if (statusElement) {
                const indicator = statusElement.querySelector('.status-indicator');
                const text = statusElement.querySelector('span');
                
                if (indicator && text) {
                    // Clear all status classes first
                    indicator.className = indicator.className.replace(/online|offline/g, '').trim();
                    indicator.classList.add('status-indicator', 'offline');
                    text.textContent = 'Connection Error';
                }
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
        
        const agentCount = project.agents?.length || 0;
        const toolCount = project.tools?.length || 0;
        const lastUpdated = project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'Unknown';
        
        div.innerHTML = `
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${project.name}</h3>
                    <p class="text-sm text-gray-600 mb-3">${project.description}</p>
                    
                    <!-- Project Stats -->
                    <div class="flex items-center space-x-2 mb-3">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            <i class="fas fa-robot mr-1"></i>${agentCount} agents
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <i class="fas fa-tools mr-1"></i>${toolCount} tools
                        </span>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            <i class="fas fa-clock mr-1"></i>${lastUpdated}
                        </span>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div class="flex space-x-2">
                        <button class="text-sm text-blue-600 hover:text-blue-800 px-3 py-1 rounded-md hover:bg-blue-50 transition-colors" onclick="app.manageProjectAgents('${project.id}')">
                            <i class="fas fa-plus mr-1"></i>Add Agents
                        </button>
                        <button class="text-sm text-green-600 hover:text-green-800 px-3 py-1 rounded-md hover:bg-green-50 transition-colors" onclick="app.manageProjectTools('${project.id}')">
                            <i class="fas fa-plus mr-1"></i>Add Tools
                        </button>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="flex flex-col space-y-2">
                    <button class="text-blue-500 hover:text-blue-700 p-2 rounded-lg hover:bg-blue-50 transition-colors" onclick="app.editProject('${project.id}')" title="Edit Project">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="text-purple-500 hover:text-purple-700 p-2 rounded-lg hover:bg-purple-50 transition-colors" onclick="app.viewProjectDetails('${project.id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="text-red-500 hover:text-red-700 p-2 rounded-lg hover:bg-red-50 transition-colors" onclick="app.deleteProject('${project.id}')" title="Delete Project">
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
        // Get function code from CodeMirror editor if available, otherwise from textarea
        const functionCode = typeof getCodeEditorContent === 'function' ? 
            getCodeEditorContent() : 
            document.getElementById('toolFunctionCode')?.value;
        
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
        
        // Render markdown for assistant messages, plain text for user messages
        if (role === 'assistant' && typeof marked !== 'undefined') {
            bubble.innerHTML = marked.parse(content);
            bubble.classList.add('chat-message-markdown');
        } else {
            bubble.textContent = content;
        }
        
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
    
    async editTool(toolId) {
        try {
            this.showLoading(true);
            
            // Find the tool in our local tools array
            const tool = this.tools.find(t => t.id === toolId);
            if (!tool) {
                this.showMessage('Tool not found', 'error');
                return;
            }
            
            console.log('Editing tool:', tool);
            console.log('Tool function code:', tool.function_code);
            
            // Populate the edit form with tool data
            document.getElementById('editToolId').value = tool.id;
            document.getElementById('editToolName').value = tool.name;
            document.getElementById('editToolType').value = tool.tool_type;
            document.getElementById('editToolDescription').value = tool.description;
            
            // Show the edit modal first
            this.showModal('editToolModal');
            
            // Show/hide function code section based on tool type
            const functionCodeSection = document.getElementById('editFunctionCodeSection');
            if (tool.tool_type === 'function') {
                functionCodeSection.classList.remove('hidden');
                
                // Set the function code value
                const functionCode = tool.function_code || '';
                document.getElementById('editToolFunctionCode').value = functionCode;
                console.log('Set function code value:', functionCode);
                
                // Initialize CodeMirror editor for edit modal after modal is shown
                setTimeout(() => {
                    this.initializeEditCodeEditor();
                }, 100);
            } else {
                functionCodeSection.classList.add('hidden');
            }
            
        } catch (error) {
            console.error('Error loading tool for editing:', error);
            this.showMessage('Error loading tool for editing', 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    initializeEditCodeEditor() {
        // Initialize CodeMirror for the edit modal
        const editCodeEditor = document.getElementById('editCodeEditor');
        const editToolFunctionCode = document.getElementById('editToolFunctionCode');
        const editCodeTheme = document.getElementById('editCodeTheme');
        
        console.log('Initializing edit code editor...');
        console.log('Function code value:', editToolFunctionCode.value);
        
        // Clear existing editor if any
        if (editCodeEditor.innerHTML.trim()) {
            editCodeEditor.innerHTML = '';
        }
        
        // Get the function code value
        const functionCodeValue = editToolFunctionCode.value || '';
        console.log('CodeMirror will initialize with value:', functionCodeValue);
        
        // Initialize CodeMirror
        const editor = CodeMirror(editCodeEditor, {
            value: functionCodeValue,
            mode: 'python',
            theme: editCodeTheme.value,
            lineNumbers: true,
            lineWrapping: true,
            indentUnit: 4,
            tabSize: 4,
            lineNumberFormatter: (line) => line
        });
        
        // Sync with textarea
        editor.on('change', () => {
            editToolFunctionCode.value = editor.getValue();
        });
        
        // Theme change handler
        editCodeTheme.addEventListener('change', () => {
            editor.setOption('theme', editCodeTheme.value);
        });
        
        // Store editor reference
        this.editCodeEditor = editor;
        
        console.log('Edit code editor initialized with value:', editor.getValue());
        
        // Force refresh the editor content
        editor.refresh();
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
    
    
    async editProject(projectId) {
        try {
            // Find the project to edit
            const project = this.projects.find(p => p.id === projectId);
            if (!project) {
                this.showMessage('Project not found', 'error');
                return;
            }

            // Show edit modal
            this.showProjectEditModal(project);
        } catch (error) {
            console.error('Error editing project:', error);
            this.showMessage('Failed to edit project', 'error');
        }
    }

    showProjectEditModal(project) {
        // Create modal HTML
        const modalHTML = `
            <div id="projectEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Edit Project</h3>
                        <button onclick="app.closeProjectEditModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <form id="projectEditForm" class="space-y-4">
                        <div>
                            <label for="editProjectName" class="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                            <input type="text" id="editProjectName" value="${project.name}" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        </div>
                        
                        <div>
                            <label for="editProjectDescription" class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea id="editProjectDescription" rows="3" 
                                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>${project.description}</textarea>
                        </div>
                        
                        <div class="flex justify-end space-x-3 pt-4">
                            <button type="button" onclick="app.closeProjectEditModal()" 
                                    class="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors">
                                Cancel
                            </button>
                            <button type="submit" 
                                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add form submit handler
        document.getElementById('projectEditForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveProjectEdit(project.id);
        });
    }

    async saveProjectEdit(projectId) {
        try {
            const name = document.getElementById('editProjectName').value.trim();
            const description = document.getElementById('editProjectDescription').value.trim();

            if (!name || !description) {
                this.showMessage('Name and description are required', 'error');
                return;
            }

            const updates = { name, description };

            const response = await fetch(`/api/projects/${projectId}/edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates)
            });

            if (response.ok) {
                const result = await response.json();
                this.showMessage('Project updated successfully!', 'success');
                this.closeProjectEditModal();
                
                // Refresh projects list
                await this.loadProjects();
                this.renderProjectsGrid();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to update project', 'error');
            }
        } catch (error) {
            console.error('Error saving project edit:', error);
            this.showMessage('Failed to save changes', 'error');
        }
    }

    closeProjectEditModal() {
        const modal = document.getElementById('projectEditModal');
        if (modal) {
            modal.remove();
        }
    }

    async manageProjectAgents(projectId) {
        try {
            const project = this.projects.find(p => p.id === projectId);
            if (!project) {
                this.showMessage('Project not found', 'error');
                return;
            }

            this.showProjectAgentsModal(project);
        } catch (error) {
            console.error('Error managing project agents:', error);
            this.showMessage('Failed to manage project agents', 'error');
        }
    }

    showProjectAgentsModal(project) {
        const modalHTML = `
            <div id="projectAgentsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Manage Agents: ${project.name}</h3>
                        <button onclick="app.closeProjectAgentsModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <!-- Current Agents -->
                    <div class="mb-6">
                        <h4 class="text-md font-medium text-gray-700 mb-3">Current Agents (${project.agents?.length || 0})</h4>
                        <div id="currentAgentsList" class="space-y-2">
                            ${this.renderCurrentAgentsList(project)}
                        </div>
                    </div>
                    
                    <!-- Add New Agents -->
                    <div>
                        <h4 class="text-md font-medium text-gray-700 mb-3">Add New Agents</h4>
                        <div class="space-y-2">
                            ${this.renderAvailableAgentsList(project)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    renderCurrentAgentsList(project) {
        if (!project.agents || project.agents.length === 0) {
            return '<p class="text-gray-500 text-sm">No agents in this project yet.</p>';
        }

        return project.agents.map(agent => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-robot text-blue-600"></i>
                    <span class="font-medium">${agent.name}</span>
                </div>
                <button onclick="app.removeAgentFromProject('${project.id}', '${agent.id}')" 
                        class="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    renderAvailableAgentsList(project) {
        const currentAgentIds = project.agents?.map(a => a.id) || [];
        const availableAgents = this.agents.filter(agent => !currentAgentIds.includes(agent.id));

        if (availableAgents.length === 0) {
            return '<p class="text-gray-500 text-sm">All available agents are already in this project.</p>';
        }

        return availableAgents.map(agent => `
            <div class="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-robot text-blue-600"></i>
                    <span class="font-medium">${agent.name}</span>
                    <span class="text-sm text-gray-600">${agent.description}</span>
                </div>
                <button onclick="app.addAgentToProject('${project.id}', '${agent.id}')" 
                        class="text-blue-600 hover:text-blue-800 px-3 py-1 rounded hover:bg-blue-100">
                    <i class="fas fa-plus mr-1"></i>Add
                </button>
            </div>
        `).join('');
    }

    async addAgentToProject(projectId, agentId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/agents/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent_id: agentId })
            });

            if (response.ok) {
                this.showMessage('Agent added to project successfully!', 'success');
                await this.loadProjects();
                this.renderProjectsGrid();
                this.closeProjectAgentsModal();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to add agent to project', 'error');
            }
        } catch (error) {
            console.error('Error adding agent to project:', error);
            this.showMessage('Failed to add agent to project', 'error');
        }
    }

    async removeAgentFromProject(projectId, agentId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/agents/${agentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showMessage('Agent removed from project successfully!', 'success');
                await this.loadProjects();
                this.renderProjectsGrid();
                this.closeProjectAgentsModal();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to remove agent from project', 'error');
            }
        } catch (error) {
            console.error('Error removing agent from project:', error);
            this.showMessage('Failed to remove agent from project', 'error');
        }
    }

    closeProjectAgentsModal() {
        const modal = document.getElementById('projectAgentsModal');
        if (modal) {
            modal.remove();
        }
    }

    async manageProjectTools(projectId) {
        try {
            const project = this.projects.find(p => p.id === projectId);
            if (!project) {
                this.showMessage('Project not found', 'error');
                return;
            }

            this.showProjectToolsModal(project);
        } catch (error) {
            console.error('Error managing project tools:', error);
            this.showMessage('Failed to manage project tools', 'error');
        }
    }

    showProjectToolsModal(project) {
        const modalHTML = `
            <div id="projectToolsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Manage Tools: ${project.name}</h3>
                        <button onclick="app.closeProjectToolsModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <!-- Current Tools -->
                    <div class="mb-6">
                        <h4 class="text-md font-medium text-gray-700 mb-3">Current Tools (${project.tools?.length || 0})</h4>
                        <div id="currentToolsList" class="space-y-2">
                            ${this.renderCurrentToolsList(project)}
                        </div>
                    </div>
                    
                    <!-- Add New Tools -->
                    <div>
                        <h4 class="text-md font-medium text-gray-700 mb-3">Add New Tools</h4>
                        <div class="space-y-2">
                            ${this.renderAvailableToolsList(project)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    renderCurrentToolsList(project) {
        if (!project.tools || project.tools.length === 0) {
            return '<p class="text-gray-500 text-sm">No tools in this project yet.</p>';
        }

        return project.tools.map(tool => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-tools text-green-600"></i>
                    <span class="font-medium">${tool.name}</span>
                </div>
                <button onclick="app.removeToolFromProject('${project.id}', '${tool.id}')" 
                        class="text-red-600 hover:text-red-800 p-1 rounded hover:bg-red-50">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `).join('');
    }

    renderAvailableToolsList(project) {
        const currentToolIds = project.tools?.map(t => t.id) || [];
        const availableTools = this.tools.filter(tool => !currentToolIds.includes(tool.id));

        if (availableTools.length === 0) {
            return '<p class="text-gray-500 text-sm">All available tools are already in this project.</p>';
        }

        return availableTools.map(tool => `
            <div class="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div class="flex items-center space-x-3">
                    <i class="fas fa-tools text-green-600"></i>
                    <span class="font-medium">${tool.name}</span>
                    <span class="text-sm text-gray-600">${tool.description}</span>
                </div>
                <button onclick="app.addToolToProject('${project.id}', '${tool.id}')" 
                        class="text-green-600 hover:text-green-800 px-3 py-1 rounded hover:bg-green-100">
                    <i class="fas fa-plus mr-1"></i>Add
                </button>
            </div>
        `).join('');
    }

    async addToolToProject(projectId, toolId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/tools/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tool_id: toolId })
            });

            if (response.ok) {
                this.showMessage('Tool added to project successfully!', 'success');
                await this.loadProjects();
                this.renderProjectsGrid();
                this.closeProjectToolsModal();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to add tool to project', 'error');
            }
        } catch (error) {
            console.error('Error adding tool to project:', error);
            this.showMessage('Failed to add tool to project', 'error');
        }
    }

    async removeToolFromProject(projectId, toolId) {
        try {
            const response = await fetch(`/api/projects/${projectId}/tools/${toolId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showMessage('Tool removed from project successfully!', 'success');
                await this.loadProjects();
                this.renderProjectsGrid();
                this.closeProjectToolsModal();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Failed to remove tool from project', 'error');
            }
        } catch (error) {
            console.error('Error removing tool from project:', error);
            this.showMessage('Failed to remove tool from project', 'error');
        }
    }

    closeProjectToolsModal() {
        const modal = document.getElementById('projectToolsModal');
        if (modal) {
            modal.remove();
        }
    }

    async viewProjectDetails(projectId) {
        try {
            const project = this.projects.find(p => p.id === projectId);
            if (!project) {
                this.showMessage('Project not found', 'error');
                return;
            }

            this.showProjectDetailsModal(project);
        } catch (error) {
            console.error('Error viewing project details:', error);
            this.showMessage('Failed to view project details', 'error');
        }
    }

    showProjectDetailsModal(project) {
        const modalHTML = `
            <div id="projectDetailsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div class="bg-white rounded-lg p-6 w-full max-w-3xl mx-4 max-h-[80vh] overflow-y-auto">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-900">Project Details: ${project.name}</h3>
                        <button onclick="app.closeProjectDetailsModal()" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <!-- Project Info -->
                        <div>
                            <h4 class="text-md font-medium text-gray-700 mb-3">Project Information</h4>
                            <div class="space-y-2">
                                <div><strong>Name:</strong> ${project.name}</div>
                                <div><strong>Description:</strong> ${project.description}</div>
                                <div><strong>Created:</strong> ${project.created_at ? new Date(project.created_at).toLocaleString() : 'Unknown'}</div>
                                <div><strong>Last Updated:</strong> ${project.updated_at ? new Date(project.updated_at).toLocaleString() : 'Unknown'}</div>
                            </div>
                        </div>
                        
                        <!-- Project Stats -->
                        <div>
                            <h4 class="text-md font-medium text-gray-700 mb-3">Project Statistics</h4>
                            <div class="space-y-2">
                                <div class="flex items-center space-x-2">
                                    <i class="fas fa-robot text-blue-600"></i>
                                    <span><strong>Agents:</strong> ${project.agents?.length || 0}</span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <i class="fas fa-tools text-green-600"></i>
                                    <span><strong>Tools:</strong> ${project.tools?.length || 0}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Agents List -->
                    <div class="mt-6">
                        <h4 class="text-md font-medium text-gray-700 mb-3">Project Agents</h4>
                        <div class="space-y-2">
                            ${this.renderProjectAgentsList(project)}
                        </div>
                    </div>
                    
                    <!-- Tools List -->
                    <div class="mt-6">
                        <h4 class="text-md font-medium text-gray-700 mb-3">Project Tools</h4>
                        <div class="space-y-2">
                            ${this.renderProjectToolsList(project)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    renderProjectAgentsList(project) {
        if (!project.agents || project.agents.length === 0) {
            return '<p class="text-gray-500 text-sm">No agents in this project.</p>';
        }

        return project.agents.map(agent => `
            <div class="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <i class="fas fa-robot text-blue-600"></i>
                <span class="font-medium">${agent.name}</span>
                <span class="text-sm text-gray-600">Added: ${agent.added_at ? new Date(agent.added_at).toLocaleDateString() : 'Unknown'}</span>
            </div>
        `).join('');
    }

    renderProjectToolsList(project) {
        if (!project.tools || project.tools.length === 0) {
            return '<p class="text-gray-500 text-sm">No tools in this project.</p>';
        }

        return project.tools.map(tool => `
            <div class="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <i class="fas fa-tools text-green-600"></i>
                <span class="font-medium">${tool.name}</span>
                <span class="text-sm text-gray-600">Added: ${tool.added_at ? new Date(tool.added_at).toLocaleDateString() : 'Unknown'}</span>
            </div>
        `).join('');
    }

    closeProjectDetailsModal() {
        const modal = document.getElementById('projectDetailsModal');
        if (modal) {
            modal.remove();
        }
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
                // Update CodeMirror editor if available, otherwise fallback to textarea
                if (typeof updateCodeEditor === 'function') {
                    updateCodeEditor(data.suggestion);
                } else {
                    const codeField = document.getElementById('toolFunctionCode');
                    if (codeField) {
                        codeField.value = data.suggestion;
                    }
                }
                this.showMessage('Python code generated successfully!', 'success');
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
    
    // Agent Embedding Methods
    async createAgentEmbed(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/embed`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Show the embed code
            this.showEmbedCode(data.embed_code, data.embed_url);
            
            this.showMessage('Agent embed created successfully!', 'success');
            
        } catch (error) {
            console.error('Error creating agent embed:', error);
            this.showMessage('Failed to create agent embed: ' + error.message, 'error');
        }
    }
    
    showEmbedCode(embedCode, embedUrl) {
        const container = document.getElementById('embedCodeContainer');
        const codeTextarea = document.getElementById('embedCode');
        
        if (container && codeTextarea) {
            codeTextarea.value = embedCode;
            container.classList.remove('hidden');
            
            // Scroll to the embed code
            container.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    copyEmbedCode() {
        const codeTextarea = document.getElementById('embedCode');
        if (codeTextarea) {
            codeTextarea.select();
            document.execCommand('copy');
            this.showMessage('Embed code copied to clipboard!', 'success');
        }
    }
    
    previewEmbed(embedUrl) {
        // Open embed preview in new window
        const fullUrl = window.location.origin + embedUrl;
        window.open(fullUrl, '_blank', 'width=800,height=600');
    }
    
    async createAgentEmbed() {
        try {
            // Get the current agent ID from the form
            const agentId = document.getElementById('agentId')?.value;
            const agentName = document.getElementById('agentName')?.value;
            
            if (!agentId || !agentName) {
                this.showMessage('Please save the agent first before creating an embed', 'warning');
                return;
            }
            
            // Show loading state
            const createEmbedBtn = document.getElementById('createEmbedBtn');
            const originalText = createEmbedBtn.innerHTML;
            createEmbedBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Creating...';
            createEmbedBtn.disabled = true;
            
            // Call the API to create embed
            const response = await fetch(`/api/agents/${agentId}/embed`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show the embed code container
                const embedCodeContainer = document.getElementById('embedCodeContainer');
                const embedCode = document.getElementById('embedCode');
                
                if (embedCodeContainer && embedCode) {
                    embedCodeContainer.classList.remove('hidden');
                    
                    // Generate the embed code
                    const embedHtml = this.generateEmbedCode(agentName, data.embed_url);
                    embedCode.value = embedHtml;
                    
                    this.showMessage('Embed created successfully!', 'success');
                }
            } else {
                this.showMessage(data.detail || 'Failed to create embed', 'error');
            }
            
        } catch (error) {
            console.error('Error creating embed:', error);
            this.showMessage('Failed to create embed: ' + error.message, 'error');
        } finally {
            // Restore button state
            const createEmbedBtn = document.getElementById('createEmbedBtn');
            if (createEmbedBtn) {
                createEmbedBtn.innerHTML = '<i class="fas fa-code mr-1"></i>Create Embed';
                createEmbedBtn.disabled = false;
            }
        }
    }
    
    generateEmbedCode(agentName, embedUrl) {
        const fullUrl = window.location.origin + embedUrl;
        return `<!-- ${agentName} Agent Embed Code -->
<div id="adk-agent-embed" style="width: 100%; max-width: 600px; margin: 0 auto;">
    <iframe 
        src="${fullUrl}" 
        width="100%" 
        height="600" 
        frameborder="0" 
        scrolling="no"
        style="border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
    </iframe>
</div>`;
    }
    
    bindEmbedEvents() {
        // Create embed button
        const createEmbedBtn = document.getElementById('createEmbedBtn');
        if (createEmbedBtn) {
            createEmbedBtn.addEventListener('click', () => {
                this.createAgentEmbed();
            });
        }
        
        // Copy embed code button
        const copyEmbedCodeBtn = document.getElementById('copyEmbedCodeBtn');
        if (copyEmbedCodeBtn) {
            copyEmbedCodeBtn.addEventListener('click', () => this.copyEmbedCode());
        }
        
        // Preview embed button
        const previewEmbedBtn = document.getElementById('previewEmbedBtn');
        if (previewEmbedBtn) {
            previewEmbedBtn.addEventListener('click', () => {
                const embedUrl = document.getElementById('embedCode')?.value.match(/src="([^"]+)"/)?.[1];
                if (embedUrl) {
                    this.previewEmbed(embedUrl);
                } else {
                    this.showMessage('No embed URL found', 'error');
                }
            });
        }
        
        // Embed agent select change
        const embedAgentSelect = document.getElementById('embedAgentSelect');
        if (embedAgentSelect) {
            embedAgentSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.loadAgentEmbeds(e.target.value);
                } else {
                    this.clearEmbedsList();
                }
            });
        }
    }
    
    populateEmbedAgentSelect() {
        const select = document.getElementById('embedAgentSelect');
        if (!select) return;
        
        // Clear existing options
        select.innerHTML = '<option value="">Choose an agent...</option>';
        
        // Add agents
        this.agents.forEach(agent => {
            const option = document.createElement('option');
            option.value = agent.id;
            option.textContent = agent.name;
            select.appendChild(option);
        });
    }
    
    async loadAgentEmbeds(agentId = null) {
        if (!agentId) {
            const select = document.getElementById('embedAgentSelect');
            agentId = select?.value;
        }
        
        if (!agentId) {
            this.clearEmbedsList();
            return;
        }
        
        try {
            const response = await fetch(`/api/agents/${agentId}/embeds`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.renderEmbedsList(data.embeds, agentId);
            
        } catch (error) {
            console.error('Error loading agent embeds:', error);
            this.showMessage('Failed to load embeds: ' + error.message, 'error');
        }
    }
    
    renderEmbedsList(embeds, agentId) {
        const container = document.getElementById('embedsList');
        if (!container) return;
        
        if (!embeds || embeds.length === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-code text-4xl mb-4"></i>
                    <p>No embeds found for this agent</p>
                    <button onclick="app.createNewEmbed('${agentId}')" class="mt-4 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
                        <i class="fas fa-plus mr-2"></i>Create First Embed
                    </button>
                </div>
            `;
            return;
        }
        
        let html = `
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-gray-900">Active Embeds</h3>
                <button onclick="app.createNewEmbed('${agentId}')" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors">
                    <i class="fas fa-plus mr-2"></i>Create New Embed
                </button>
            </div>
        `;
        
        embeds.forEach(embed => {
            const embedUrl = `/api/embed/${embed.embed_id}`;
            const fullUrl = window.location.origin + embedUrl;
            
            html += `
                <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-center justify-between mb-3">
                        <div>
                            <h4 class="font-medium text-gray-900">${embed.agent_name}</h4>
                            <p class="text-sm text-gray-600">Created: ${new Date(embed.created_at).toLocaleDateString()}</p>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                ${embed.access_count} views
                            </span>
                            <button onclick="app.deleteEmbed('${embed.embed_id}')" class="text-red-600 hover:text-red-800 transition-colors" title="Delete embed">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="space-y-3">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Embed URL:</label>
                            <div class="flex items-center space-x-2">
                                <input type="text" value="${fullUrl}" readonly class="flex-1 p-2 border border-gray-300 rounded-md bg-gray-50 text-sm">
                                <button onclick="app.copyToClipboard('${fullUrl}')" class="px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Embed Code:</label>
                            <textarea readonly rows="3" class="w-full p-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono">${this.generateEmbedCode(embed.agent_name, fullUrl)}</textarea>
                        </div>
                        
                        <div class="flex space-x-2">
                            <button onclick="app.previewEmbed('${embedUrl}')" class="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors">
                                <i class="fas fa-eye mr-2"></i>Preview
                            </button>
                            <button onclick="app.testEmbed('${embed.embed_id}')" class="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                <i class="fas fa-comments mr-2"></i>Test Chat
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    
    clearEmbedsList() {
        const container = document.getElementById('embedsList');
        if (container) {
            container.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-code text-4xl mb-4"></i>
                    <p>Select an agent to view and manage its embeds</p>
                </div>
            `;
        }
    }
    
    async createNewEmbed(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/embed`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Reload embeds list
            this.loadAgentEmbeds(agentId);
            
            this.showMessage('New embed created successfully!', 'success');
            
        } catch (error) {
            console.error('Error creating embed:', error);
            this.showMessage('Failed to create embed: ' + error.message, 'error');
        }
    }
    
    async deleteEmbed(embedId) {
        if (!confirm('Are you sure you want to delete this embed? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/embed/${embedId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Reload embeds list
            const select = document.getElementById('embedAgentSelect');
            if (select && select.value) {
                this.loadAgentEmbeds(select.value);
            }
            
            this.showMessage('Embed deleted successfully!', 'success');
            
        } catch (error) {
            console.error('Error deleting embed:', error);
            this.showMessage('Failed to delete embed: ' + error.message, 'error');
        }
    }
    
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showMessage('Copied to clipboard!', 'success');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showMessage('Copied to clipboard!', 'success');
        });
    }
    
    testEmbed(embedId) {
        const embedUrl = `/api/embed/${embedId}`;
        this.previewEmbed(embedUrl);
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
