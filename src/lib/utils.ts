import fs from 'fs';
import path from 'path';
import { STATUS_DIR } from './config';
import axios from 'axios';

export function getTaskStatusPath(taskId: string): string {
  return path.join(STATUS_DIR, `${taskId}.json`);
}

export function getTaskLogPath(taskId: string): string {
  return path.join(STATUS_DIR, `${taskId}.log`);
}

export function updateTaskStatus(taskId: string, updates: Record<string, any>) {
  const statusPath = getTaskStatusPath(taskId);
  let statusData: Record<string, any> = { id: taskId, created_at: new Date().toISOString() };

  if (fs.existsSync(statusPath)) {
    try {
      statusData = JSON.parse(fs.readFileSync(statusPath, 'utf8'));
    } catch (e) {
      // Ignore corrupted file
    }
  }

  statusData = { ...statusData, ...updates, updated_at: new Date().toISOString() };
  fs.writeFileSync(statusPath, JSON.stringify(statusData, null, 4));
}

export async function getWorkingProxy(logFile: string): Promise<string | null> {
  const proxyListUrl = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt";
  fs.appendFileSync(logFile, "Fetching proxy list...\n");
  
  try {
    const response = await axios.get(proxyListUrl);
    const proxies = response.data.split('\n').filter((p: string) => p.trim());
    
    // Simple implementation: try a few random ones
    const sampled = proxies.sort(() => 0.5 - Math.random()).slice(0, 50);
    fs.appendFileSync(logFile, `Testing ${sampled.length} proxies...\n`);

    for (const proxy of sampled) {
      try {
        await axios.get("https://www.google.com", {
          proxy: {
            host: proxy.split(':')[0],
            port: parseInt(proxy.split(':')[1])
          },
          timeout: 5000
        });
        fs.appendFileSync(logFile, `Found working proxy: ${proxy}\n`);
        return proxy;
      } catch (e) {
        continue;
      }
    }
  } catch (e) {
    fs.appendFileSync(logFile, `Error fetching proxies: ${e}\n`);
  }
  
  return null;
}

export function createRcloneConfig(taskId: string, service: string, params: Record<string, any>): string {
  const configPath = path.join(STATUS_DIR, `${taskId}_rclone.conf`);
  let configContent = '[remote]\n';

  if (service === 'onedrive') {
    configContent += 'type = onedrive\n';
    configContent += `token = ${params.onedrive_token}\n`;
    configContent += `drive_id = ${params.onedrive_drive_id}\n`;
    configContent += `drive_type = ${params.onedrive_drive_type}\n`;
  } else if (service === 'googledrive') {
    configContent += 'type = drive\n';
    configContent += `token = ${params.googledrive_token}\n`;
    configContent += `team_drive = ${params.googledrive_team_drive || ''}\n`;
  } else if (service === 'alist') {
    configContent += 'type = webdav\n';
    configContent += `url = ${params.alist_url}\n`;
    configContent += `vendor = other\n`;
    configContent += `user = ${params.alist_user}\n`;
    configContent += `pass = ${params.alist_pass}\n`; // Note: rclone pass is usually obscured
  }
  // Add more services as needed

  fs.writeFileSync(configPath, configContent);
  return configPath;
}

export function generateArchiveName(url: string): string {
    const domainMatch = url.match(/https?:\/\/(?:www\.)?([^\/]+)/);
    const domain = domainMatch ? domainMatch[1].replace(/\./g, '_') : 'download';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    return `${domain}_${timestamp}`;
}
