// No-Code ADK Interface

// DOM Elements
const mainContent = document.getElementById('main-content');
const loadingContainer = document.getElementById('loading-container');
const errorContainer = document.getElementById('error-container');
const newAgentBtn = document.getElementById('new-agent-btn');
const myAgentsBtn = document.getElementById('my-agents-btn');
const functionToolsBtn = document.getElementById('function-tools-btn');
const configBtn = document.getElementById('config-btn');

// Templates
const newAgentTemplate = document.getElementById('new-agent-template');
const agentsListTemplate = document.getElementById('agents-list-template');
const agentDetailTemplate = document.getElementById('agent-detail-template');
const functionToolsTemplate = document.getElementById('function-tools-template');
const configTemplate = document.getElementById('config-template');
const subAgentTemplate = document.getElementById('sub-agent-template');

// State
let models = [];
let tools = [];
let templates = [];
let agents = [];
let functionTools = [];
let currentView = 'new-agent'; // 'new-agent', 'agents-list', 'agent-detail', 'function-tools', 'config'
let selectedAgentId = null;

// Event Listeners
newAgentBtn.addEventListener('click', showNewAgentView);
myAgentsBtn.addEventListener('click', showAgentsListView);
functionToolsBtn.addEventListener('click', showFunctionToolsView);
configBtn.addEventListener('click', showConfigView);

// Initialize
document.addEventListener('DOMContentLoaded', initialize);

async function initialize() {
    console.log('Initializing application...');
    showLoading();
    try {
        // Check if chat template is available
        const chatTemplate = document.getElementById('chat-interface-template');
        if (!chatTemplate) {
            console.error('Chat interface template not found during initialization');
        } else {
            console.log('Chat interface template loaded successfully');
        }
        
        // Check if all required templates are available
        const requiredTemplates = [
            'new-agent-template',
            'agents-list-template', 
            'agent-detail-template',
            'function-tools-template',
            'config-template',
            'chat-interface-template'
        ];
        
        requiredTemplates.forEach(templateId => {
            const template = document.getElementById(templateId);
            if (!template) {
                console.error(`Required template not found: ${templateId}`);
            } else {
                console.log(`Template loaded: ${templateId}`);
            }
        });
        
        console.log('Fetching data...');
        await Promise.all([
            fetchModels(),
            fetchTools(),
            fetchTemplates(),
            fetchAgents(),
            fetchFunctionTools()
        ]);
        console.log('Data fetched successfully');
        console.log('Models:', models);
        console.log('Tools:', tools);
        console.log('Templates:', templates);
        console.log('Agents:', agents);
        console.log('Function Tools:', functionTools);
        showNewAgentView();
    } catch (error) {
        console.error('Initialization error:', error);
        showError('Failed to initialize the application. Please refresh the page.');
    } finally {
        hideLoading();
    }
}

// API Functions
async function fetchModels() {
    try {
        const response = await fetch('/api/models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        models = data.models;
        console.log('Models fetched:', models);
    } catch (error) {
        console.error('Error fetching models:', error);
        models = [];
    }
}

async function fetchTools() {
    try {
        const response = await fetch('/api/tools');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        tools = data.tools;
        console.log('Tools fetched:', tools);
    } catch (error) {
        console.error('Error fetching tools:', error);
        tools = [];
    }
}

async function fetchTemplates() {
    try {
        const response = await fetch('/api/templates');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        templates = data.templates;
        console.log('Templates fetched:', templates);
    } catch (error) {
        console.error('Error fetching templates:', error);
        templates = [];
    }
}

async function fetchAgents() {
    try {
        const response = await fetch('/api/agents');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        agents = data.agents;
        console.log('Agents fetched:', agents);
    } catch (error) {
        console.error('Error fetching agents:', error);
        agents = [];
    }
}

async function fetchFunctionTools() {
    try {
        const response = await fetch('/api/function_tools');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        functionTools = data.templates;
        console.log('Function tools fetched:', functionTools);
    } catch (error) {
        console.error('Error fetching function tools:', error);
        functionTools = [];
    }
}

async function fetchAgent(agentId) {
    const response = await fetch(`/api/agents/${agentId}`);
    return await response.json();
}

async function createAgent(agentConfig) {
    const response = await fetch('/api/agents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(agentConfig),
    });
    return await response.json();
}

