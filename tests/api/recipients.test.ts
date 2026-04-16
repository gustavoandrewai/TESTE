import { describe, expect, it } from "vitest";

describe("api recipients placeholder", () => {
  it("has route path", () => {
    expect("/api/recipients").toContain("recipients");
  });
});
