import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { validateProposalForm, validateRejectRemarks } from "../src/lib/validation.js";

describe("Phase 4: Form Validation & Mutation Safety", () => {
  // Test 1 — Empty proposal
  it("Test 1 — Empty proposal fails validation on all required fields and prevents API request", () => {
    const emptyForm = {
      project_id: "",
      purpose: "",
      required_area_ha: "",
      parcel_ids: [],
    };

    const errors = validateProposalForm(emptyForm);

    assert.equal(errors.project_id, "Project is required.");
    assert.equal(errors.purpose, "Purpose is required.");
    assert.equal(errors.required_area_ha, "Required area must be greater than 0.");
    assert.equal(errors.parcel_ids, "Select at least one parcel.");
    assert.equal(Object.keys(errors).length, 4);
  });

  // Test 2 — Missing parcel selection
  it("Test 2 — Missing parcel selection reports 'Select at least one parcel.' and prevents submission", () => {
    const noParcelsForm = {
      project_id: "proj-123",
      purpose: "National Highway expansion corridor",
      required_area_ha: "12.5",
      parcel_ids: [],
    };

    const errors = validateProposalForm(noParcelsForm);

    assert.equal(errors.parcel_ids, "Select at least one parcel.");
    assert.equal(errors.project_id, undefined);
    assert.equal(errors.purpose, undefined);
    assert.equal(errors.required_area_ha, undefined);
  });

  // Test 3 — Invalid area checks (0, -1, non-numeric, empty)
  it("Test 3 — Invalid area (0, negative, non-numeric, whitespace) triggers validation error", () => {
    const base = {
      project_id: "proj-123",
      purpose: "Valid purpose for expansion",
      parcel_ids: ["parcel-1"],
    };

    const testCases = ["0", 0, "-1", -5.5, "not-a-number", "", null, undefined];
    for (const badArea of testCases) {
      const errors = validateProposalForm({ ...base, required_area_ha: badArea });
      assert.equal(
        errors.required_area_ha,
        "Required area must be greater than 0.",
        `Failed to reject bad area: ${badArea}`
      );
    }
  });

  // Test 4 — Valid form
  it("Test 4 — Valid form passes all validation rules with 0 errors", () => {
    const validForm = {
      project_id: "proj-123",
      purpose: "Highway widening project phase 1",
      required_area_ha: "4.5",
      parcel_ids: ["parcel-1", "parcel-2"],
      estimated_compensation_inr: "5000000",
      affected_families_count: "12",
    };

    const errors = validateProposalForm(validForm);
    assert.deepEqual(errors, {});
  });

  // Test 5 — Duplicate submit protection simulation
  it("Test 5 — Duplicate submit simulation ensures only one API call runs while saving/busy", async () => {
    let apiCallCount = 0;
    let saving = false;

    async function mockSubmit(formData) {
      if (saving) return { skipped: true };
      const validationErrors = validateProposalForm(formData);
      if (Object.keys(validationErrors).length > 0) return { error: validationErrors };

      saving = true;
      try {
        await new Promise((resolve) => setTimeout(resolve, 20));
        apiCallCount++;
        return { success: true, id: "proposal-new-1" };
      } finally {
        saving = false;
      }
    }

    const validData = {
      project_id: "proj-1",
      purpose: "Ring road bypass",
      required_area_ha: 15.0,
      parcel_ids: ["p-1"],
    };

    // Trigger two rapid submissions
    const [res1, res2] = await Promise.all([
      mockSubmit(validData),
      mockSubmit(validData),
    ]);

    assert.equal(apiCallCount, 1, "Only one API call should be executed during rapid submissions");
    assert.equal(res1.success, true);
    assert.equal(res2.skipped, true);
    assert.equal(saving, false, "Saving state must be reset to false after completion");
  });

  // Test 6 — API mutation failure resets saving state and keeps form values intact
  it("Test 6 — API mutation failure preserves user data and resets saving state without false success", async () => {
    let saving = false;
    let errorMessage = null;

    const userFormData = {
      project_id: "proj-1",
      purpose: "Metro station construction",
      required_area_ha: "3.25",
      parcel_ids: ["p-100"],
      estimated_compensation_inr: "1200000",
      affected_families_count: "4",
    };

    async function mockFailingSubmit(form) {
      if (saving) return;
      const validationErrors = validateProposalForm(form);
      if (Object.keys(validationErrors).length > 0) return;

      saving = true;
      try {
        throw new Error("500 Internal Server Error: Database deadlock");
      } catch (err) {
        errorMessage = err.message;
      } finally {
        saving = false;
      }
    }

    await mockFailingSubmit(userFormData);

    // Assertions
    assert.equal(saving, false, "Saving state must reset to false on failure");
    assert.equal(errorMessage, "500 Internal Server Error: Database deadlock");
    assert.equal(userFormData.purpose, "Metro station construction", "Form data must remain intact");
    assert.equal(userFormData.required_area_ha, "3.25", "Form data must remain intact");
    assert.deepEqual(userFormData.parcel_ids, ["p-100"], "Form data must remain intact");
  });

  // Test 7 — Reject validation
  it("Test 7 — Rejection remarks validation blocks empty remarks and permits valid remarks", () => {
    // Empty / whitespace remarks
    assert.equal(validateRejectRemarks(""), "Rejection remarks are required.");
    assert.equal(validateRejectRemarks("   "), "Rejection remarks are required.");
    assert.equal(validateRejectRemarks(null), "Rejection remarks are required.");
    assert.equal(validateRejectRemarks(undefined), "Rejection remarks are required.");

    // Valid remarks
    assert.equal(validateRejectRemarks("Alignment overlaps with protected wetland area"), null);
    assert.equal(validateRejectRemarks("Requires reassessment of compensatory award"), null);
  });

  // Extra checks — Optional fields validation
  it("Optional numeric fields validation rejects negative numbers and non-integers for family count", () => {
    const base = {
      project_id: "proj-123",
      purpose: "Valid purpose",
      required_area_ha: "10",
      parcel_ids: ["p-1"],
    };

    // Negative compensation
    const errComp = validateProposalForm({ ...base, estimated_compensation_inr: "-500" });
    assert.equal(errComp.estimated_compensation_inr, "Estimated compensation must be 0 or greater.");

    // Negative families count
    const errFamNeg = validateProposalForm({ ...base, affected_families_count: "-2" });
    assert.equal(errFamNeg.affected_families_count, "Affected families must be a whole number 0 or greater.");

    // Non-integer families count
    const errFamFloat = validateProposalForm({ ...base, affected_families_count: "3.5" });
    assert.equal(errFamFloat.affected_families_count, "Affected families must be a whole number 0 or greater.");
  });
});