async function deleteAgent(agentId) {
    const response = await fetch(`/api/agents/${agentId}`, {
        method: 'DELETE',
    });
    return await response.json();
}

async function runAgent(agentId) {
    const response = await fetch(`/api/run/${agentId}`, {
        method: 'POST',
    });
    return await response.json();
}

async function createCustomTool(toolConfig) {
    const response = await fetch('/api/custom_tools', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(toolConfig),
    });
    return await response.json();
}

// View Functions
function showNewAgentView() {
    currentView = 'new-agent';
    clearMainContent();

    const newAgentNode = document.importNode(newAgentTemplate.content, true);

    // Handle provider selection
    const providerSelect = newAgentNode.querySelector('#provider');
    const modelSelect = newAgentNode.querySelector('#model');
    const ollamaSettings = newAgentNode.querySelector('.ollama-settings');

    // Function to update models based on provider
    const updateModels = (provider) => {
        // Clear current options
        modelSelect.innerHTML = '<option value="">Select a model</option>';

        // Filter models by provider
        const filteredModels = models.filter(model => model.provider === provider);

        // Add models to dropdown
        filteredModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            
            // Add status indicator if model is unavailable
            if (model.status === 'unavailable') {
                option.textContent += ` (${model.status})`;
                option.disabled = true;
            }
            
            modelSelect.appendChild(option);
        });
    };

    // Initial model population
    updateModels(providerSelect.value);

    // Handle provider change
    providerSelect.addEventListener('change', (e) => {
        updateModels(e.target.value);
        
        // Show/hide Ollama settings
        if (e.target.value === 'ollama') {
            ollamaSettings.classList.remove('d-none');
        } else {
            ollamaSettings.classList.add('d-none');
        }
    });

    // Populate tools with proper styling and status
    const toolsContainer = newAgentNode.querySelector('#tools-container');
    tools.forEach(tool => {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'col-md-6 mb-3';
        toolDiv.innerHTML = `
            <div class="card tool-card h-100">
                <div class="card-body">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="tools[]" value="${tool.id}" id="tool_${tool.id}">
                        <label class="form-check-label" for="tool_${tool.id}">
                            <h6 class="card-title mb-1">${tool.name}</h6>
                            <p class="card-text text-muted small mb-0">${tool.description}</p>
                        </label>
                    </div>
                </div>
            </div>
        `;
        toolsContainer.appendChild(toolDiv);
    });

    // Populate templates
    const templatesRow = newAgentNode.querySelector('#templates-row');
    templates.forEach(template => {
        const templateDiv = document.createElement('div');
        templateDiv.className = 'col-md-6 col-lg-4 mb-3';
        templateDiv.innerHTML = `
            <div class="card template-card" data-template-id="${template.id}">
                <div class="card-body text-center">
                    <h6 class="card-title">${template.name}</h6>
                    <p class="card-text text-muted small">${template.description}</p>
                    <button type="button" class="btn btn-outline-primary btn-sm use-template-btn">
                        Use Template
                    </button>
                </div>
            </div>
        `;
        templatesRow.appendChild(templateDiv);

        // Add template selection handler
        const useTemplateBtn = templateDiv.querySelector('.use-template-btn');
        useTemplateBtn.addEventListener('click', () => handleTemplateSelect(template));
    });

    // Handle sub-agent functionality
    const addSubAgentBtn = newAgentNode.querySelector('#add-sub-agent-btn');
    const subAgentsContainer = newAgentNode.querySelector('#sub-agents-container');
    const subAgentsCounter = newAgentNode.querySelector('#sub-agents-counter');
    
    // Function to update sub-agents counter
    const updateSubAgentsCounter = () => {
        const count = subAgentsContainer.querySelectorAll('.sub-agent-item').length;
        if (subAgentsCounter) {
            subAgentsCounter.textContent = count;
            subAgentsCounter.className = count > 0 ? 'badge badge-primary' : 'badge badge-secondary';
        }
    };
    
    addSubAgentBtn.addEventListener('click', () => {
        addSubAgent(subAgentsContainer, models);
        updateSubAgentsCounter();
    });
    
    // Initial counter update
    updateSubAgentsCounter();

    // Handle form submission
    const form = newAgentNode.querySelector('#agent-form');
    form.addEventListener('submit', handleAgentFormSubmit);

    // Handle temperature range
    const temperatureRange = newAgentNode.querySelector('#temperature');
    const temperatureValue = newAgentNode.querySelector('#temperature-value');
    temperatureRange.addEventListener('input', (e) => {
        temperatureValue.textContent = `Current: ${e.target.value}`;
    });

    mainContent.appendChild(newAgentNode);
}

