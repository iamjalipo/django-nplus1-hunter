import * as vscode from 'vscode';
import * as fs from 'fs';
import * as readline from 'readline';

let diagnosticCollection: vscode.DiagnosticCollection;

export function activate(context: vscode.ExtensionContext) {
    console.log('Django N+1 Hunter extension is now active!');

    diagnosticCollection = vscode.languages.createDiagnosticCollection('django-nplus1-hunter');
    context.subscriptions.push(diagnosticCollection);

    const logFileName = vscode.workspace.getConfiguration('djangoNPlus1Hunter').get<string>('logFile') || '.nplus1-hunter.jsonl';
    
    // Watch for changes in the workspace
    const watcher = vscode.workspace.createFileSystemWatcher(`**/${logFileName}`);
    
    watcher.onDidChange(uri => {
        processLogFile(uri.fsPath);
    });

    watcher.onDidCreate(uri => {
        processLogFile(uri.fsPath);
    });

    watcher.onDidDelete(uri => {
        diagnosticCollection.clear();
    });

    context.subscriptions.push(watcher);

    // Initial load if file exists
    vscode.workspace.findFiles(`**/${logFileName}`).then(uris => {
        if (uris.length > 0) {
            processLogFile(uris[0].fsPath);
        }
    });
}

interface NPlus1Event {
    timestamp: number;
    file: string;
    line: number;
    function: string;
    count: number;
    duration: number;
    sql: string;
    tip: string;
}

async function processLogFile(filePath: string) {
    try {
        const fileStream = fs.createReadStream(filePath);
        const rl = readline.createInterface({
            input: fileStream,
            crlfDelay: Infinity
        });

        const diagnosticsMap = new Map<string, vscode.Diagnostic[]>();

        // Clear existing collection
        diagnosticCollection.clear();

        for await (const line of rl) {
            if (!line.trim()) continue;

            try {
                const event = JSON.parse(line) as NPlus1Event;
                const uri = vscode.Uri.file(event.file);
                
                // Line numbers from Python tracebacks are 1-indexed, VS Code ranges are 0-indexed
                const lineNumber = Math.max(0, (event.line || 1) - 1);
                
                // We'll highlight the entire line
                const range = new vscode.Range(lineNumber, 0, lineNumber, 1000);
                
                const message = `N+1 Query Detected! ${event.count} queries took ${(event.duration || 0).toFixed(4)}s in ${event.function}.\n\nTip: ${event.tip}`;
                
                const diagnostic = new vscode.Diagnostic(
                    range,
                    message,
                    vscode.DiagnosticSeverity.Warning
                );

                diagnostic.source = 'django-nplus1-hunter';
                diagnostic.code = 'N+1';

                const diags = diagnosticsMap.get(uri.toString()) || [];
                diags.push(diagnostic);
                diagnosticsMap.set(uri.toString(), diags);
            } catch (e) {
                console.error('Failed to parse JSON line:', e);
            }
        }

        // Apply diagnostics
        for (const [uriString, diags] of diagnosticsMap.entries()) {
            diagnosticCollection.set(vscode.Uri.parse(uriString), diags);
        }

    } catch (e) {
        console.error('Failed to read log file:', e);
    }
}

export function deactivate() {
    if (diagnosticCollection) {
        diagnosticCollection.clear();
        diagnosticCollection.dispose();
    }
}
