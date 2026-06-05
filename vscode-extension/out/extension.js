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
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const readline = __importStar(require("readline"));
let diagnosticCollection;
function activate(context) {
    console.log('Django N+1 Hunter extension is now active!');
    diagnosticCollection = vscode.languages.createDiagnosticCollection('django-nplus1-hunter');
    context.subscriptions.push(diagnosticCollection);
    const logFileName = vscode.workspace.getConfiguration('djangoNPlus1Hunter').get('logFile') || '.nplus1-hunter.jsonl';
    // Watch for changes in the workspace
    const watcher = vscode.workspace.createFileSystemWatcher(`**/${logFileName}`);
    watcher.onDidChange(uri => {
        processLogFile(uri.fsPath);
    });
    watcher.onDidCreate(uri => {
        processLogFile(uri.fsPath);
    });
    context.subscriptions.push(watcher);
    // Initial load if file exists
    vscode.workspace.findFiles(`**/${logFileName}`).then(uris => {
        if (uris.length > 0) {
            processLogFile(uris[0].fsPath);
        }
    });
}
async function processLogFile(filePath) {
    try {
        const fileStream = fs.createReadStream(filePath);
        const rl = readline.createInterface({
            input: fileStream,
            crlfDelay: Infinity
        });
        const diagnosticsMap = new Map();
        // Clear existing collection
        diagnosticCollection.clear();
        for await (const line of rl) {
            if (!line.trim())
                continue;
            try {
                const event = JSON.parse(line);
                const uri = vscode.Uri.file(event.file);
                // Line numbers from Python tracebacks are 1-indexed, VS Code ranges are 0-indexed
                const lineNumber = Math.max(0, event.line - 1);
                // We'll highlight the entire line
                const range = new vscode.Range(lineNumber, 0, lineNumber, 1000);
                const message = `N+1 Query Detected! ${event.count} queries took ${event.duration.toFixed(4)}s in ${event.function}.\n\nTip: ${event.tip}`;
                const diagnostic = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Warning);
                diagnostic.source = 'django-nplus1-hunter';
                diagnostic.code = 'N+1';
                const diags = diagnosticsMap.get(uri.toString()) || [];
                diags.push(diagnostic);
                diagnosticsMap.set(uri.toString(), diags);
            }
            catch (e) {
                console.error('Failed to parse JSON line:', e);
            }
        }
        // Apply diagnostics
        for (const [uriString, diags] of diagnosticsMap.entries()) {
            diagnosticCollection.set(vscode.Uri.parse(uriString), diags);
        }
    }
    catch (e) {
        console.error('Failed to read log file:', e);
    }
}
function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
}
//# sourceMappingURL=extension.js.map