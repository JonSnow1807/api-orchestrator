"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
const axios_1 = __importDefault(require("axios"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const socket_io_client_1 = require("socket.io-client");
// API Client for communicating with the backend
class APIOrchestoratorClient {
    constructor() {
        const config = vscode.workspace.getConfiguration('api-orchestrator');
        this.baseUrl = config.get('serverUrl') || 'http://localhost:8000';
    }
    async login(email, password) {
        try {
            const response = await axios_1.default.post(`${this.baseUrl}/auth/login`, {
                username: email,
                password: password
            });
            this.token = response.data.access_token;
            await this.saveToken(this.token || '');
            this.connectWebSocket();
            return true;
        }
        catch (error) {
            return false;
        }
    }
    async logout() {
        this.token = undefined;
        await this.saveToken('');
        if (this.socket) {
            this.socket.disconnect();
        }
    }
    async saveToken(token) {
        await vscode.workspace.getConfiguration().update('api-orchestrator.token', token || '', vscode.ConfigurationTarget.Global);
    }
    connectWebSocket() {
        if (!this.token)
            return;
        this.socket = (0, socket_io_client_1.io)(this.baseUrl, {
            transports: ['websocket'],
            auth: { token: this.token }
        });
        this.socket.on('progress', (data) => {
            vscode.window.showInformationMessage(`Orchestration: ${data.message}`);
        });
        this.socket.on('complete', (data) => {
            vscode.window.showInformationMessage('✅ Orchestration completed!');
        });
    }
    async orchestrate(projectPath) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }
        const config = vscode.workspace.getConfiguration('api-orchestrator');
        const response = await axios_1.default.post(`${this.baseUrl}/api/orchestrate`, {
            source_path: projectPath,
            framework: 'auto',
            include_tests: config.get('includeTests'),
            include_mock: config.get('includeMockServer'),
            include_ai_analysis: config.get('includeAiAnalysis')
        }, {
            headers: { Authorization: `Bearer ${this.token}` }
        });
        return response.data;
    }
    async scanFile(filePath) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }
        const content = fs.readFileSync(filePath, 'utf-8');
        const ext = path.extname(filePath);
        let framework = 'unknown';
        // Detect framework from file content
        if (ext === '.py') {
            if (content.includes('from fastapi'))
                framework = 'fastapi';
            else if (content.includes('from flask'))
                framework = 'flask';
            else if (content.includes('from django'))
                framework = 'django';
        }
        else if (ext === '.js' || ext === '.ts') {
            if (content.includes('express'))
                framework = 'express';
        }
        const response = await axios_1.default.post(`${this.baseUrl}/api/scan/file`, {
            file_path: filePath,
            content: content,
            framework: framework
        }, {
            headers: { Authorization: `Bearer ${this.token}` }
        });
        return response.data;
    }
    async startMockServer(specPath, port = 3000) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }
        const spec = JSON.parse(fs.readFileSync(specPath, 'utf-8'));
        const response = await axios_1.default.post(`${this.baseUrl}/api/mock/start`, {
            spec: spec,
            port: port
        }, {
            headers: { Authorization: `Bearer ${this.token}` }
        });
        return response.data;
    }
    async getTaskStatus(taskId) {
        if (!this.token) {
            throw new Error('Not authenticated');
        }
        const response = await axios_1.default.get(`${this.baseUrl}/api/tasks/${taskId}`, {
            headers: { Authorization: `Bearer ${this.token}` }
        });
        return response.data;
    }
}
// Tree Data Provider for the sidebar views
class ApiEndpointsProvider {
    constructor() {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.endpoints = [];
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    addEndpoint(endpoint) {
        this.endpoints.push(endpoint);
        this.refresh();
    }
    clearEndpoints() {
        this.endpoints = [];
        this.refresh();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!element) {
            return Promise.resolve(this.endpoints);
        }
        return Promise.resolve([]);
    }
}
class ApiEndpoint extends vscode.TreeItem {
    constructor(label, method, path, collapsibleState) {
        super(label, collapsibleState);
        this.label = label;
        this.method = method;
        this.path = path;
        this.collapsibleState = collapsibleState;
        this.tooltip = `${this.method} ${this.path}`;
        this.description = this.path;
        this.iconPath = this.getIcon(method);
    }
    getIcon(method) {
        switch (method.toUpperCase()) {
            case 'GET': return new vscode.ThemeIcon('arrow-down');
            case 'POST': return new vscode.ThemeIcon('arrow-up');
            case 'PUT': return new vscode.ThemeIcon('edit');
            case 'DELETE': return new vscode.ThemeIcon('trash');
            default: return new vscode.ThemeIcon('circle');
        }
    }
}
// Status Bar Item
class StatusBarManager {
    constructor() {
        this.isAuthenticated = false;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'api-orchestrator.showDashboard';
        this.updateStatus();
        this.statusBarItem.show();
    }
    updateStatus(isAuthenticated = false, message = '') {
        this.isAuthenticated = isAuthenticated;
        if (isAuthenticated) {
            this.statusBarItem.text = `$(globe) API Orchestrator${message ? ': ' + message : ''}`;
            this.statusBarItem.backgroundColor = undefined;
        }
        else {
            this.statusBarItem.text = '$(globe) API Orchestrator (Not Connected)';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
    }
    dispose() {
        this.statusBarItem.dispose();
    }
}
function activate(context) {
    console.log('API Orchestrator extension is now active!');
    const client = new APIOrchestoratorClient();
    const apiEndpointsProvider = new ApiEndpointsProvider();
    const statusBar = new StatusBarManager();
    // Register tree data providers
    vscode.window.registerTreeDataProvider('apiEndpoints', apiEndpointsProvider);
    // Command: Login
    const loginCommand = vscode.commands.registerCommand('api-orchestrator.login', async () => {
        const email = await vscode.window.showInputBox({
            prompt: 'Enter your email',
            placeHolder: 'email@example.com'
        });
        if (!email)
            return;
        const password = await vscode.window.showInputBox({
            prompt: 'Enter your password',
            password: true
        });
        if (!password)
            return;
        const success = await client.login(email, password);
        if (success) {
            vscode.window.showInformationMessage('✅ Successfully logged in to API Orchestrator');
            statusBar.updateStatus(true);
        }
        else {
            vscode.window.showErrorMessage('Failed to login. Please check your credentials.');
        }
    });
    // Command: Logout
    const logoutCommand = vscode.commands.registerCommand('api-orchestrator.logout', async () => {
        await client.logout();
        vscode.window.showInformationMessage('Logged out from API Orchestrator');
        statusBar.updateStatus(false);
        apiEndpointsProvider.clearEndpoints();
    });
    // Command: Scan Project
    const scanCommand = vscode.commands.registerCommand('api-orchestrator.scan', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }
        try {
            statusBar.updateStatus(true, 'Scanning...');
            await vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Scanning project for APIs...",
                cancellable: false
            }, async (progress) => {
                progress.report({ increment: 0 });
                const result = await client.orchestrate(workspaceFolders[0].uri.fsPath);
                progress.report({ increment: 50, message: "Processing results..." });
                // Clear existing endpoints
                apiEndpointsProvider.clearEndpoints();
                // Add discovered endpoints to the tree view
                if (result.endpoints) {
                    result.endpoints.forEach((endpoint) => {
                        apiEndpointsProvider.addEndpoint(new ApiEndpoint(`${endpoint.method} ${endpoint.path}`, endpoint.method, endpoint.path, vscode.TreeItemCollapsibleState.None));
                    });
                }
                progress.report({ increment: 100 });
                vscode.window.showInformationMessage(`✅ Discovered ${result.endpoints?.length || 0} API endpoints`);
            });
            statusBar.updateStatus(true);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Scan failed: ${error.message}`);
            statusBar.updateStatus(true);
        }
    });
    // Command: Scan Current File
    const scanFileCommand = vscode.commands.registerCommand('api-orchestrator.scanFile', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No file open');
            return;
        }
        try {
            statusBar.updateStatus(true, 'Scanning file...');
            const result = await client.scanFile(editor.document.fileName);
            if (result.endpoints && result.endpoints.length > 0) {
                vscode.window.showInformationMessage(`Found ${result.endpoints.length} API endpoints in this file`);
                // Add to tree view
                result.endpoints.forEach((endpoint) => {
                    apiEndpointsProvider.addEndpoint(new ApiEndpoint(`${endpoint.method} ${endpoint.path}`, endpoint.method, endpoint.path, vscode.TreeItemCollapsibleState.None));
                });
            }
            else {
                vscode.window.showInformationMessage('No API endpoints found in this file');
            }
            statusBar.updateStatus(true);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Scan failed: ${error.message}`);
            statusBar.updateStatus(true);
        }
    });
    // Command: Generate OpenAPI Spec
    const generateSpecCommand = vscode.commands.registerCommand('api-orchestrator.generateSpec', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }
        try {
            statusBar.updateStatus(true, 'Generating spec...');
            const result = await client.orchestrate(workspaceFolders[0].uri.fsPath);
            // Save the spec to a file
            const outputPath = path.join(workspaceFolders[0].uri.fsPath, 'api-output', 'openapi.json');
            if (!fs.existsSync(path.dirname(outputPath))) {
                fs.mkdirSync(path.dirname(outputPath), { recursive: true });
            }
            fs.writeFileSync(outputPath, JSON.stringify(result.spec, null, 2));
            // Open the generated spec
            const doc = await vscode.workspace.openTextDocument(outputPath);
            await vscode.window.showTextDocument(doc);
            vscode.window.showInformationMessage(`✅ OpenAPI spec generated: ${outputPath}`);
            statusBar.updateStatus(true);
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to generate spec: ${error.message}`);
            statusBar.updateStatus(true);
        }
    });
    // Command: Start Mock Server
    const startMockServerCommand = vscode.commands.registerCommand('api-orchestrator.startMockServer', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }
        const specPath = path.join(workspaceFolders[0].uri.fsPath, 'api-output', 'openapi.json');
        if (!fs.existsSync(specPath)) {
            vscode.window.showErrorMessage('No OpenAPI spec found. Please generate one first.');
            return;
        }
        const port = await vscode.window.showInputBox({
            prompt: 'Enter port for mock server',
            value: '3000',
            validateInput: (value) => {
                const p = parseInt(value);
                return p > 0 && p < 65536 ? null : 'Invalid port';
            }
        });
        if (!port)
            return;
        try {
            statusBar.updateStatus(true, 'Starting mock...');
            const result = await client.startMockServer(specPath, parseInt(port));
            vscode.window.showInformationMessage(`✅ Mock server started at http://localhost:${port}`);
            // Open in browser
            vscode.env.openExternal(vscode.Uri.parse(`http://localhost:${port}`));
            statusBar.updateStatus(true, 'Mock running');
        }
        catch (error) {
            vscode.window.showErrorMessage(`Failed to start mock server: ${error.message}`);
            statusBar.updateStatus(true);
        }
    });
    // Command: Generate Tests
    const generateTestsCommand = vscode.commands.registerCommand('api-orchestrator.generateTests', async () => {
        vscode.window.showInformationMessage('Generating test suites...');
        // Implementation would follow similar pattern
    });
    // Command: AI Analysis
    const aiAnalyzeCommand = vscode.commands.registerCommand('api-orchestrator.aiAnalyze', async () => {
        vscode.window.showInformationMessage('Running AI security and performance analysis...');
        // Implementation would follow similar pattern
    });
    // Command: Show Dashboard
    const showDashboardCommand = vscode.commands.registerCommand('api-orchestrator.showDashboard', async () => {
        const panel = vscode.window.createWebviewPanel('apiOrchestratorDashboard', 'API Orchestrator Dashboard', vscode.ViewColumn.One, {
            enableScripts: true
        });
        panel.webview.html = getDashboardWebviewContent();
    });
    // Auto-scan on save
    const onSaveEvent = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('api-orchestrator');
        if (!config.get('autoScan'))
            return;
        const ext = path.extname(document.fileName);
        if (['.py', '.js', '.ts', '.java', '.go', '.rb'].includes(ext)) {
            try {
                await client.scanFile(document.fileName);
            }
            catch (error) {
                // Silent fail for auto-scan
            }
        }
    });
    // Register all commands
    context.subscriptions.push(loginCommand, logoutCommand, scanCommand, scanFileCommand, generateSpecCommand, startMockServerCommand, generateTestsCommand, aiAnalyzeCommand, showDashboardCommand, onSaveEvent, statusBar);
    // Show welcome message
    vscode.window.showInformationMessage('API Orchestrator is ready! Click here to login.', 'Login').then(selection => {
        if (selection === 'Login') {
            vscode.commands.executeCommand('api-orchestrator.login');
        }
    });
}
exports.activate = activate;
function getDashboardWebviewContent() {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API Orchestrator Dashboard</title>
        <style>
            body {
                font-family: var(--vscode-font-family);
                padding: 20px;
                color: var(--vscode-foreground);
                background-color: var(--vscode-editor-background);
            }
            h1 {
                color: var(--vscode-foreground);
                border-bottom: 2px solid var(--vscode-panel-border);
                padding-bottom: 10px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: var(--vscode-editor-background);
                border: 1px solid var(--vscode-panel-border);
                border-radius: 4px;
                padding: 15px;
            }
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: var(--vscode-textLink-foreground);
            }
            .stat-label {
                color: var(--vscode-descriptionForeground);
                margin-top: 5px;
            }
            button {
                background: var(--vscode-button-background);
                color: var(--vscode-button-foreground);
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: var(--vscode-button-hoverBackground);
            }
            .actions {
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <h1>🚀 API Orchestrator Dashboard</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">0</div>
                <div class="stat-label">APIs Discovered</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">0</div>
                <div class="stat-label">Mock Servers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">0</div>
                <div class="stat-label">Tests Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">--</div>
                <div class="stat-label">Security Score</div>
            </div>
        </div>

        <div class="actions">
            <h2>Quick Actions</h2>
            <button onclick="scanProject()">🔍 Scan Project</button>
            <button onclick="generateSpec()">📄 Generate OpenAPI Spec</button>
            <button onclick="startMock()">🎭 Start Mock Server</button>
            <button onclick="generateTests()">🧪 Generate Tests</button>
            <button onclick="aiAnalysis()">🤖 AI Analysis</button>
        </div>

        <script>
            const vscode = acquireVsCodeApi();
            
            function scanProject() {
                vscode.postMessage({ command: 'scan' });
            }
            
            function generateSpec() {
                vscode.postMessage({ command: 'generateSpec' });
            }
            
            function startMock() {
                vscode.postMessage({ command: 'startMock' });
            }
            
            function generateTests() {
                vscode.postMessage({ command: 'generateTests' });
            }
            
            function aiAnalysis() {
                vscode.postMessage({ command: 'aiAnalysis' });
            }
        </script>
    </body>
    </html>`;
}
function deactivate() {
    console.log('API Orchestrator extension deactivated');
}
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map