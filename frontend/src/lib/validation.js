/**
 * Form validation utilities for NLAMP proposal and mutation workflows.
 * Prevents invalid API requests while keeping backend as authoritative validator.
 */

export function validateProposalForm(form) {
  const newErrors = {};

  if (!form?.project_id) {
    newErrors.project_id = "Project is required.";
  }

  if (!form?.purpose || !form.purpose.trim()) {
    newErrors.purpose = "Purpose is required.";
  } else if (form.purpose.trim().length < 2) {
    newErrors.purpose = "Purpose must be at least 2 characters.";
  }

  const area = Number(form?.required_area_ha);
  if (
    form?.required_area_ha === "" ||
    form?.required_area_ha == null ||
    isNaN(area) ||
    area <= 0
  ) {
    newErrors.required_area_ha = "Required area must be greater than 0.";
  }

  if (!form?.parcel_ids || form.parcel_ids.length === 0) {
    newErrors.parcel_ids = "Select at least one parcel.";
  }

  if (form?.estimated_compensation_inr !== "" && form?.estimated_compensation_inr != null) {
    const comp = Number(form.estimated_compensation_inr);
    if (isNaN(comp) || comp < 0) {
      newErrors.estimated_compensation_inr = "Estimated compensation must be 0 or greater.";
    }
  }

  if (form?.affected_families_count !== "" && form?.affected_families_count != null) {
    const fam = Number(form.affected_families_count);
    if (isNaN(fam) || fam < 0 || !Number.isInteger(fam)) {
      newErrors.affected_families_count = "Affected families must be a whole number 0 or greater.";
    }
  }

  return newErrors;
}

export function validateRejectRemarks(remarks) {
  if (!remarks || !remarks.trim()) {
    return "Rejection remarks are required.";
  }
  return null;
}
