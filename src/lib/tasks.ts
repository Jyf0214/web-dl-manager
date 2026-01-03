import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import { 
  DOWNLOADS_DIR, 
  ARCHIVES_DIR 
} from './config';
import { 
  updateTaskStatus, 
  getTaskLogPath, 
  getWorkingProxy, 
  createRcloneConfig, 
  generateArchiveName 
} from './utils';

async function runCommand(
  command: string, 
  args: string[], 
  logFile: string, 
  taskId: string,
  envExtra: Record<string, string> = {}
): Promise<void> {
  return new Promise((resolve, reject) => {
    const stream = fs.createWriteStream(logFile, { flags: 'a' });
    stream.write(`\n[Executing] ${command} ${args.join(' ')}\n`);

    const child = spawn(command, args, {
      shell: true,
      env: { ...process.env, ...envExtra }
    });

    child.stdout?.on('data', (data) => stream.write(data));
    child.stderr?.on('data', (data) => stream.write(data));

    child.on('close', (code) => {
      if (code === 0) {
        stream.write(`\n[Success] Command finished successfully.\n`);
        resolve();
      } else {
        stream.write(`\n[Error] Command failed with exit code ${code}\n`);
        reject(new Error(`Command failed with code ${code}`));
      }
      stream.end();
    });

    child.on('error', (err) => {
      stream.write(`\n[Exception] ${err.message}\n`);
      reject(err);
      stream.end();
    });
  });
}

export async function processDownloadJob(
  taskId: string,
  url: string,
  params: Record<string, any>
) {
  const taskDownloadDir = path.join(DOWNLOADS_DIR, taskId);
  const archiveName = generateArchiveName(url);
  const logFile = getTaskLogPath(taskId);
  const downloader = params.downloader || 'gallery-dl';
  const service = params.upload_service;
  const uploadPath = params.upload_path;
  const enableCompression = params.enable_compression !== 'false';
  const splitCompression = params.split_compression === 'true';
  const splitSize = parseInt(params.split_size || '1000');

  let archivePaths: string[] = [];
  let rcloneConfigPath: string | null = null;

  try {
    updateTaskStatus(taskId, { status: 'running', url, downloader });
    fs.writeFileSync(logFile, `Starting job ${taskId} for URL: ${url}\n`);

    let proxy = params.proxy;
    if (params.auto_proxy === 'true') {
      proxy = await getWorkingProxy(logFile);
    }

    // 1. Download
    let downloadCmd = '';
    let downloadArgs: string[] = [];

    if (downloader === 'megadl') {
      downloadCmd = 'megadl';
      downloadArgs = [`--path="${taskDownloadDir}"`, `"${url}"`];
      if (params.rate_limit) {
        downloadArgs.unshift(`--limit-speed=${params.rate_limit}`);
      }
    } else {
      downloadCmd = 'gallery-dl';
      downloadArgs = ['--verbose', '-D', `"${taskDownloadDir}"`];
      if (proxy) downloadArgs.push('--proxy', `"${proxy}"`);
      if (params.rate_limit) downloadArgs.push('--limit-rate', `"${params.rate_limit}"`);
      downloadArgs.push(`"${url}"`);
    }

    updateTaskStatus(taskId, { command: `${downloadCmd} ${downloadArgs.join(' ')}` });
    await runCommand(downloadCmd, downloadArgs, logFile, taskId);

    // 2. Compression
    if (!enableCompression) {
      updateTaskStatus(taskId, { status: 'uploading' });
    } else {
      updateTaskStatus(taskId, { status: 'compressing' });
      const taskArchivePath = path.join(ARCHIVES_DIR, `${archiveName}.tar.zst`);
      const compressCmd = `tar -cf - -C "${taskDownloadDir}" . | zstd -o "${taskArchivePath}"`;
      await runCommand('sh', ['-c', compressCmd], logFile, taskId);
      archivePaths.push(taskArchivePath);
    }

    // 3. Upload
    updateTaskStatus(taskId, { status: 'uploading' });
    for (const archivePath of archivePaths) {
      if (service === 'gofile') {
        // TODO: Implement gofile upload
      } else {
        rcloneConfigPath = createRcloneConfig(taskId, service, params);
        const remotePath = `remote:${uploadPath}`;
        const uploadArgs = [
          'copyto',
          '--config', `"${rcloneConfigPath}"`,
          `"${archivePath}"`,
          `"${remotePath}/${path.basename(archivePath)}"`,
          '-P', '--log-level', 'INFO'
        ];
        await runCommand('rclone', uploadArgs, logFile, taskId);
      }
    }

    updateTaskStatus(taskId, { status: 'completed' });
    fs.appendFileSync(logFile, '\nJob completed successfully!\n');

  } catch (e: any) {
    const errorMsg = `An error occurred: ${e.message}`;
    fs.appendFileSync(logFile, `\n--- JOB FAILED ---\n${errorMsg}\n`);
    updateTaskStatus(taskId, { status: 'failed', error: errorMsg });
  } finally {
    if (fs.existsSync(taskDownloadDir)) {
      fs.rmSync(taskDownloadDir, { recursive: true, force: true });
    }
    for (const ap of archivePaths) {
      if (fs.existsSync(ap)) fs.unlinkSync(ap);
    }
    if (rcloneConfigPath && fs.existsSync(rcloneConfigPath)) {
      fs.unlinkSync(rcloneConfigPath);
    }
  }
}
