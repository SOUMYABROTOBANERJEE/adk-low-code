// No-Code ADK Interface

// DOM Elements
const mainContent = document.getElementById('main-content');
const loadingContainer = document.getElementById('loading-container');
const errorContainer = document.getElementById('error-container');
const newAgentBtn = document.getElementById('new-agent-btn');
const myAgentsBtn = document.getElementById('my-agents-btn');

// Templates
const newAgentTemplate = document.getElementById('new-agent-template');
const agentsListTemplate = document.getElementById('agents-list-template');
const agentDetailTemplate = document.getElementById('agent-detail-template');

// State
let models = [];
let tools = [];
let templates = [];
let agents = [];
let currentView = 'new-agent'; // 'new-agent', 'agents-list', 'agent-detail'
let selectedAgentId = null;

// Event Listeners
newAgentBtn.addEventListener('click', showNewAgentView);
myAgentsBtn.addEventListener('click', showAgentsListView);

// Initialize
document.addEventListener('DOMContentLoaded', initialize);

async function initialize() {
    showLoading();
    try {
        await Promise.all([
            fetchModels(),
            fetchTools(),
            fetchTemplates(),
            fetchAgents()
        ]);
        showNewAgentView();
    } catch (error) {
        showError('Failed to initialize the application. Please refresh the page.');
        console.error('Initialization error:', error);
    } finally {
        hideLoading();
    }
}

// API Functions
async function fetchModels() {
    const response = await fetch('/api/models');
    const data = await response.json();
    models = data.models;
}

async function fetchTools() {
    const response = await fetch('/api/tools');
    const data = await response.json();
    tools = data.tools;
}

async function fetchTemplates() {
    const response = await fetch('/api/templates');
    const data = await response.json();
    templates = data.templates;
}

async function fetchAgents() {
    const response = await fetch('/api/agents');
    const data = await response.json();
    agents = data.agents;
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
            modelSelect.appendChild(option);
        });

        // Show/hide Ollama settings
        if (provider === 'ollama') {
            ollamaSettings.classList.remove('d-none');
        } else {
            ollamaSettings.classList.add('d-none');
        }
    };

    // Initial population
    updateModels(providerSelect.value);

    // Update on provider change
    providerSelect.addEventListener('change', () => {
        updateModels(providerSelect.value);
    });

    // Populate tools checkboxes
    const toolsContainer = newAgentNode.querySelector('#tools-container');
    tools.forEach(tool => {
        const col = document.createElement('div');
        col.className = 'col-md-6 tool-checkbox';
        col.innerHTML = `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="tool-${tool.id}" name="tools" value="${tool.id}">
                <label class="form-check-label" for="tool-${tool.id}">
                    ${tool.name}
                    <div class="tool-description">${tool.description}</div>
                </label>
            </div>
        `;
        toolsContainer.appendChild(col);
    });

    // Populate templates
    const templatesRow = newAgentNode.querySelector('#templates-row');
    templates.forEach(template => {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-3';
        col.innerHTML = `
            <div class="card h-100 template-card" data-template-id="${template.id}">
                <div class="card-body">
                    <h5 class="card-title">${template.name}</h5>
                    <p class="card-text">${template.description}</p>
                    <button class="btn btn-outline-primary btn-sm use-template-btn">
                        Use Template
                    </button>
                </div>
            </div>
        `;
        templatesRow.appendChild(col);
    });

    // Add event listeners
    const form = newAgentNode.querySelector('#agent-form');
    form.addEventListener('submit', handleAgentFormSubmit);

    const temperatureInput = newAgentNode.querySelector('#temperature');
    const temperatureValue = newAgentNode.querySelector('#temperature-value');
    temperatureInput.addEventListener('input', () => {
        temperatureValue.textContent = `Current: ${temperatureInput.value}`;
    });

    const templateButtons = newAgentNode.querySelectorAll('.use-template-btn');
    templateButtons.forEach(button => {
        button.addEventListener('click', handleTemplateSelect);
    });

    mainContent.appendChild(newAgentNode);
}

function showAgentsListView() {
    currentView = 'agents-list';
    clearMainContent();

    const agentsListNode = document.importNode(agentsListTemplate.content, true);

    const noAgentsMessage = agentsListNode.querySelector('#no-agents-message');
    const agentsTableContainer = agentsListNode.querySelector('#agents-table-container');
    const agentsTableBody = agentsListNode.querySelector('#agents-table-body');

    if (agents.length === 0) {
        noAgentsMessage.classList.remove('d-none');
        agentsTableContainer.classList.add('d-none');
    } else {
        noAgentsMessage.classList.add('d-none');
        agentsTableContainer.classList.remove('d-none');

        agents.forEach(agent => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${agent.name}</td>
                <td><code>${agent.path}</code></td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary view-agent-btn" data-agent-id="${agent.id}">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-outline-success run-agent-btn" data-agent-id="${agent.id}">
                            <i class="bi bi-play-fill"></i>
                        </button>
                        <button class="btn btn-outline-danger delete-agent-btn" data-agent-id="${agent.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            agentsTableBody.appendChild(row);
        });
    }

    // Add event listeners
    const viewButtons = agentsListNode.querySelectorAll('.view-agent-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', handleViewAgent);
    });

    const runButtons = agentsListNode.querySelectorAll('.run-agent-btn');
    runButtons.forEach(button => {
        button.addEventListener('click', handleRunAgent);
    });

    const deleteButtons = agentsListNode.querySelectorAll('.delete-agent-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', handleDeleteAgent);
    });

    mainContent.appendChild(agentsListNode);
}

