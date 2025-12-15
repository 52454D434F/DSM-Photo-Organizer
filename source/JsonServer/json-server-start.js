#!/usr/bin/env node
/**
    * JSON Server Start Script
 * Reads config.ini and starts jsonserver with the configured settings
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Default paths
const PACKAGE_VAR_DIR = process.env.PACKAGE_VAR_DIR || '/var/packages/JsonServer/var';
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
        
        // Check if directory exists
        if (!fs.existsSync(dir)) {
            try {
                fs.mkdirSync(dir, { recursive: true });
            } catch (error) {
                console.error(`ERROR: Cannot create directory ${dir}: ${error.message}`);
                console.error(`Please ensure the directory exists and the package user has write permissions.`);
                process.exit(1);
            }
        }
        
        // Check if we can write to the directory
        try {
            const testFile = path.join(dir, '.json-server-test-' + Date.now());
            fs.writeFileSync(testFile, 'test');
            fs.unlinkSync(testFile);
        } catch (error) {
            console.error(`ERROR: Cannot write to directory ${dir}: ${error.message}`);
            console.error(`Permission denied. The JsonServer package user needs write access to this directory.`);
            console.error(``);
            console.error(`SOLUTION: Grant Read/Write permissions to the JsonServer user:`);
            console.error(`  1. Open Control Panel > Shared Folder`);
            console.error(`  2. Find the shared folder containing: ${dir}`);
            console.error(`  3. Click Edit > Permissions tab`);
            console.error(`  4. Select "System internal user"`);
            console.error(`  5. Find "JsonServer" user and set to "Read/Write"`);
            console.error(`  6. Click OK and restart the service`);
            console.error(``);
            console.error(`Alternative: Use the default location: /var/packages/JsonServer/var/data`);
            process.exit(1);
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
        
        try {
            fs.writeFileSync(dbPath, JSON.stringify(defaultDb, null, 2));
            console.log(`Created default db.json at ${dbPath}`);
        } catch (error) {
            console.error(`ERROR: Cannot create database file ${dbPath}: ${error.message}`);
            console.error(`Permission denied. The JsonServer package user needs write access.`);
            console.error(`SOLUTION: Grant Read/Write permissions via Control Panel > Shared Folder > [folder] > Edit > Permissions > System internal user > JsonServer > Read/Write`);
            process.exit(1);
        }
    } else {
        // File exists, check if it's readable and writable (json-server needs to write to it)
        try {
            fs.accessSync(dbPath, fs.constants.R_OK | fs.constants.W_OK);
        } catch (error) {
            console.error(`ERROR: Database file exists but is not readable/writable: ${dbPath}`);
            console.error(`Permission denied. json-server needs write access to update the database.`);
            console.error(`SOLUTION: Grant Read/Write permissions via Control Panel > Shared Folder > [folder] > Edit > Permissions > System internal user > JsonServer > Read/Write`);
            process.exit(1);
        }
    }
}

// Find json-server binary and return both the command and args
function findJsonServer() {
    // Try local node_modules .bin first (usually a symlink or script)
    const localBin = path.join(PACKAGE_VAR_DIR, 'node_modules', '.bin', 'json-server');
    if (fs.existsSync(localBin)) {
        return { command: localBin, args: [] };
    }
    
    // Try alternative local path - use node to run the script directly
    const localBinAlt = path.join(PACKAGE_VAR_DIR, 'node_modules', 'json-server', 'lib', 'bin.js');
    if (fs.existsSync(localBinAlt)) {
        return { command: process.execPath, args: [localBinAlt] };
    }
    
    // Try global installation
    const globalBin = '/usr/local/bin/json-server';
    if (fs.existsSync(globalBin)) {
        return { command: globalBin, args: [] };
    }
    
    // Try to find in PATH
    return { command: 'json-server', args: [] };
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
    const { command: jsonServerBin, args: jsonServerArgs } = findJsonServer();
    console.log(`Using json-server: ${jsonServerBin}`);
    
    // Build arguments
    const args = [
        ...jsonServerArgs,
        config.dbFile,
        '--watch',  // Watch for file changes and reload automatically
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
        console.error(`Attempted command: ${jsonServerBin} ${args.join(' ')}`);
        console.error(`PACKAGE_VAR_DIR: ${PACKAGE_VAR_DIR}`);
        console.error(`Checking paths:`);
        console.error(`  .bin/json-server: ${fs.existsSync(path.join(PACKAGE_VAR_DIR, 'node_modules', '.bin', 'json-server'))}`);
        console.error(`  lib/bin.js: ${fs.existsSync(path.join(PACKAGE_VAR_DIR, 'node_modules', 'json-server', 'lib', 'bin.js'))}`);
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