function showAgentsListView() {
    currentView = 'agents-list';
    clearMainContent();

    const agentsListNode = document.importNode(agentsListTemplate.content, true);
    
    if (agents.length === 0) {
        agentsListNode.querySelector('#no-agents-message').classList.remove('d-none');
        agentsListNode.querySelector('#agents-table-container').classList.add('d-none');
    } else {
        const tbody = agentsListNode.querySelector('#agents-table-body');
        agents.forEach(agent => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${agent.name}</strong></td>
                <td><span class="badge badge-primary">${agent.model}</span></td>
                <td><span class="badge badge-secondary">${agent.provider}</span></td>
                <td><span class="badge badge-success">Ready</span></td>
                <td>
                    <button class="btn btn-outline-primary btn-sm me-2 view-agent-btn" data-agent-id="${agent.id}">
                        <i class="bi bi-eye"></i> View
                    </button>
                    <button class="btn btn-outline-success btn-sm me-2 run-agent-btn" data-agent-id="${agent.id}">
                        <i class="bi bi-play"></i> Run
                    </button>
                    <button class="btn btn-outline-danger btn-sm delete-agent-btn" data-agent-id="${agent.id}">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });

        // Add event listeners
        agentsListNode.querySelectorAll('.view-agent-btn').forEach(btn => {
            btn.addEventListener('click', handleViewAgent);
        });
        agentsListNode.querySelectorAll('.run-agent-btn').forEach(btn => {
            btn.addEventListener('click', handleRunAgent);
        });
        agentsListNode.querySelectorAll('.delete-agent-btn').forEach(btn => {
            btn.addEventListener('click', handleDeleteAgent);
        });
    }

    mainContent.appendChild(agentsListNode);
}

