import { describe, expect, it } from "vitest";

import { GET as health } from "@/app/api/healthz/route";
import { GET as version } from "@/app/api/version/route";
import { GET as publicHealth } from "@/app/frontend/healthz/route";
import { GET as publicVersion } from "@/app/frontend/version/route";

describe("operational routes", () => {
  it("returns the same health payload from both health routes", async () => {
    expect(await (await health()).json()).toEqual(await (await publicHealth()).json());
  });

  it("returns the same version payload from both version routes", async () => {
    expect(await (await version()).json()).toEqual(await (await publicVersion()).json());
  });
});
