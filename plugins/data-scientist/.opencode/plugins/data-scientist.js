import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const DataScientistPlugin = async () => {
  const skillsDir = path.resolve(__dirname, "../../skills");

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },
    "experimental.chat.system.transform": async (_input, output) => {
      const bootstrap = [
        "<DATA_SCIENTIST_PLUGIN>",
        "You have access to the Data Scientist skills. Use them for messy structured data analysis, manufacturing analytics, statistical method planning, data readiness checks, and evidence-backed reporting.",
        "When delegating staged analysis, use the agent prompts in the plugin's agents directory when your runtime supports subagents; otherwise execute the same roles sequentially.",
        "</DATA_SCIENTIST_PLUGIN>"
      ].join("\n");
      (output.system ||= []).push(bootstrap);
    }
  };
};
