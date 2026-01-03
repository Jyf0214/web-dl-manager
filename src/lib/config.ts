import path from 'path';
import os from 'os';

export const PROJECT_ROOT = process.cwd();
export const DATA_DIR = process.env.DATA_DIR || path.join(PROJECT_ROOT, 'data');
export const DOWNLOADS_DIR = path.join(DATA_DIR, 'downloads');
export const ARCHIVES_DIR = path.join(DATA_DIR, 'archives');
export const STATUS_DIR = path.join(DATA_DIR, 'status');
export const LOGS_DIR = path.join(PROJECT_ROOT, 'logs');

// Ensure directories exist
const dirs = [DATA_DIR, DOWNLOADS_DIR, ARCHIVES_DIR, STATUS_DIR, LOGS_DIR];
import fs from 'fs';
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

export const APP_USERNAME = process.env.APP_USERNAME || '';
export const APP_PASSWORD = process.env.APP_PASSWORD || '';
export const DEBUG_MODE = process.env.DEBUG_MODE?.toLowerCase() === 'true';
