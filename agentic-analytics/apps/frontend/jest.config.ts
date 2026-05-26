import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({ dir: "./" });

const config: Config = {
  coverageProvider: "v8",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^react-markdown$": "<rootDir>/__mocks__/react-markdown.js",
    "^remark-gfm$": "<rootDir>/__mocks__/remark-gfm.js"
  }
};

export default createJestConfig(config);
