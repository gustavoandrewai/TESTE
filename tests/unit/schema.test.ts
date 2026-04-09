import { describe, expect, it } from "vitest";
import { newsletterDraftSchema } from "@/lib/validation/schemas";

describe("schema", () => {
  it("validates newsletter draft", () => {
    const valid = newsletterDraftSchema.safeParse({
      subject: "s",
      executiveSummary: ["1", "2", "3"],
      sections: [],
      monitorToday: ["x"],
      agenda: ["y"]
    });
    expect(valid.success).toBeTruthy();
  });
});
