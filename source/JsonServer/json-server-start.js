#!/usr/bin/env node
/**
 * JSON Server Start Script
 * Reads config.ini and starts json-server with the configured settings
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Default paths
const PACKAGE_VAR_DIR = process.env.PACKAGE_VAR_DIR || '/var/packages/Json-Server/var';
const CONFIG_FILE = path.join(PACKAGE_VAR_DIR, 'config.ini');
const DATA_DIR = path.join(PACKAGE_VAR_DIR, 'data');
const DEFAULT_DB_FILE = path.join(DATA_DIR, 'db.json');
const DEFAULT_PORT = 3000;

// Parse config.ini file
function parseConfigFile(configPath) {
    const config = {
        port: DEFAULT_PORT,
        dbFile: DEFAULT_DB_FILE
    };

    if (!fs.existsSync(configPath)) {
        console.error(`Config file not found: ${configPath}`);
        return config;
    }

    try {
        const content = fs.readFileSync(configPath, 'utf8');
        const lines = content.split('\n');
        
        let currentSection = '';
        for (const line of lines) {
            const trimmed = line.trim();
            
            // Skip empty lines and comments
            if (!trimmed || trimmed.startsWith('#')) {
                continue;
            }
            
            // Check for section headers
            if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
                currentSection = trimmed.slice(1, -1).toLowerCase();
                continue;
            }
            
            // Parse key=value pairs
            const match = trimmed.match(/^([^=]+)=(.*)$/);
            if (match) {
                const key = match[1].trim().toLowerCase();
                const value = match[2].trim();
                
                if (currentSection === 'server' && key === 'port') {
                    config.port = parseInt(value, 10) || DEFAULT_PORT;
                } else if (currentSection === 'database' && key === 'db_file') {
                    config.dbFile = value;
                }
            }
        }
    } catch (error) {
        console.error(`Error reading config file: ${error.message}`);
    }

    return config;
}

// Ensure db.json exists
function ensureDbFile(dbPath) {
    if (!fs.existsSync(dbPath)) {
        const dir = path.dirname(dbPath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        // Default db.json content
        const defaultDb = {
            "posts": [
                {
                    "id": 1,
                    "title": "Post 1",
                    "author": "John"
                },
                {
                    "id": 2,
                    "title": "Post 2",
                    "author": "Doe"
                }
            ],
            "comments": [
                {
                    "id": 1,
                    "body": "This is a comment",
                    "postId": 1
                },
                {
                    "id": 2,
                    "body": "This is the second comment",
                    "postId": 2
                }
            ],
            "profile": {
                "name": "John Doe"
            }
        };
        
        fs.writeFileSync(dbPath, JSON.stringify(defaultDb, null, 2));
        console.log(`Created default db.json at ${dbPath}`);
    }
}

// Find json-server binary
function findJsonServer() {
    // Try local node_modules first
    const localBin = path.join(PACKAGE_VAR_DIR, 'node_modules', '.bin', 'json-server');
    if (fs.existsSync(localBin)) {
        return localBin;
    }
    
    // Try global installation
    const globalBin = '/usr/local/bin/json-server';
    if (fs.existsSync(globalBin)) {
        return globalBin;
    }
    
    // Try to find in PATH
    return 'json-server';
}

// Main function
function main() {
    console.log('Starting JSON Server...');
    
    // Parse configuration
    const config = parseConfigFile(CONFIG_FILE);
    console.log(`Configuration loaded: port=${config.port}, db=${config.dbFile}`);
    
    // Ensure db.json exists
    ensureDbFile(config.dbFile);
    
    // Verify db.json exists
    if (!fs.existsSync(config.dbFile)) {
        console.error(`Database file not found: ${config.dbFile}`);
        process.exit(1);
    }
    
    // Find json-server binary
    const jsonServerBin = findJsonServer();
    console.log(`Using json-server: ${jsonServerBin}`);
    
    // Start json-server
    const args = [
        config.dbFile,
        '--port', config.port.toString(),
        '--host', '0.0.0.0'  // Listen on all interfaces
    ];
    
    console.log(`Starting json-server with args: ${args.join(' ')}`);
    
    const child = spawn(jsonServerBin, args, {
        stdio: 'inherit',
        env: process.env
    });
    
    child.on('error', (error) => {
        console.error(`Failed to start json-server: ${error.message}`);
        process.exit(1);
    });
    
    child.on('exit', (code) => {
        console.log(`json-server exited with code ${code}`);
        process.exit(code || 0);
    });
    
    // Handle termination signals
    process.on('SIGTERM', () => {
        console.log('Received SIGTERM, shutting down...');
        child.kill('SIGTERM');
    });
    
    process.on('SIGINT', () => {
        console.log('Received SIGINT, shutting down...');
        child.kill('SIGINT');
    });
}

main();
