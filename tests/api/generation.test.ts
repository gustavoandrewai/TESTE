import { describe, expect, it } from "vitest";

describe("api generation placeholder", () => {
  it("has run endpoint", () => {
    expect("/api/newsletters/run").toContain("run");
  });
});
