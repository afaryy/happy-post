import { describe, expect, it } from "vitest";

import { GET as health } from "@/app/healthz/route";
import { GET as version } from "@/app/version/route";
import { GET as publicHealth } from "@/app/frontend/healthz/route";
import { GET as publicVersion } from "@/app/frontend/version/route";

describe("operational routes", () => {
  it("returns the same health payload from the root and frontend health routes", async () => {
    expect(await (await health()).json()).toEqual(await (await publicHealth()).json());
  });

  it("returns the same version payload from the root and frontend version routes", async () => {
    expect(await (await version()).json()).toEqual(await (await publicVersion()).json());
  });
});