async function showAgentDetailView(agentId) {
    currentView = 'agent-detail';
    clearMainContent();
    showLoading();

    try {
        const agent = await fetchAgent(agentId);
        selectedAgentId = agentId;

        const agentDetailNode = document.importNode(agentDetailTemplate.content, true);

        // Populate agent details
        agentDetailNode.querySelector('#agent-name').textContent = agent.name;
        agentDetailNode.querySelector('#agent-config').textContent = JSON.stringify(agent.config, null, 2);
        agentDetailNode.querySelector('#agent-code').textContent = agent.code;

        // Add event listeners
        agentDetailNode.querySelector('#back-btn').addEventListener('click', showAgentsListView);
        agentDetailNode.querySelector('#run-btn').addEventListener('click', () => handleRunAgent({ target: { dataset: { agentId } } }));

        mainContent.appendChild(agentDetailNode);
    } catch (error) {
        showError(`Failed to load agent details: ${error.message}`);
        console.error('Error loading agent details:', error);
        showAgentsListView();
    } finally {
        hideLoading();
    }
}

// Event Handlers
async function handleAgentFormSubmit(event) {
    event.preventDefault();
    showLoading();

    try {
        const form = event.target;
        const formData = new FormData(form);

        // Build agent config
        const agentConfig = {
            name: formData.get('name'),
            model: formData.get('model'),
            provider: formData.get('provider'),
            instruction: formData.get('instruction'),
            description: formData.get('description') || '',
            flow: formData.get('flow'),
            temperature: parseFloat(formData.get('temperature')),
        };

        // Add Ollama-specific settings if provider is Ollama
        if (agentConfig.provider === 'ollama') {
            agentConfig.ollama_base_url = formData.get('ollama_base_url') || 'http://localhost:11434';
        }

        // Get selected tools
        const selectedTools = [];
        form.querySelectorAll('input[name="tools"]:checked').forEach(checkbox => {
            selectedTools.push(checkbox.value);
        });
        agentConfig.tools = selectedTools;

        // Create agent
        await createAgent(agentConfig);

        // Refresh agents list and show it
        await fetchAgents();
        showAgentsListView();

        // Show success message
        showSuccess(`Agent '${agentConfig.name}' created successfully!`);
    } catch (error) {
        showError(`Failed to create agent: ${error.message}`);
        console.error('Error creating agent:', error);
    } finally {
        hideLoading();
    }
}

function handleTemplateSelect(event) {
    const templateCard = event.target.closest('.template-card');
    const templateId = templateCard.dataset.templateId;
    const template = templates.find(t => t.id === templateId);

    if (template && template.config) {
        const form = document.getElementById('agent-form');

        // Fill form with template values
        form.querySelector('#name').value = template.config.name;

        // Set provider and update models
        const providerSelect = form.querySelector('#provider');
        providerSelect.value = template.config.provider || 'google';

        // Trigger change event to update models
        const event = new Event('change');
        providerSelect.dispatchEvent(event);

        // Set model after models are updated
        setTimeout(() => {
            form.querySelector('#model').value = template.config.model;
        }, 100);

        // Set other fields
        form.querySelector('#description').value = template.config.description || '';
        form.querySelector('#instruction').value = template.config.instruction;
        form.querySelector('#flow').value = template.config.flow || 'auto';

        // Set Ollama-specific settings if available
        if (template.config.provider === 'ollama') {
            form.querySelector('#ollama_base_url').value = template.config.ollama_base_url || 'http://localhost:11434';
            form.querySelector('.ollama-settings').classList.remove('d-none');
        } else {
            form.querySelector('.ollama-settings').classList.add('d-none');
        }

        const temperatureInput = form.querySelector('#temperature');
        temperatureInput.value = template.config.temperature || 0.2;
        form.querySelector('#temperature-value').textContent = `Current: ${temperatureInput.value}`;

        // Check tools
        form.querySelectorAll('input[name="tools"]').forEach(checkbox => {
            checkbox.checked = template.config.tools && template.config.tools.includes(checkbox.value);
        });

        // Scroll to form
        form.scrollIntoView({ behavior: 'smooth' });
    }
}

async function handleViewAgent(event) {
    const agentId = event.target.closest('.view-agent-btn').dataset.agentId;
    await showAgentDetailView(agentId);
}

async function handleRunAgent(event) {
    const agentId = event.target.closest('[data-agent-id]').dataset.agentId;
    showLoading();

    try {
        const result = await runAgent(agentId);
        alert(`Agent launched! Run this command to start: ${result.command}`);
    } catch (error) {
        showError(`Failed to run agent: ${error.message}`);
        console.error('Error running agent:', error);
    } finally {
        hideLoading();
    }
}

async function handleDeleteAgent(event) {
    const agentId = event.target.closest('.delete-agent-btn').dataset.agentId;

    if (confirm(`Are you sure you want to delete agent '${agentId}'?`)) {
        showLoading();

        try {
            await deleteAgent(agentId);
            await fetchAgents();
            showAgentsListView();
            showSuccess(`Agent '${agentId}' deleted successfully!`);
        } catch (error) {
            showError(`Failed to delete agent: ${error.message}`);
            console.error('Error deleting agent:', error);
        } finally {
            hideLoading();
        }
    }
}

// Utility Functions
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
    const successContainer = document.createElement('div');
    successContainer.className = 'alert alert-success alert-dismissible fade show';
    successContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    mainContent.insertAdjacentElement('beforebegin', successContainer);
    setTimeout(() => {
        successContainer.remove();
    }, 5000);
}
