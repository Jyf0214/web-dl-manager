import sqlite3 from 'sqlite3';
import path from 'path';
import fs from 'fs';

const DB_PATH = path.resolve(process.cwd(), 'webdl-manager.db');

// 初始化数据库
const db = new sqlite3.Database(DB_PATH);

db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT UNIQUE NOT NULL,
    key_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )`);
  
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )`);
});

export const db_config = {
  get: (key: string, defaultValue: string = ''): Promise<string> => {
    return new Promise((resolve) => {
      db.get('SELECT key_value FROM config WHERE key_name = ?', [key], (err, row: any) => {
        if (err || !row) resolve(defaultValue);
        else resolve(row.key_value);
      });
    });
  },
  
  set: (key: string, value: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      db.run(
        `INSERT INTO config (key_name, key_value, updated_at) 
         VALUES (?, ?, CURRENT_TIMESTAMP)
         ON CONFLICT(key_name) DO UPDATE SET key_value = excluded.key_value, updated_at = CURRENT_TIMESTAMP`,
        [key, value],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  },

  getAll: (): Promise<Record<string, string>> => {
    return new Promise((resolve) => {
      db.all('SELECT key_name, key_value FROM config', [], (err, rows: any[]) => {
        if (err) resolve({});
        const config: Record<string, string> = {};
        rows?.forEach(row => {
          config[row.key_name] = row.key_value;
        });
        resolve(config);
      });
    });
  }
};