function showFunctionToolsView() {
    currentView = 'function-tools';
    clearMainContent();

    const functionToolsNode = document.importNode(functionToolsTemplate.content, true);
    
    // Populate function tool templates
    const container = functionToolsNode.querySelector('#function-tools-container');
    functionTools.forEach(tool => {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'function-tool-card';
        toolDiv.innerHTML = `
            <h6 class="text-primary">${tool.name}</h6>
            <p class="text-muted">${tool.description}</p>
            <div class="parameter-table">
                <h6 class="text-secondary">Parameters:</h6>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(tool.parameters || {}).map(([key, value]) => `
                            <tr>
                                <td><code>${key}</code></td>
                                <td><span class="badge badge-secondary">${value.type}</span></td>
                                <td>${value.description}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="mt-3">
                <button class="btn btn-outline-primary btn-sm use-tool-template-btn" data-tool-id="${tool.id}">
                    Use Template
                </button>
            </div>
        `;
        container.appendChild(toolDiv);

        // Add template usage handler
        const useTemplateBtn = toolDiv.querySelector('.use-tool-template-btn');
        useTemplateBtn.addEventListener('click', () => {
            useFunctionToolTemplate(tool);
        });
    });

    // Handle custom tool form submission
    const form = functionToolsNode.querySelector('#custom-tool-form');
    form.addEventListener('submit', handleCustomToolFormSubmit);

    mainContent.appendChild(functionToolsNode);
}

function showConfigView() {
    currentView = 'config';
    clearMainContent();

    const configNode = document.importNode(configTemplate.content, true);
    
    // Handle API key visibility toggle
    const toggleBtn = configNode.querySelector('#toggle-api-key');
    const apiKeyInput = configNode.querySelector('#google-api-key');
    toggleBtn.addEventListener('click', () => {
        if (apiKeyInput.type === 'password') {
            apiKeyInput.type = 'text';
            toggleBtn.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
            apiKeyInput.type = 'password';
            toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
        }
    });

    // Handle copy API key
    const copyBtn = configNode.querySelector('#copy-api-key');
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(apiKeyInput.value);
            showSuccess('API key copied to clipboard!');
        } catch (error) {
            showError('Failed to copy API key');
        }
    });

    // Handle refresh configuration
    const refreshBtn = configNode.querySelector('#refresh-config-btn');
    refreshBtn.addEventListener('click', async () => {
        await refreshConfigStatus(configNode);
    });

    // Load initial configuration status
    loadConfigStatus(configNode);
    
    mainContent.appendChild(configNode);
}

function addSubAgent(container, models) {
    const subAgentNode = document.importNode(subAgentTemplate.content, true);
    
    // Add unique identifier to the sub-agent
    const uniqueId = `sub_agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    subAgentNode.querySelector('.sub-agent-item').id = uniqueId;
    
    // Populate model options
    const modelSelect = subAgentNode.querySelector('.sub-agent-model');
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.textContent = model.name;
        
        // Add status indicator if model is unavailable
        if (model.status === 'unavailable') {
            option.textContent += ` (${model.status})`;
            option.disabled = true;
        }
        
        modelSelect.appendChild(option);
    });

    // Populate tools with proper styling
    const toolsContainer = subAgentNode.querySelector('.sub-agent-tools');
    tools.forEach(tool => {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'form-check form-check-inline mb-2';
        toolDiv.innerHTML = `
            <input class="form-check-input" type="checkbox" name="sub_agent_tools[]" value="${tool.id}" id="sub_tool_${tool.id}_${Date.now()}">
            <label class="form-check-label" for="sub_tool_${tool.id}_${Date.now()}">
                <strong>${tool.name}</strong>
                <br><small class="text-muted">${tool.description}</small>
            </label>
        `;
        toolsContainer.appendChild(toolDiv);
    });

    // Handle remove button with improved logic and animation
    const removeBtn = subAgentNode.querySelector('.remove-sub-agent-btn');
    removeBtn.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        
        // Find the sub-agent item to remove
        const subAgentItem = subAgentNode.querySelector('.sub-agent-item');
        if (subAgentItem && container.contains(subAgentItem)) {
            // Get sub-agent name for confirmation
            const subAgentName = subAgentItem.querySelector('.sub-agent-name').value || 'Unnamed Sub-Agent';
            
            // Show confirmation dialog
            if (confirm(`Are you sure you want to remove the sub-agent "${subAgentName}"?`)) {
                // Add removal animation
                subAgentItem.classList.add('removing');
                
                // Remove after animation completes
                setTimeout(() => {
                    if (container.contains(subAgentItem)) {
                        container.removeChild(subAgentItem);
                        console.log(`Removed sub-agent: ${uniqueId}`);
                        
                        // Update counter after removal
                        const counter = document.querySelector('#sub-agents-counter');
                        if (counter) {
                            const count = container.querySelectorAll('.sub-agent-item').length;
                            counter.textContent = count;
                            counter.className = count > 0 ? 'badge badge-primary' : 'badge badge-secondary';
                        }
                        
                        // Show success message
                        showSuccess(`Sub-agent "${subAgentName}" removed successfully!`);
                    }
                }, 300);
            }
        } else {
            console.log('Sub-agent not found or already removed');
            showError('Sub-agent not found or already removed');
        }
    });

    container.appendChild(subAgentNode);
    
    // Return the unique ID for reference
    return uniqueId;
}

function useFunctionToolTemplate(tool) {
    // Switch to new agent view and populate with tool template
    showNewAgentView();
    
    // Find the custom tool form and populate it
    const toolIdInput = document.getElementById('tool_id');
    const toolNameInput = document.getElementById('tool_name');
    const toolDescriptionInput = document.getElementById('tool_description');
    const toolCodeInput = document.getElementById('tool_code');
    
    if (toolIdInput && toolNameInput && toolDescriptionInput && toolCodeInput) {
        toolIdInput.value = tool.id;
        toolNameInput.value = tool.name;
        toolDescriptionInput.value = tool.description;
        toolCodeInput.value = tool.code;
    }
}

