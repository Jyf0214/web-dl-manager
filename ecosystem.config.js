module.exports = {
  apps: [
    {
      name: "web-dl-manager-next",
      script: "npm",
      args: "run dev",
      cwd: __dirname,
      env: {
        NODE_ENV: "development",
        PORT: "3000"
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      log_file: "logs/next.log",
      time: true
    }
  ]
};