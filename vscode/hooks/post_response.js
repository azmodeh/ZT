import { spawn } from "child_process";
import path from "path";

const VALIDATOR = path.resolve(__dirname, "../../enforcement/validator.py");

function runValidator() {
  return new Promise((resolve, reject) => {
    const python = process.env.PYTHON_PATH || "python";
    const child = spawn(python, [VALIDATOR], { stdio: "inherit" });
    child.on("close", (code) => {
      if (code === 0) {
        resolve(true);
      } else {
        reject(new Error(`Validator exited with code ${code}`));
      }
    });
  });
}

export async function runPostResponse() {
  console.log("ZeroTolerance: در حال اجرای اعتبارسنجی پس از پاسخ مدل...");
  try {
    await runValidator();
    console.log("ZeroTolerance: Validation completed successfully.");
  } catch (error) {
    console.error("ZeroTolerance: Validation failed.", error);
  }
  return {};
}