async function showAgentDetailView(agentId) {
    currentView = 'agent-detail';
    selectedAgentId = agentId;
    clearMainContent();

    try {
        const agent = await fetchAgent(agentId);
        const agentDetailNode = document.importNode(agentDetailTemplate.content, true);
        
        agentDetailNode.querySelector('#agent-name').textContent = agent.name;
        agentDetailNode.querySelector('#agent-config').textContent = JSON.stringify(agent, null, 2);
        
        // Fetch and display agent code
        try {
            const codeResponse = await fetch(`/api/agents/${agentId}/code`);
            if (codeResponse.ok) {
                const codeData = await codeResponse.json();
                agentDetailNode.querySelector('#agent-code').textContent = codeData.code;
            }
        } catch (error) {
            agentDetailNode.querySelector('#agent-code').textContent = 'Code not available';
        }

        // Add event listeners
        agentDetailNode.querySelector('#back-btn').addEventListener('click', showAgentsListView);
        agentDetailNode.querySelector('#run-btn').addEventListener('click', handleRunAgent);

        mainContent.appendChild(agentDetailNode);
    } catch (error) {
        showError(`Failed to load agent details: ${error.message}`);
    }
}

async function handleAgentFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const agentConfig = {
        name: formData.get('name'),
        model: formData.get('model'),
        provider: formData.get('provider'),
        instruction: formData.get('instruction'),
        description: formData.get('description'),
        tools: formData.getAll('tools[]'),
        flow: formData.get('flow'),
        temperature: parseFloat(formData.get('temperature')),
        generate_api: formData.get('generate_api') === 'on',
        api_port: 8000
    };

    // Handle Ollama-specific settings
    if (agentConfig.provider === 'ollama') {
        agentConfig.ollama_base_url = formData.get('ollama_base_url');
    }

    // Handle sub-agents
    const subAgents = [];
    const subAgentItems = document.querySelectorAll('.sub-agent-item');
    subAgentItems.forEach(item => {
        const subAgent = {
            name: item.querySelector('.sub-agent-name').value,
            model: item.querySelector('.sub-agent-model').value,
            instruction: item.querySelector('.sub-agent-instruction').value,
            description: item.querySelector('.sub-agent-description').value,
            tools: Array.from(item.querySelectorAll('input[name="sub_agent_tools[]"]:checked')).map(cb => cb.value)
        };
        if (subAgent.name && subAgent.model && subAgent.instruction) {
            subAgents.push(subAgent);
        }
    });
    
    if (subAgents.length > 0) {
        agentConfig.sub_agents = subAgents;
    }

    try {
        showLoading();
        const result = await createAgent(agentConfig);
        showSuccess(`Agent '${agentConfig.name}' created successfully!`);
        
        // Refresh agents list and show it
        await fetchAgents();
        showAgentsListView();
    } catch (error) {
        console.error('Error creating agent:', error);
        showError(`Failed to create agent: ${error.message}`);
    } finally {
        hideLoading();
    }
}

async function handleCustomToolFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const toolConfig = {
        id: formData.get('tool_id'),
        name: formData.get('tool_name'),
        description: formData.get('tool_description'),
        code: formData.get('tool_code')
    };

    try {
        showLoading();
        const result = await createCustomTool(toolConfig);
        showSuccess(`Tool '${toolConfig.name}' created successfully!`);
        
        // Refresh tools and clear form
        await fetchTools();
        event.target.reset();
    } catch (error) {
        console.error('Error creating tool:', error);
        showError(`Failed to create tool: ${error.message}`);
    } finally {
        hideLoading();
    }
}

