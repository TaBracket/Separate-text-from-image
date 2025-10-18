// اجرای Flask از داخل venv به‌صورت Cross-Platform
// ساختار فرضی: react-frontend/ ../py-backend/.venv/... و app.py

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, join } from "node:path";

// مسیر پروژه‌ها نسبت به react-frontend
const backendRoot = resolve(process.cwd(), "..", "py-backend");

// مسیرهای پایتون در venv
const pyWin = join(backendRoot, ".venv", "Scripts", "python.exe");
const pyPosix = join(backendRoot, ".venv", "bin", "python");

// انتخاب باینری مناسب
let pythonPath = process.platform === "win32" ? pyWin : pyPosix;

// اگر باینری venv وجود نداشت، به python سیستم برگردیم (هشدار می‌دهیم)
const fallback = process.platform === "win32" ? "python" : "python3";
if (!existsSync(pythonPath)) {
  console.warn(
    `[warn] venv python not found at ${pythonPath}\n` +
      `       falling back to "${fallback}" (make sure venv is active or in PATH).`
  );
  pythonPath = fallback;
}

// مسیر app.py
const appPy = join(backendRoot, "app.py");

// اجرای سرور Flask
const child = spawn(pythonPath, [appPy], {
  stdio: "inherit",
  cwd: backendRoot,
  env: {
    ...process.env,
    // اگر لازم دارید چیزی ست کنید:
    // FLASK_ENV: "development",
    // PORT: "5001",
  },
});

const shutdown = () => {
  if (!child.killed) {
    try {
      process.platform === "win32"
        ? spawn("taskkill", ["/PID", child.pid, "/T", "/F"])
        : process.kill(child.pid);
    } catch {}
  }
};

process.on("SIGINT", () => {
  shutdown();
  process.exit(0);
});
process.on("SIGTERM", () => {
  shutdown();
  process.exit(0);
});
process.on("exit", shutdown);
