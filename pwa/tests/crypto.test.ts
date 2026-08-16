// @vitest-environment node
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { decryptJson, encryptJson } from "../src/crypto";

describe("encrypted packets", () => {
  it("round-trips with AES-GCM and rejects the wrong passphrase", async () => {
    const value = { plan: "synthetic", total_cents: 60521 };
    const envelope = await encryptJson(value, "correct horse battery staple");
    expect(envelope.ciphertext).not.toContain("synthetic");
    await expect(decryptJson(envelope, "correct horse battery staple")).resolves.toEqual(value);
    await expect(decryptJson(envelope, "incorrect but long passphrase")).rejects.toThrow();
  });

  it("requires a strong-enough passphrase and supported format", async () => {
    await expect(encryptJson({}, "short")).rejects.toThrow("12 characters");
    const envelope = await encryptJson({}, "twelve-characters-minimum");
    await expect(decryptJson({ ...envelope, version: 2 as 1 }, "twelve-characters-minimum")).rejects.toThrow("unsupported");
  });

  it("decrypts the shared Python-generated envelope", async () => {
    const fixture = JSON.parse(
      readFileSync(resolve("..", "tests", "shared", "python-encrypted-packet.json"), "utf8"),
    );
    await expect(decryptJson(fixture.envelope, fixture.passphrase_for_test_only)).resolves.toEqual(fixture.expected);
  });
});