function handleTemplateSelect(template) {
    // Clear form
    document.getElementById('agent-form').reset();
    
    // Populate with template data
    document.getElementById('name').value = template.config.name;
    document.getElementById('description').value = template.config.description;
    document.getElementById('instruction').value = template.config.instruction;
    document.getElementById('flow').value = template.config.flow;
    document.getElementById('generate_api').checked = template.config.generate_api;
    
    // Set provider and model
    const providerSelect = document.getElementById('provider');
    providerSelect.value = template.config.provider;
    providerSelect.dispatchEvent(new Event('change'));
    
    // Wait for models to populate, then set the model
    setTimeout(() => {
        const modelSelect = document.getElementById('model');
        modelSelect.value = template.config.model;
    }, 100);
    
    // Set tools
    if (template.config.tools) {
        template.config.tools.forEach(toolId => {
            const toolCheckbox = document.querySelector(`input[name="tools[]"][value="${toolId}"]`);
            if (toolCheckbox) {
                toolCheckbox.checked = true;
            }
        });
    }
    
    // Set sub-agents if any
    if (template.config.sub_agents) {
        const subAgentsContainer = document.getElementById('sub-agents-container');
        subAgentsContainer.innerHTML = '';
        
        template.config.sub_agents.forEach(subAgent => {
            addSubAgent(subAgentsContainer, models);
            
            // Populate the newly added sub-agent
            const lastSubAgent = subAgentsContainer.lastElementChild;
            lastSubAgent.querySelector('.sub-agent-name').value = subAgent.name;
            lastSubAgent.querySelector('.sub-agent-model').value = subAgent.model;
            lastSubAgent.querySelector('.sub-agent-instruction').value = subAgent.instruction;
            lastSubAgent.querySelector('.sub-agent-description').value = subAgent.description;
            
            if (subAgent.tools) {
                subAgent.tools.forEach(toolId => {
                    const toolCheckbox = lastSubAgent.querySelector(`input[value="${toolId}"]`);
                    if (toolCheckbox) {
                        toolCheckbox.checked = true;
                    }
                });
            }
        });
    }
    
    // Highlight selected template
    document.querySelectorAll('.template-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    const selectedCard = document.querySelector(`[data-template-id="${template.id}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    showSuccess(`Template "${template.name}" applied!`);
}

async function handleViewAgent(event) {
    const agentId = event.target.dataset.agentId;
    await showAgentDetailView(agentId);
}

async function handleRunAgent(event) {
    let agentId;
    
    // Try to get agent ID from button data attribute (for agents list view)
    if (event.target.dataset.agentId) {
        agentId = event.target.dataset.agentId;
    } 
    // If no data attribute, use selectedAgentId (for agent detail view)
    else if (selectedAgentId) {
        agentId = selectedAgentId;
    } 
    // Fallback: try to get from parent button or find the closest button with data
    else {
        const button = event.target.closest('button');
        if (button && button.dataset.agentId) {
            agentId = button.dataset.agentId;
        } else {
            showError('Could not determine which agent to run');
            return;
        }
    }
    
    try {
        // Launch chat interface for this agent
        launchChatInterface(agentId);
    } catch (error) {
        console.error('Error launching chat interface:', error);
        showError(`Failed to launch chat interface: ${error.message}`);
    }
}

async function handleDeleteAgent(event) {
    const agentId = event.target.dataset.agentId;
    
    if (confirm(`Are you sure you want to delete agent '${agentId}'?`)) {
        try {
            showLoading();
            await deleteAgent(agentId);
            showSuccess(`Agent '${agentId}' deleted successfully!`);
            
            // Refresh agents list
            await fetchAgents();
            showAgentsListView();
        } catch (error) {
            console.error('Error deleting agent:', error);
            showError(`Failed to delete agent: ${error.message}`);
        } finally {
            hideLoading();
        }
    }
}

async function loadConfigStatus(configNode) {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Update Google API status
        const googleStatus = configNode.querySelector('#google-api-status');
        if (config.google_api_available) {
            googleStatus.innerHTML = `
                <span class="badge badge-success me-2">Available</span>
                <small class="text-muted">API key is valid and working</small>
            `;
        } else {
            googleStatus.innerHTML = `
                <span class="badge badge-danger me-2">Unavailable</span>
                <small class="text-muted">API key is invalid or not configured</small>
            `;
        }
        
        // Update Ollama status
        const ollamaStatus = configNode.querySelector('#ollama-status');
        if (config.ollama_available) {
            ollamaStatus.innerHTML = `
                <span class="badge badge-success me-2">Available</span>
                <small class="text-muted">Ollama is running locally</small>
            `;
        } else {
            ollamaStatus.innerHTML = `
                <span class="badge badge-warning me-2">Unavailable</span>
                <small class="text-muted">Ollama is not running or not accessible</small>
            `;
        }
    } catch (error) {
        console.error('Error loading config status:', error);
    }
}

