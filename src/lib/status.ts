import si from 'systeminformation';
import fs from 'fs';
import path from 'path';
import { STATUS_DIR } from './config';

export async function getSystemStatus() {
  const [cpu, mem, disk] = await Promise.all([
    si.currentLoad(),
    si.mem(),
    si.fsSize()
  ]);

  const dataDisk = disk.find(d => d.mount === '/data') || disk[0];

  return {
    uptime: si.time().uptime,
    cpu_usage: cpu.currentLoad,
    memory: {
      total: mem.total,
      used: mem.used,
      free: mem.free,
      percent: (mem.used / mem.total) * 100
    },
    disk: {
      total: dataDisk?.size || 0,
      used: dataDisk?.used || 0,
      free: dataDisk?.available || 0,
      percent: dataDisk?.use || 0
    }
  };
}

export async function getAllTasks() {
  if (!fs.existsSync(STATUS_DIR)) return [];

  const files = fs.readdirSync(STATUS_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      const fullPath = path.join(STATUS_DIR, f);
      const stats = fs.statSync(fullPath);
      return { name: f, path: fullPath, mtime: stats.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);

  const tasks = [];
  for (const file of files) {
    try {
      const content = fs.readFileSync(file.path, 'utf8');
      tasks.push(JSON.parse(content));
    } catch (e) {
      console.error(`Error reading task file ${file.name}:`, e);
    }
  }
  return tasks;
}