async function refreshConfigStatus(configNode) {
    const refreshBtn = configNode.querySelector('#refresh-config-btn');
    const originalText = refreshBtn.innerHTML;
    
    refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-2 spin"></i>Refreshing...';
    refreshBtn.disabled = true;
    
    try {
        await loadConfigStatus(configNode);
        showSuccess('Configuration status refreshed!');
    } catch (error) {
        showError('Failed to refresh configuration status');
    } finally {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
    }
}

function clearMainContent() {
    mainContent.innerHTML = '';
}

function showLoading() {
    loadingContainer.classList.remove('d-none');
}

function hideLoading() {
    loadingContainer.classList.add('d-none');
}

function showError(message) {
    errorContainer.textContent = message;
    errorContainer.classList.remove('d-none');
    setTimeout(() => {
        errorContainer.classList.add('d-none');
    }, 5000);
}

function showSuccess(message) {
    // Create a temporary success alert
    const successAlert = document.createElement('div');
    successAlert.className = 'alert alert-success alert-dismissible fade show';
    successAlert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    container.insertBefore(successAlert, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (successAlert.parentNode) {
            successAlert.remove();
        }
    }, 5000);
}


// ----------------- Custom Tools UI -----------------
function showCustomToolsView(){
    currentView = 'custom-tools';
    clearMainContent();
    const div = document.createElement('div');
    div.innerHTML = `
    <h2 class="mb-3">Custom Tools</h2>
    <form id="tool-form" class="card p-3 mb-4">
      <div class="mb-3"><label class="form-label">Tool ID</label><input name="id" class="form-control" required></div>
      <div class="mb-3"><label class="form-label">Name</label><input name="name" class="form-control" required></div>
      <div class="mb-3"><label class="form-label">Description</label><input name="description" class="form-control" required></div>
      <div class="mb-3"><label class="form-label">Python Code (module content)</label><textarea name="code" class="form-control" rows="6" placeholder="def my_tool(arg):
return 'result'"></textarea></div>
      <button type="submit" class="btn btn-primary">Create Tool</button>
    </form>
    <h3>Existing Custom Tools</h3>
    <ul id="custom-tools-list" class="list-group"></ul>`;
    mainContent.appendChild(div);

    // Load list
    fetch('/api/custom_tools').then(r=>r.json()).then(d=>{
        const ul=document.getElementById('custom-tools-list');
        ul.innerHTML='';
        d.tools.forEach(t=>{const li=document.createElement('li'); li.className='list-group-item'; li.textContent=`${t.id} — ${t.name}`; ul.appendChild(li);});
    });

    div.querySelector('#tool-form').addEventListener('submit', async (e)=>{
        e.preventDefault();
        const fd=new FormData(e.target); const obj={}; fd.forEach((v,k)=>obj[k]=v);
        await fetch('/api/custom_tools',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
        alert('Tool created');
        showCustomToolsView();
    });
}

// Add navbar button listener
const customToolsBtn = document.getElementById('custom-tools-btn');
if(customToolsBtn){ customToolsBtn.addEventListener('click', showCustomToolsView); }

// Chat Interface Functions
let currentChatAgent = null;
let chatHistory = [];

function launchChatInterface(agentId) {
    console.log('Launching chat interface for agent:', agentId);
    
    // Get agent details
    const agent = agents.find(a => a.id === agentId);
    if (!agent) {
        console.error('Agent not found:', agentId);
        alert('Agent not found');
        return;
    }
    
    console.log('Found agent:', agent);
    currentChatAgent = agent;
    chatHistory = [];
    
    // Get the chat interface template
    const chatInterfaceTemplate = document.getElementById('chat-interface-template');
    if (!chatInterfaceTemplate) {
        console.error('Chat interface template not found');
        alert('Chat interface template not found');
        return;
    }
    
    console.log('Template found, creating interface...');
    
    // Create chat overlay
    const overlay = document.createElement('div');
    overlay.className = 'chat-overlay';
    overlay.id = 'chat-overlay';
    
    // Create chat interface
    const chatInterface = document.importNode(chatInterfaceTemplate.content, true);
    chatInterface.id = 'chat-interface';
    
    // Set agent information
    chatInterface.querySelector('#chat-agent-name').textContent = agent.name;
    chatInterface.querySelector('#chat-agent-model').textContent = `Model: ${agent.model}`;
    
    // Add to DOM
    overlay.appendChild(chatInterface);
    document.body.appendChild(overlay);
    
    console.log('Interface added to DOM, setting up functionality...');
    
    // Setup chat functionality
    setupChatInterface(chatInterface);
    
    // Focus on input
    setTimeout(() => {
        chatInterface.querySelector('#chat-input').focus();
    }, 100);
    
    console.log('Chat interface launched successfully');
}

function setupChatInterface(chatInterface) {
    const chatForm = chatInterface.querySelector('#chat-form');
    const chatInput = chatInterface.querySelector('#chat-input');
    const closeBtn = chatInterface.querySelector('#close-chat-btn');
    const charCount = chatInterface.querySelector('#char-count');
    
    // Handle form submission
    chatForm.addEventListener('submit', handleChatSubmit);
    
    // Handle input changes
    chatInput.addEventListener('input', (e) => {
        const count = e.target.value.length;
        charCount.textContent = count;
        
        // Auto-resize textarea
        e.target.style.height = 'auto';
        e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
    });
    
    // Handle Enter key (send on Enter, new line on Shift+Enter)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
    
    // Handle close button
    closeBtn.addEventListener('click', closeChatInterface);
    
    // Handle overlay click to close
    const overlay = document.getElementById('chat-overlay');
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeChatInterface();
        }
    });
}

async function handleChatSubmit(event) {
    event.preventDefault();
    
    const chatInterface = document.getElementById('chat-interface');
    const chatInput = chatInterface.querySelector('#chat-input');
    const chatMessages = chatInterface.querySelector('#chat-messages');
    const sendBtn = chatInterface.querySelector('#chat-send-btn');
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    // Add user message
    addChatMessage('user', message);
    
    // Clear input and reset height
    chatInput.value = '';
    chatInput.style.height = 'auto';
    chatInterface.querySelector('#char-count').textContent = '0';
    
    // Disable input and show typing indicator
    chatInput.disabled = true;
    sendBtn.disabled = true;
    showTypingIndicator(chatMessages);
    
    try {
        // Send message to agent
        const response = await sendMessageToAgent(message);
        
        // Remove typing indicator
        removeTypingIndicator(chatMessages);
        
        // Add agent response
        addChatMessage('agent', response);
        
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(chatMessages);
        addChatMessage('system', 'Sorry, I encountered an error. Please try again.');
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function addChatMessage(type, content) {
    const chatInterface = document.getElementById('chat-interface');
    const chatMessages = chatInterface.querySelector('#chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${type === 'user' ? '<i class="bi bi-person me-2"></i>' : ''}
            ${type === 'agent' ? '<i class="bi bi-robot me-2"></i>' : ''}
            ${type === 'system' ? '<i class="bi bi-exclamation-triangle me-2"></i>' : ''}
            ${content}
        </div>
        <div class="message-timestamp">${timestamp}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add to history
    chatHistory.push({ type, content, timestamp });
}

function showTypingIndicator(chatMessages) {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message agent-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-content">
            <i class="bi bi-robot me-2"></i>
            <span>Agent is typing</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator(chatMessages) {
    const typingIndicator = chatMessages.querySelector('#typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessageToAgent(message) {
    if (!currentChatAgent) {
        throw new Error('No agent available');
    }
    
    try {
        // Send message to the chat API
        const response = await fetch(`/api/chat/${currentChatAgent.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                agent_id: currentChatAgent.id
            }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.response;
        
    } catch (error) {
        console.error('Error sending message to agent:', error);
        throw new Error('Failed to communicate with agent. Please try again.');
    }
}

function closeChatInterface() {
    const overlay = document.getElementById('chat-overlay');
    if (overlay) {
        overlay.remove();
    }
    currentChatAgent = null;
    chatHistory = [];
}
